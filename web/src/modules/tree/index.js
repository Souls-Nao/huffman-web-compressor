// Secciones 3.2 y 3.3 - Codigos y arbol interactivo.
//   montar(el, store)                 -> seccion completa (selector, tabla, grafica y arbol)
//   montarArbol(el, opciones)         -> componente reutilizable (lo usa el inspector)
import { alerta, descargar, h, reemplazar } from "../../app/dom.js";
import { simboloLegible } from "../../core/index.js";
import { dibujarArbol } from "./render.js";
import { describirCamino, filasCodigos, serieGrafica } from "./viewmodel.js";

// opciones: { raiz, codigos, simbolo, onSeleccionar }  ->  { actualizar({raiz, codigos, simbolo}), destruir() }
export function montarArbol(el, opciones) {
  let estado = { ...opciones };
  const leyenda = h("div", { clase: "camino", "aria-live": "polite" });
  const lienzo = h("div", { clase: "arbol__lienzo" });
  let dibujo = null;
  let raizDibujada;

  const botones = () =>
    h("div", { clase: "arbol__controles" },
      h("button", { clase: "btn btn--chico", type: "button", "aria-label": "Acercar", onClick: () => dibujo?.viewport.acercar() }, "＋"),
      h("button", { clase: "btn btn--chico", type: "button", "aria-label": "Alejar", onClick: () => dibujo?.viewport.alejar() }, "－"),
      h("button", { clase: "btn btn--chico", type: "button", onClick: () => dibujo?.viewport.ajustar() }, "Ajustar"),
      h("button", { clase: "btn btn--chico", type: "button", onClick: () => dibujo && descargar(new XMLSerializer().serializeToString(dibujo.svg).replace("<svg ", '<svg xmlns:xlink="http://www.w3.org/1999/xlink" '), "arbol-huffman.svg", "image/svg+xml") }, "Exportar SVG"),
    );

  const pintarLeyenda = () => {
    const info = estado.simbolo !== null && estado.simbolo !== undefined && estado.raiz && estado.codigos ? describirCamino(estado.raiz, estado.codigos, estado.simbolo) : null;
    if (!info) return reemplazar(leyenda, h("span", { clase: "suave" }, "Elige un símbolo (clic en una hoja o en la tabla) para ver su camino desde la raíz."));
    reemplazar(leyenda,
      h("strong", {}, `${info.etiqueta} → `),
      h("span", { clase: "codigo" }, [...info.codigo].map((b) => h("span", { clase: `bit-${b}` }, b))),
      h("div", { clase: "suave" }, `Raíz ${info.pasos.map((p) => `→ ${p}`).join(" ")} → hoja (${info.codigo.length} ${info.codigo.length === 1 ? "bit" : "bits"} en lugar de 8)`),
    );
  };

  const pintar = () => {
    if (!estado.raiz) {
      dibujo = null;
      raizDibujada = null;
      return reemplazar(lienzo, h("div", { clase: "vacio" }, "Aún no hay árbol: carga un texto en el paso 1."));
    }
    if (raizDibujada !== estado.raiz) {
      dibujo = dibujarArbol(estado.raiz, { onSeleccionar: (b) => estado.onSeleccionar?.(b) });
      raizDibujada = estado.raiz;
      reemplazar(lienzo, dibujo.svg);
      if (dibujo.nodos > 400) lienzo.append(alerta("aviso", "Árbol grande: usa la rueda del ratón para acercar y arrastra para moverte."));
    }
    const camino = estado.simbolo !== null && estado.simbolo !== undefined ? describirCamino(estado.raiz, estado.codigos, estado.simbolo) : null;
    dibujo.resaltar(camino?.ids ?? null);
    pintarLeyenda();
  };

  reemplazar(el, h("div", { clase: "arbol" }, botones(), leyenda, lienzo));
  pintar();
  return {
    actualizar(parcial) { estado = { ...estado, ...parcial }; pintar(); },
    destruir() { reemplazar(el); },
  };
}

function grafica(filas) {
  const { barras, maxBits, escalaLog } = serieGrafica(filas);
  if (!barras.length) return null;
  return h("figure", { clase: "grafica" },
    h("figcaption", {}, "Frecuencia (altura) y longitud del código (color)", escalaLog && " · escala logarítmica"),
    h("div", { clase: "grafica__barras", role: "img", "aria-label": "Gráfica de frecuencia contra longitud del código" },
      barras.map((b) => h("div", { clase: "barra", title: `${b.etiqueta}: ${b.frecuencia.toLocaleString("en-US")} veces, ${b.bits} bits` },
        h("div", { clase: "barra__columna", estilo: { height: `${Math.max(2, b.altura * 100)}%`, "--tono": String(maxBits <= 1 ? 0 : (b.bits - 1) / (maxBits - 1)) } }),
        h("span", { clase: "barra__etiqueta" }, b.etiqueta.length > 3 ? b.etiqueta.slice(0, 2) : b.etiqueta),
      )),
    ),
    h("div", { clase: "grafica__escala" }, h("span", {}, "código corto"), h("span", { clase: "grafica__degradado" }), h("span", {}, "código largo")),
  );
}

export function montar(el, store) {
  const contenido = h("div");
  reemplazar(el, h("div", { clase: "encabezado-seccion" }, h("span", { clase: "numero" }, "3"), h("h2", { id: "t-tree" }, "Códigos y árbol de Huffman")), contenido);
  let arbol = null;
  let raizMontada = null;

  store.alCambiar(["analisis", "simbolo"], ({ analisis, simbolo }) => {
    if (!analisis || !analisis.raiz) {
      arbol = null;
      raizMontada = null;
      return reemplazar(contenido, h("div", { clase: "tarjeta" }, h("div", { clase: "vacio" }, "Carga un texto en el paso 1 para construir el árbol.")));
    }
    if (raizMontada !== analisis.raiz) {
      raizMontada = analisis.raiz;
      const filas = filasCodigos(analisis.frecuencias, analisis.codigos);
      const lugarArbol = h("div");
      const selector = h("select", { "aria-label": "Símbolo a resaltar", onChange: (e) => store.actualizar({ simbolo: e.target.value === "" ? null : Number(e.target.value) }) },
        h("option", { value: "" }, "— elegir símbolo —"),
        [...analisis.frecuencias.keys()].map((b) => h("option", { value: b }, `${simboloLegible(b)} → ${analisis.codigos.get(b)}`)));
      const cuerpoTabla = h("tbody", {}, filas.map((f) =>
        h("tr", { dataset: { byte: f.byte }, tabindex: "0", onClick: () => store.actualizar({ simbolo: f.byte }), onKeydown: (e) => { if (e.key === "Enter") store.actualizar({ simbolo: f.byte }); } },
          h("td", {}, f.simbolo), h("td", { clase: "num" }, f.byte), h("td", { clase: "num" }, f.frecuencia.toLocaleString("en-US")), h("td", { clase: "num" }, `${f.porcentaje} %`),
          h("td", { clase: "codigo" }, [...f.codigo].map((b) => h("span", { clase: `bit-${b}` }, b))), h("td", { clase: "num" }, f.bits))));
      reemplazar(contenido,
        h("div", { clase: "rejilla-2 arbol__rejilla" },
          h("div", { clase: "tarjeta" },
            h("h3", {}, "3.2 Código de cada símbolo"),
            h("p", { clase: "suave" }, "Los símbolos más frecuentes reciben los códigos más cortos."),
            h("label", { clase: "selector" }, "Resaltar símbolo: ", selector),
            h("div", { clase: "tabla-envoltura" }, h("table", { clase: "tabla" },
              h("thead", {}, h("tr", {}, ["Símbolo", "Byte", "Frecuencia", "%", "Código", "Bits"].map((t, i) => h("th", { clase: i === 4 || i === 0 ? "" : "num" }, t)))), cuerpoTabla)),
            grafica(filas),
          ),
          h("div", { clase: "tarjeta" }, h("h3", {}, "3.3 Árbol con el camino resaltado"), lugarArbol),
        ));
      arbol = montarArbol(lugarArbol, { raiz: analisis.raiz, codigos: analisis.codigos, simbolo, onSeleccionar: (b) => store.actualizar({ simbolo: b }) });
    }
    arbol.actualizar({ simbolo });
    for (const fila of contenido.querySelectorAll("tbody tr")) {
      const activa = simbolo !== null && Number(fila.dataset.byte) === simbolo;
      fila.setAttribute("aria-selected", String(activa));
      if (activa) fila.scrollIntoView({ block: "nearest" });
    }
    const select = contenido.querySelector("select");
    if (select) select.value = simbolo === null ? "" : String(simbolo);
  });
}
