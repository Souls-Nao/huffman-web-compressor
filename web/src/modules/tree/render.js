// Dibuja el arbol como SVG a partir de distribuirArbol(). El camino de un simbolo se resalta
// cambiando clases CSS (sin redibujar): los nodos fuera del camino se atenuan.
import { s } from "../../app/dom.js";
import { distribuirArbol, simboloCorto } from "../../core/index.js";
import { crearViewport } from "./viewport.js";

const DX = 46; // separacion horizontal entre columnas
const DY = 78; // separacion vertical entre niveles
const MARGEN = 40;

export function dibujarArbol(raiz, { onSeleccionar } = {}) {
  const dist = distribuirArbol(raiz);
  const ancho = Math.max(240, (Math.max(1, dist.columnas) - 1) * DX + MARGEN * 2);
  const alto = Math.max(160, (dist.filas - 1) * DY + MARGEN * 2);
  const pos = new Map(dist.nodos.map((n) => [n.id, { ...n, x: MARGEN + n.x * DX, y: MARGEN + n.y * DY }]));

  const aristas = dist.aristas.map((a) => {
    const p = pos.get(a.de);
    const q = pos.get(a.a);
    return s("g", { clase: "arista", dataset: { de: a.de, a: a.a } },
      s("line", { x1: p.x, y1: p.y, x2: q.x, y2: q.y }),
      s("text", { x: (p.x + q.x) / 2 + (a.bit === "0" ? -9 : 9), y: (p.y + q.y) / 2 - 3, clase: `arista__bit bit-${a.bit}` }, a.bit),
    );
  });

  const nodos = dist.nodos.map((n) => {
    const { x, y } = pos.get(n.id);
    const hoja = n.nodo.esHoja();
    const grupo = s("g", {
      clase: `nodo ${hoja ? "nodo--hoja" : "nodo--interno"}`,
      dataset: { id: n.id, ...(hoja ? { simbolo: n.nodo.simbolo } : {}) },
      transform: `translate(${x} ${y})`,
      tabindex: hoja ? "0" : null,
      role: hoja ? "button" : null,
      "aria-label": hoja ? `Símbolo ${simboloCorto(n.nodo.simbolo)}, frecuencia ${n.nodo.frecuencia}` : null,
    },
      hoja ? s("rect", { x: -17, y: -15, width: 34, height: 30, rx: 8 }) : s("circle", { r: 15 }),
      s("text", { clase: "nodo__texto", y: hoja ? -2 : 4 }, hoja ? simboloCorto(n.nodo.simbolo) : n.nodo.frecuencia),
      hoja && s("text", { clase: "nodo__frecuencia", y: 10 }, n.nodo.frecuencia),
      s("title", {}, hoja ? `símbolo ${simboloCorto(n.nodo.simbolo)} · frecuencia ${n.nodo.frecuencia}` : `frecuencia ${n.nodo.frecuencia}`),
    );
    if (hoja && onSeleccionar) {
      grupo.addEventListener("click", () => onSeleccionar(n.nodo.simbolo));
      grupo.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSeleccionar(n.nodo.simbolo); } });
    }
    return grupo;
  });

  const svg = s("svg", { clase: "arbol__svg", viewBox: `0 0 ${ancho} ${alto}`, role: "group", "aria-label": "Árbol de Huffman" }, s("g", {}, aristas), s("g", {}, nodos));
  const viewport = crearViewport(svg, ancho, alto);

  // Resalta una lista de ids de nodos (camino raiz -> hoja). null limpia el resaltado.
  const resaltar = (ids) => {
    const set = ids ? new Set(ids) : null;
    svg.classList.toggle("arbol--con-camino", !!set);
    for (const g of svg.querySelectorAll(".nodo")) g.classList.toggle("nodo--camino", !!set && set.has(Number(g.dataset.id)));
    for (const g of svg.querySelectorAll(".arista")) g.classList.toggle("arista--camino", !!set && set.has(Number(g.dataset.de)) && set.has(Number(g.dataset.a)));
    if (!set) return viewport.ajustar();
    const puntos = ids.map((id) => pos.get(id)).filter(Boolean);
    const xs = puntos.map((q) => q.x);
    const ys = puntos.map((q) => q.y);
    viewport.enfocarCaja(Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys));
  };
  return { svg, viewport, resaltar, ancho, alto, nodos: dist.nodos.length };
}
