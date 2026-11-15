// Paso a paso de la cola de prioridad, sin DOM. Todo sale de analisis.inicial y analisis.pasos
// (core/arbol.js registra la cola real despues de cada union, no una simulacion).
import { simboloCorto } from "../../core/index.js";

export const etiquetaNodo = (n) => (n.esHoja() ? `${simboloCorto(n.simbolo)}:${n.frecuencia}` : String(n.frecuencia));

const elemento = (n, marca = null) => ({ id: n.id, etiqueta: etiquetaNodo(n), frecuencia: n.frecuencia, esHoja: n.esHoja(), marca });

// Estado de la construccion en el paso k (0 = cola inicial, total = arbol completo).
export function crearVistaPasos({ inicial, pasos }) {
  const total = pasos.length;
  const cola = (k) => (k === 0 ? inicial : pasos[k - 1].cola);
  return {
    total,
    estado(k) {
      if (!Number.isInteger(k) || k < 0 || k > total) throw new RangeError(`Paso fuera de rango: ${k}`);
      const paso = k === 0 ? null : pasos[k - 1];
      const despues = cola(k);
      const antes = k === 0 ? null : cola(k - 1);
      let texto;
      if (total === 0) texto = "Un solo símbolo distinto: el árbol es una hoja y no hay uniones que hacer.";
      else if (k === 0) texto = `Cola inicial: ${inicial.length} hojas ordenadas por frecuencia. En cada paso salen los dos nodos de menor frecuencia.`;
      else if (k === total) texto = `Paso ${k} de ${total}: salen ${etiquetaNodo(paso.izquierdo)} y ${etiquetaNodo(paso.derecho)} y se unen en la raíz (${paso.padre.frecuencia}). El árbol está completo.`;
      else texto = `Paso ${k} de ${total}: salen ${etiquetaNodo(paso.izquierdo)} y ${etiquetaNodo(paso.derecho)}; el nuevo nodo pesa ${paso.izquierdo.frecuencia} + ${paso.derecho.frecuencia} = ${paso.padre.frecuencia} y vuelve a la cola.`;
      return {
        k,
        total,
        texto,
        paso: paso && { izquierdo: elemento(paso.izquierdo, "izquierdo"), derecho: elemento(paso.derecho, "derecho"), padre: elemento(paso.padre, "nuevo") },
        antes: antes && antes.map((n) => elemento(n, paso.izquierdo.id === n.id ? "izquierdo" : paso.derecho.id === n.id ? "derecho" : null)),
        despues: despues.map((n) => elemento(n, paso && paso.padre.id === n.id ? "nuevo" : null)),
        raices: despues, // nodos reales, para dibujar el bosque
        idNuevo: paso ? paso.padre.id : null,
      };
    },
  };
}

// ids de todos los nodos del subarbol (para resaltar la union en el bosque).
export function idsDeSubarbol(raiz) {
  const ids = new Set();
  const visitar = (n) => {
    ids.add(n.id);
    if (!n.esHoja()) {
      visitar(n.izquierdo);
      visitar(n.derecho);
    }
  };
  if (raiz) visitar(raiz);
  return ids;
}
