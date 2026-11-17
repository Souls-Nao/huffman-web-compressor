// Seccion 1 - Entrada: subir .txt, escribir un texto corto o buscar en Project Gutenberg.
// Publica en el store: entrada = { nombre, datos: Uint8Array, origen, libro? }
import { alerta, h, reemplazar } from "../../app/dom.js";
import { tamanoLegible } from "../../core/index.js";
import { buscar, descargar } from "./gutenberg.js";

const PESTANAS = [
  ["archivo", "Subir .txt"],
  ["gutenberg", "Buscar en Project Gutenberg"],
  ["texto", "Escribir un texto corto"],
];

export function montar(el, store) {
  const resumen = h("div", { "aria-live": "polite" });
  const panel = h("div", { clase: "entrada__panel" });
  const pestanas = h("div", { clase: "pestanas", role: "tablist" });
  let activa = "archivo";

  const usar = (entrada) => store.actualizar({ entrada });

  const paneles = {
    archivo: () => panelArchivo(usar),
    gutenberg: () => panelGutenberg(usar),
    texto: () => panelTexto(usar),
  };

  const dibujarPestanas = () =>
    reemplazar(
      pestanas,
      PESTANAS.map(([clave, etiqueta]) =>
        h("button", {
          clase: "pestana",
          role: "tab",
          type: "button",
          "aria-selected": String(clave === activa),
          onClick: () => {
            activa = clave;
            dibujarPestanas();
            reemplazar(panel, paneles[clave]());
          },
        }, etiqueta),
      ),
    );

  store.alCambiar(["entrada"], ({ entrada }) =>
    reemplazar(
      resumen,
      entrada &&
        h("div", { clase: "entrada__actual" },
          h("div", {},
            h("strong", {}, entrada.libro ? entrada.libro.titulo : entrada.nombre),
            h("div", { clase: "suave" }, [entrada.libro?.autor, entrada.nombre, tamanoLegible(entrada.datos.length), ORIGEN[entrada.origen]].filter(Boolean).join(" · ")),
          ),
          h("button", { clase: "btn btn--chico", type: "button", onClick: () => store.actualizar({ entrada: null }) }, "Quitar"),
        ),
    ),
  );

  reemplazar(
    el,
    h("div", { clase: "encabezado-seccion" }, h("span", { clase: "numero" }, "1"), h("h2", { id: "t-input" }, "Entrada")),
    h("div", { clase: "tarjeta" }, pestanas, panel, resumen),
  );
  dibujarPestanas();
  reemplazar(panel, paneles[activa]());
}

const ORIGEN = { archivo: "archivo local", texto: "texto escrito", gutenberg: "Project Gutenberg" };

function panelArchivo(usar) {
  const aviso = h("div");
  const leer = async (archivo) => {
    if (!archivo) return;
    try {
      usar({ nombre: archivo.name, datos: new Uint8Array(await archivo.arrayBuffer()), origen: "archivo" });
      reemplazar(aviso);
    } catch {
      reemplazar(aviso, alerta("error", "No se pudo leer el archivo."));
    }
  };
  const zona = h("label", { clase: "soltar", tabindex: "0" },
    h("input", { type: "file", accept: ".txt,text/plain", clase: "solo-lectores", onChange: (e) => leer(e.target.files[0]) }),
    h("strong", {}, "Arrastra un .txt aquí o haz clic para elegirlo"),
    h("span", { clase: "suave" }, "Se lee como bytes: cualquier codificación se recupera idéntica."),
  );
  zona.addEventListener("dragover", (e) => { e.preventDefault(); zona.classList.add("soltar--sobre"); });
  zona.addEventListener("dragleave", () => zona.classList.remove("soltar--sobre"));
  zona.addEventListener("drop", (e) => { e.preventDefault(); zona.classList.remove("soltar--sobre"); leer(e.dataTransfer.files[0]); });
  zona.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); zona.querySelector("input").click(); } });
  return h("div", {}, zona, aviso);
}

function panelTexto(usar) {
  const area = h("textarea", { rows: 4, "aria-label": "Texto a comprimir", placeholder: "Escribe o pega un texto, por ejemplo: abracadabra" });
  const boton = (etiqueta, texto) => h("button", { clase: "btn btn--chico", type: "button", onClick: () => { area.value = texto; } }, etiqueta);
  return h("div", {},
    area,
    h("div", { clase: "entrada__acciones" },
      h("button", { clase: "btn btn--primario", type: "button", onClick: () => area.value && usar({ nombre: "texto.txt", datos: new TextEncoder().encode(area.value), origen: "texto" }) }, "Usar este texto"),
      h("span", { clase: "suave" }, "Ejemplos:"),
      boton("abracadabra", "abracadabra"),
      boton("Con acentos", "¡Hola, ñandú! Adiós, canción."),
    ),
    h("p", { clase: "suave" }, "Con textos muy cortos el .hfa pesa más que el original: el encabezado ocupa más que el ahorro."),
  );
}

function panelGutenberg(usar) {
  const campo = h("input", { type: "search", "aria-label": "Título, autor o tema", placeholder: "quijote, Mary Shelley, pirates…" });
  const resultados = h("ul", { clase: "libros" });
  const estado = h("div", { "aria-live": "polite" });
  let control = null;

  const elegir = async (libro, boton) => {
    control?.abort();
    control = new AbortController();
    boton.disabled = true;
    reemplazar(estado, alerta("info", `Descargando «${libro.titulo}»…`));
    try {
      const datos = await descargar(libro.id, {
        senal: control.signal,
        alProgreso: (f) => reemplazar(estado, alerta("info", `Descargando «${libro.titulo}»… ${Math.round(f * 100)} %`)),
      });
      usar({ nombre: `pg${libro.id}.txt`, datos, origen: "gutenberg", libro });
      reemplazar(estado, alerta("ok", `«${libro.titulo}» cargado correctamente.`));
    } catch (error) {
      if (error.name !== "AbortError") reemplazar(estado, alerta("error", error.message));
    } finally {
      boton.disabled = false;
    }
  };

  const ejecutar = async (evento) => {
    evento.preventDefault();
    reemplazar(resultados);
    reemplazar(estado, alerta("info", "Buscando…"));
    try {
      const libros = await buscar(campo.value);
      reemplazar(estado, !libros.length && alerta("aviso", "Sin resultados. Prueba con otro título, autor o tema."));
      reemplazar(resultados, libros.map((libro) => {
        const boton = h("button", { clase: "btn btn--chico btn--primario", type: "button" }, "Usar este libro");
        boton.addEventListener("click", () => elegir(libro, boton));
        return h("li", { clase: "libro" }, h("div", {}, h("strong", {}, libro.titulo), h("div", { clase: "suave" }, `${libro.autor || "Autor desconocido"} · #${libro.id}`)), boton);
      }));
    } catch (error) {
      reemplazar(estado, alerta("error", error.message));
    }
  };

  return h("div", {},
    h("form", { clase: "buscador", onSubmit: ejecutar }, campo, h("button", { clase: "btn btn--primario", type: "submit" }, "Buscar")),
    h("p", { clase: "suave" }, "Se muestran los primeros 25 resultados del catálogo oficial."),
    estado,
    resultados,
  );
}
