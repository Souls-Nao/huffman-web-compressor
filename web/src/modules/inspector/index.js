// Secciones 5 y 6 - Inspector (tabla, bits por caracter, arbol, tamano final vs original) y descompresion.
import { alerta, descargar, h, reemplazar, tarjetaMetrica } from "../../app/dom.js";
import { aHex, descomprimir, EXTENSION, FormatoError, sha256, tamanoLegible } from "../../core/index.js";
import { montarArbol } from "../tree/index.js";
import { bytesMuestra, segmentarBits, vistaDesdeAnalisis, vistaDesdeHfa } from "./viewmodel.js";

const bitsColor = (texto) => [...texto].map((b) => h("span", { clase: `bit-${b}` }, b));
const fmt = (n) => n.toLocaleString("en-US");

export function montar(el, store) {
  let fuente = "actual";
  let archivo = null; // { nombre, bytes, vista } | { error }
  let limpiezas = [];
  const cuerpo = h("div");
  const pestanas = h("div", { clase: "pestanas", role: "tablist" });
  reemplazar(el, h("div", { clase: "encabezado-seccion" }, h("span", { clase: "numero" }, "5"), h("h2", { id: "t-inspector" }, "Inspector del archivo comprimido")), h("div", { clase: "tarjeta" }, pestanas, cuerpo));

  const marcar = (clave) => store.actualizar({ progreso: { ...store.obtener().progreso, [clave]: true } });

  const cargarHfa = (nombre, bytes) => {
    try {
      archivo = { nombre, bytes, vista: vistaDesdeHfa(bytes, nombre) };
      marcar("inspeccionado");
    } catch (error) {
      archivo = { error: error instanceof FormatoError ? error.message : "No se pudo leer el archivo." };
    }
    dibujar();
  };

  function dibujar() {
    limpiezas.forEach((f) => f());
    limpiezas = [];
    reemplazar(pestanas, [["actual", "Texto actual"], ["hfa", `Archivo ${EXTENSION}`]].map(([clave, texto]) =>
      h("button", { clase: "pestana", role: "tab", type: "button", "aria-selected": String(fuente === clave), onClick: () => { fuente = clave; dibujar(); } }, texto)));
    const { analisis, entrada, comprimido } = store.obtener();
    if (fuente === "actual") {
      if (!analisis?.raiz) return reemplazar(cuerpo, h("div", { clase: "vacio" }, "Carga un texto en el paso 1 para inspeccionar su tabla de frecuencias, códigos y tamaño final."));
      return reemplazar(cuerpo, panel(vistaDesdeAnalisis(analisis, entrada), null));
    }
    const selector = h("input", { type: "file", accept: `${EXTENSION}`, "aria-label": `Archivo ${EXTENSION}`, onChange: async (e) => { const f = e.target.files[0]; if (f) cargarHfa(f.name, new Uint8Array(await f.arrayBuffer())); } });
    reemplazar(cuerpo,
      h("div", { clase: "inspector__fuente" }, selector, comprimido && h("button", { clase: "btn", type: "button", onClick: () => cargarHfa(comprimido.nombre, comprimido.bytes) }, `Usar ${comprimido.nombre} recién comprimido`)),
      !archivo && h("p", { clase: "suave" }, `Sube un ${EXTENSION}: el inspector muestra su estructura sin necesitar el .txt original. El texto solo aparece después de pulsar DESCOMPRIMIR.`),
      archivo?.error && alerta("error", archivo.error),
      archivo?.vista && panel(archivo.vista, archivo));
  }

  function panel(vista, hfa) {
    const m = vista.metricas;
    const proporcion = Math.min(100, (vista.tamanoFinal / Math.max(1, vista.tamanoOriginal)) * 100);
    const lugarArbol = h("div");
    const detalleArbol = h("details", { open: true }, h("summary", {}, "Árbol de Huffman reconstruido"), lugarArbol);
    const arbol = montarArbol(lugarArbol, { raiz: vista.raiz, codigos: vista.codigos, simbolo: store.obtener().simbolo, onSeleccionar: (b) => store.actualizar({ simbolo: b }) });
    limpiezas.push(store.alCambiar(["simbolo"], ({ simbolo }) => arbol.actualizar({ simbolo })));
    limpiezas.push(() => arbol.destruir());
    const bytes = bytesMuestra(vista.bitsMuestra);
    const segmentos = segmentarBits(vista.bitsMuestra, vista.raiz);
    return h("div", { clase: "inspector" },
      vista.metadatos && h("div", {}, h("h3", {}, "Metadatos del encabezado"), h("table", { clase: "tabla meta" }, h("tbody", {}, vista.metadatos.map(([k, v]) => h("tr", {}, h("th", { scope: "row" }, k), h("td", { clase: k.startsWith("SHA") ? "mono hash" : "" }, v)))))),
      h("div", { clase: "metricas" },
        tarjetaMetrica("Tamaño original", tamanoLegible(vista.tamanoOriginal)),
        tarjetaMetrica(hfa ? "Tamaño del .hfa" : "Tamaño final del .hfa", tamanoLegible(vista.tamanoFinal), hfa ? null : "calculado sin generar el archivo"),
        tarjetaMetrica("Ahorro", tamanoLegible(m.ahorro)),
        tarjetaMetrica("Reducción", `${m.reduccion.toFixed(2)} %`),
        tarjetaMetrica("Razón", `${m.razon.toFixed(2)} : 1`),
        tarjetaMetrica("Símbolos / bits", `${m.simbolos} · ${fmt(vista.totalBits)} bits`)),
      h("div", { clase: "comparacion", role: "img", "aria-label": `Final: ${proporcion.toFixed(1)} % del original` },
        h("div", { clase: "comparacion__barra comparacion__barra--original" }, `Original · ${fmt(vista.tamanoOriginal)} B`),
        h("div", { clase: "comparacion__barra comparacion__barra--comprimido", estilo: { width: `${Math.max(proporcion, 10)}%` } }, `Final · ${fmt(vista.tamanoFinal)} B`)),
      h("h3", {}, "Tabla de frecuencias y bits por carácter"),
      h("p", { clase: "suave" }, "Cada carácter ocupa 8 bits sin comprimir; con Huffman ocupa solo la longitud de su código."),
      h("div", { clase: "tabla-envoltura" }, h("table", { clase: "tabla" },
        h("thead", {}, h("tr", {}, ["Símbolo", "Byte", "Frecuencia", "%", "Código", "Bits por carácter", "Bits totales", "Sin comprimir"].map((t, i) => h("th", { clase: i === 0 || i === 4 ? "" : "num" }, t)))),
        h("tbody", {}, vista.filas.map((f) => h("tr", { dataset: { byte: f.byte }, onClick: () => store.actualizar({ simbolo: f.byte }) },
          h("td", {}, f.simbolo), h("td", { clase: "num" }, f.byte), h("td", { clase: "num" }, fmt(f.frecuencia)), h("td", { clase: "num" }, `${f.porcentaje} %`),
          h("td", { clase: "codigo" }, bitsColor(f.codigo)),
          h("td", { clase: "num" }, h("span", { clase: "bits-barra", estilo: { "--w": `${(f.bits / 8) * 100}%` } }), ` ${f.bits} / 8`),
          h("td", { clase: "num" }, fmt(f.bitsTotales)), h("td", { clase: "num" }, fmt(f.bitsOriginal))))))),
      detalleArbol,
      h("h3", {}, "Primeros bits"),
      h("div", { clase: "bytes" }, bytes.map((b) => h("div", { clase: "byte" }, h("span", { clase: "mono" }, b.binario), h("small", {}, b.hex)))),
      h("p", { clase: "suave" }, "Los mismos bits separados por palabra de código:"),
      h("div", { clase: "palabras" }, segmentos.map((p) => h("span", { clase: "palabra" }, h("span", { clase: "codigo" }, bitsColor(p.bits)), h("small", {}, p.etiqueta)))),
      hfa ? bloqueDescomprimir(hfa, vista) : h("p", { clase: "suave" }, `Para descomprimir y verificar, usa la pestaña «Archivo ${EXTENSION}».`));
  }

  function bloqueDescomprimir(hfa, vista) {
    const salida = h("div", { "aria-live": "polite" });
    const boton = h("button", { clase: "btn btn--primario", type: "button" }, "DESCOMPRIMIR");
    boton.addEventListener("click", async () => {
      boton.disabled = true;
      try {
        const { datos, integridadOk } = await descomprimir(hfa.bytes);
        marcar("descomprimido");
        if (integridadOk) marcar("verificado");
        const hashRecuperado = aHex(await sha256(datos));
        reemplazar(salida,
          integridadOk ? alerta("ok", "Integridad verificada: el SHA-256 del texto recuperado es idéntico al original.") : alerta("error", "Integridad fallida: el texto recuperado NO coincide con el original."),
          h("p", { clase: "suave mono hash" }, `SHA-256 recuperado: ${hashRecuperado}`),
          h("textarea", { readonly: true, rows: 10, "aria-label": "Texto recuperado" }, new TextDecoder("utf-8").decode(datos.subarray(0, 5000))),
          datos.length > 5000 && h("p", { clase: "suave" }, "Vista previa de los primeros 5,000 bytes."),
          h("button", { clase: "btn", type: "button", onClick: () => descargar(datos, `recuperado_${vista.nombre}`, "text/plain") }, "Descargar texto recuperado (.txt)"));
      } catch (error) {
        reemplazar(salida, alerta("error", error.message));
      } finally {
        boton.disabled = false;
      }
    });
    return h("div", { clase: "descomprimir" }, h("h3", {}, "6. Descomprimir y verificar"), h("p", { clase: "suave" }, "El texto original solo aparece después de este botón."), boton, salida);
  }

  store.alCambiar(["analisis", "entrada"], dibujar);
  let ultima = store.obtener().inspeccionar;
  store.suscribir(({ inspeccionar, comprimido }) => {
    if (inspeccionar !== ultima && comprimido) { ultima = inspeccionar; fuente = "hfa"; cargarHfa(comprimido.nombre, comprimido.bytes); }
  });
}
