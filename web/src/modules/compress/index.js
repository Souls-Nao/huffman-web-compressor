// Seccion 4 - Comprimir y medir: genera el .hfa, muestra metricas y permite descargarlo.
import { alerta, descargar, h, reemplazar, tarjetaMetrica } from "../../app/dom.js";
import { comprimir, EXTENSION, metricas, tamanoLegible } from "../../core/index.js";

const nombreHfa = (nombre) => nombre.replace(/\.[^.]*$/, "") + EXTENSION;

export function montar(el, store) {
  const cuerpo = h("div");
  reemplazar(el, h("div", { clase: "encabezado-seccion" }, h("span", { clase: "numero" }, "4"), h("h2", { id: "t-compress" }, "Comprimir y medir")), h("div", { clase: "tarjeta" }, cuerpo));

  const comprimirAhora = async (estado) => {
    const { entrada, analisis } = estado;
    reemplazar(cuerpo, alerta("info", "Comprimiendo…"));
    try {
      const inicio = performance.now();
      const bytes = await comprimir(entrada.datos, entrada.nombre);
      const ms = performance.now() - inicio;
      store.actualizar({ comprimido: { nombre: nombreHfa(entrada.nombre), bytes, ms, metricas: metricas(entrada.datos.length, bytes.length, analisis.frecuencias.size) } });
    } catch (error) {
      reemplazar(cuerpo, alerta("error", `No se pudo comprimir: ${error.message}`));
    }
  };

  store.alCambiar(["analisis", "comprimido"], (estado) => {
    const { analisis, comprimido } = estado;
    if (!analisis) return reemplazar(cuerpo, h("div", { clase: "vacio" }, "Carga un texto en el paso 1 para poder comprimirlo."));
    if (!analisis.raiz) return reemplazar(cuerpo, alerta("aviso", "El archivo está vacío: no hay nada que comprimir."));
    if (!comprimido) {
      return reemplazar(cuerpo,
        h("p", {}, "Tamaño final estimado del ", h("code", {}, EXTENSION), ": ", h("strong", {}, tamanoLegible(analisis.tamanoFinal)), " (encabezado + bits de Huffman)."),
        h("button", { clase: "btn btn--primario", type: "button", onClick: () => comprimirAhora(store.obtener()) }, "Comprimir"),
      );
    }
    const m = comprimido.metricas;
    const proporcion = Math.min(100, (m.comprimido / m.original) * 100);
    reemplazar(cuerpo,
      h("div", { clase: "metricas" },
        tarjetaMetrica("Original", tamanoLegible(m.original)),
        tarjetaMetrica("Comprimido", tamanoLegible(m.comprimido), "incluye el encabezado"),
        tarjetaMetrica("Ahorro", tamanoLegible(m.ahorro)),
        tarjetaMetrica("Reducción", `${m.reduccion.toFixed(2)} %`),
        tarjetaMetrica("Razón de compresión", `${m.razon.toFixed(2)} : 1`),
        tarjetaMetrica("Símbolos diferentes", String(m.simbolos)),
      ),
      h("div", { clase: "comparacion", role: "img", "aria-label": `El comprimido ocupa el ${proporcion.toFixed(1)} % del original` },
        h("div", { clase: "comparacion__barra comparacion__barra--original" }, "Original"),
        h("div", { clase: "comparacion__barra comparacion__barra--comprimido", estilo: { width: `${Math.max(proporcion, 8)}%` } }, `${proporcion.toFixed(1)} %`),
      ),
      h("p", { clase: "suave" }, `Comprimido en ${comprimido.ms.toFixed(1)} ms.`),
      h("div", { clase: "acciones" },
        h("button", { clase: "btn btn--primario", type: "button", onClick: () => descargar(comprimido.bytes, comprimido.nombre) }, `Descargar ${comprimido.nombre}`),
        h("button", { clase: "btn", type: "button", onClick: () => { store.actualizar({ inspeccionar: Date.now() }); document.getElementById("mod-inspector")?.scrollIntoView({ behavior: "smooth" }); } }, "Inspeccionar este archivo"),
      ),
      m.reduccion < 0 && alerta("aviso", "El .hfa pesa más que el original: con textos muy cortos el encabezado ocupa más que el ahorro."),
    );
  });
}
