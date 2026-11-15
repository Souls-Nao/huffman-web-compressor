// Seccion 3.1 - Construccion paso a paso con la cola de prioridad (min-heap).
import { h, reemplazar, s } from "../../app/dom.js";
import { distribuirBosque, simboloCorto } from "../../core/index.js";
import { crearVistaPasos, idsDeSubarbol } from "./viewmodel.js";

const MAX_VISIBLES = 14; // elementos de la cola que se muestran; el resto se resume
const DX = 30;
const DY = 52;

function filaCola(titulo, items, nota) {
  const visibles = items.slice(0, MAX_VISIBLES);
  return h("div", { clase: "cola" },
    h("div", { clase: "cola__titulo" }, titulo, h("span", { clase: "suave" }, ` · ${items.length} ${items.length === 1 ? "nodo" : "nodos"}`)),
    h("ol", { clase: "cola__lista", "aria-label": titulo },
      visibles.map((it) => h("li", { clase: `ficha ficha--${it.esHoja ? "hoja" : "interno"} ${it.marca ? `ficha--${it.marca}` : ""}` },
        h("span", {}, it.etiqueta), it.marca === "izquierdo" && h("small", {}, "sale · 0"), it.marca === "derecho" && h("small", {}, "sale · 1"), it.marca === "nuevo" && h("small", {}, "nuevo"))),
      items.length > MAX_VISIBLES && h("li", { clase: "ficha ficha--mas" }, `… +${items.length - MAX_VISIBLES}`),
    ),
    nota && h("small", { clase: "suave" }, nota),
  );
}

function dibujarBosque(raices, idsNuevos) {
  const dist = distribuirBosque(raices, 0.8);
  const ancho = Math.max(200, dist.columnas * DX + 40);
  const alto = Math.max(90, (dist.filas - 1) * DY + 60);
  const p = new Map(dist.nodos.map((n) => [n.id, { x: 20 + n.x * DX, y: 28 + n.y * DY, nodo: n.nodo }]));
  return s("svg", { clase: "bosque__svg", width: ancho, height: alto, viewBox: `0 0 ${ancho} ${alto}`, role: "img", "aria-label": "Bosque de árboles parciales en la cola" },
    dist.aristas.map((a) => s("line", { clase: `bosque__arista ${idsNuevos.has(a.de) && idsNuevos.has(a.a) ? "bosque__arista--nuevo" : ""}`, x1: p.get(a.de).x, y1: p.get(a.de).y, x2: p.get(a.a).x, y2: p.get(a.a).y })),
    dist.nodos.map((n) => {
      const { x, y } = p.get(n.id);
      const hoja = n.nodo.esHoja();
      return s("g", { clase: `bnodo ${hoja ? "bnodo--hoja" : ""} ${idsNuevos.has(n.id) ? "bnodo--nuevo" : ""}`, transform: `translate(${x} ${y})` },
        s("circle", { r: hoja ? 12 : 11 }),
        s("text", { y: hoja ? -1 : 4 }, hoja ? simboloCorto(n.nodo.simbolo) : n.nodo.frecuencia),
        hoja && s("text", { clase: "bnodo__f", y: 8 }, n.nodo.frecuencia),
        s("title", {}, hoja ? `${simboloCorto(n.nodo.simbolo)}: ${n.nodo.frecuencia}` : `frecuencia ${n.nodo.frecuencia}`));
    }),
  );
}

export function montar(el, store) {
  const cuerpo = h("div");
  reemplazar(el, h("div", { clase: "encabezado-seccion" }, h("span", { clase: "numero" }, "3"), h("h2", { id: "t-steps" }, "Construcción paso a paso (cola de prioridad)")), h("div", { clase: "tarjeta" }, cuerpo));
  let temporizador = null;
  const parar = () => { clearInterval(temporizador); temporizador = null; };

  store.alCambiar(["analisis"], ({ analisis }) => {
    parar();
    if (!analisis || !analisis.raiz) return reemplazar(cuerpo, h("div", { clase: "vacio" }, "Carga un texto en el paso 1 para ver cómo la técnica voraz arma el árbol."));
    const vista = crearVistaPasos(analisis);
    let k = 0;
    const texto = h("p", { clase: "paso__texto", "aria-live": "polite" });
    const colas = h("div", { clase: "colas" });
    const bosque = h("div", { clase: "bosque", tabindex: "0", "aria-label": "Bosque, desplazable" });
    const deslizador = h("input", { type: "range", min: 0, max: vista.total, value: 0, "aria-label": "Paso de la construcción", onInput: (e) => ir(Number(e.target.value)) });
    const contador = h("output", { clase: "paso__contador" });
    const botonPlay = h("button", { clase: "btn btn--chico", type: "button", onClick: () => alternar() }, "▶ Reproducir");
    const velocidad = h("select", { "aria-label": "Velocidad" }, [["900", "Lenta"], ["450", "Normal"], ["150", "Rápida"]].map(([v, t], i) => h("option", { value: v, selected: i === 1 }, t)));

    function ir(nuevo) {
      k = Math.max(0, Math.min(vista.total, nuevo));
      const e = vista.estado(k);
      deslizador.value = k;
      contador.textContent = `${k} / ${vista.total}`;
      reemplazar(texto, e.texto);
      reemplazar(colas,
        e.antes ? filaCola("Antes del paso (cola ordenada de menor a mayor)", e.antes, "Salen siempre los dos primeros.") : null,
        filaCola(e.antes ? "Después del paso" : "Cola de prioridad", e.despues, e.antes ? null : "El primero de la cola es el de menor frecuencia."));
      const ids = e.idNuevo === null ? new Set() : idsDeSubarbol(e.raices.find((r) => r.id === e.idNuevo));
      reemplazar(bosque, dibujarBosque(e.raices, ids));
      if (k === vista.total) parar(), (botonPlay.textContent = "▶ Reproducir");
    }
    function alternar() {
      if (temporizador) { parar(); botonPlay.textContent = "▶ Reproducir"; return; }
      if (k >= vista.total) ir(0);
      botonPlay.textContent = "⏸ Pausar";
      temporizador = setInterval(() => ir(k + 1), Number(velocidad.value));
    }
    velocidad.addEventListener("change", () => { if (temporizador) { parar(); temporizador = setInterval(() => ir(k + 1), Number(velocidad.value)); } });

    reemplazar(cuerpo,
      h("p", { clase: "suave" }, "Estrategia voraz: en cada paso se unen los dos nodos de menor frecuencia. Con n símbolos hay n − 1 uniones y cada una cuesta O(log n)."),
      h("div", { clase: "paso__controles" },
        h("button", { clase: "btn btn--chico", type: "button", onClick: () => { parar(); botonPlay.textContent = "▶ Reproducir"; ir(0); } }, "⏮"),
        h("button", { clase: "btn btn--chico", type: "button", onClick: () => ir(k - 1), "aria-label": "Paso anterior" }, "◀"),
        botonPlay,
        h("button", { clase: "btn btn--chico", type: "button", onClick: () => ir(k + 1), "aria-label": "Paso siguiente" }, "▶"),
        h("button", { clase: "btn btn--chico", type: "button", onClick: () => { parar(); botonPlay.textContent = "▶ Reproducir"; ir(vista.total); } }, "⏭"),
        deslizador, contador, velocidad),
      texto, colas, h("h3", {}, "Bosque en este paso"), bosque);
    ir(0);
  });
}
