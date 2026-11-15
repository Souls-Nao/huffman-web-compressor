// Bloque 2 - Arbol de Huffman (tecnica voraz) con cola de prioridad (min-heap).
// En cada paso se sacan los DOS nodos de menor frecuencia y se unen en un padre
// con la suma. Costo: n hojas -> n-1 uniones, cada una O(log n)  =>  O(n log n).

export class Nodo {
  constructor(id, frecuencia, simbolo = null, izquierdo = null, derecho = null) {
    this.id = id; // numero de llegada a la cola; sirve de desempate y de llave en la interfaz
    this.frecuencia = frecuencia;
    this.simbolo = simbolo;
    this.izquierdo = izquierdo; // bit 0
    this.derecho = derecho; // bit 1
  }
  esHoja() {
    return this.izquierdo === null && this.derecho === null;
  }
}

// Orden total (frecuencia, id): entre frecuencias iguales sale el que llego antes.
// Es la misma regla de heapq con tuplas (frecuencia, orden, nodo) de la version Python.
const menor = (a, b) => a.frecuencia < b.frecuencia || (a.frecuencia === b.frecuencia && a.id < b.id);

export class ColaPrioridad {
  constructor() {
    this.heap = [];
  }
  get tamano() {
    return this.heap.length;
  }
  insertar(nodo) {
    const h = this.heap;
    let i = h.push(nodo) - 1;
    while (i > 0) {
      const padre = (i - 1) >> 1;
      if (!menor(h[i], h[padre])) break;
      [h[i], h[padre]] = [h[padre], h[i]];
      i = padre;
    }
  }
  extraerMinimo() {
    const h = this.heap;
    const minimo = h[0];
    const ultimo = h.pop();
    if (h.length > 0) {
      h[0] = ultimo;
      let i = 0;
      for (;;) {
        const l = 2 * i + 1;
        const r = l + 1;
        let m = i;
        if (l < h.length && menor(h[l], h[m])) m = l;
        if (r < h.length && menor(h[r], h[m])) m = r;
        if (m === i) break;
        [h[i], h[m]] = [h[m], h[i]];
        i = m;
      }
    }
    return minimo;
  }
  // Contenido ordenado de menor a mayor: es el orden real en que saldrian los nodos.
  ordenada() {
    return [...this.heap].sort((a, b) => (menor(a, b) ? -1 : 1));
  }
}

// Construye el arbol y registra cada union (para la vista paso a paso).
// Regresa { raiz, inicial, pasos }:
//   inicial = cola antes de empezar (solo hojas)
//   pasos[k] = { izquierdo, derecho, padre, cola }  (cola = estado DESPUES de la union k)
export function construirConPasos(frecuencias) {
  if (!frecuencias || frecuencias.size === 0) return { raiz: null, inicial: [], pasos: [] };
  const cola = new ColaPrioridad();
  let id = 0;
  // Las hojas entran ordenadas por simbolo.
  for (const simbolo of [...frecuencias.keys()].sort((a, b) => a - b)) {
    cola.insertar(new Nodo(id++, frecuencias.get(simbolo), simbolo));
  }
  const inicial = cola.ordenada();
  const pasos = [];
  while (cola.tamano > 1) {
    const izquierdo = cola.extraerMinimo();
    const derecho = cola.extraerMinimo();
    const padre = new Nodo(id++, izquierdo.frecuencia + derecho.frecuencia, null, izquierdo, derecho);
    cola.insertar(padre);
    pasos.push({ izquierdo, derecho, padre, cola: cola.ordenada() });
  }
  return { raiz: cola.extraerMinimo(), inicial, pasos };
}

export function construirArbol(frecuencias) {
  if (!frecuencias || frecuencias.size === 0) return null;
  // Version sin registro de pasos: evita copiar la cola en cada union.
  const cola = new ColaPrioridad();
  let id = 0;
  for (const simbolo of [...frecuencias.keys()].sort((a, b) => a - b)) {
    cola.insertar(new Nodo(id++, frecuencias.get(simbolo), simbolo));
  }
  while (cola.tamano > 1) {
    const izquierdo = cola.extraerMinimo();
    const derecho = cola.extraerMinimo();
    cola.insertar(new Nodo(id++, izquierdo.frecuencia + derecho.frecuencia, null, izquierdo, derecho));
  }
  return cola.extraerMinimo();
}
