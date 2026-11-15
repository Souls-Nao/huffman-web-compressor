// Bloque 3 - Codigos de Huffman. Izquierda = "0", derecha = "1".
// Los simbolos solo estan en hojas, asi que ningun codigo es prefijo de otro.

// Regresa Map<byte, "0101"> ordenado por simbolo.
export function generarCodigos(raiz) {
  if (!raiz) return new Map();
  // Caso especial: un solo simbolo distinto. No hay camino, se le asigna "0".
  if (raiz.esHoja()) return new Map([[raiz.simbolo, "0"]]);
  const codigos = new Map();
  const recorrer = (nodo, codigo) => {
    if (nodo.esHoja()) return codigos.set(nodo.simbolo, codigo);
    recorrer(nodo.izquierdo, codigo + "0");
    recorrer(nodo.derecho, codigo + "1");
  };
  recorrer(raiz, "");
  return new Map([...codigos].sort((a, b) => a[0] - b[0]));
}

// Camino raiz -> hoja de un simbolo: ids de los nodos visitados y bits de cada arista.
// Ejemplo: { ids: [6, 5, 3, 1], bits: "110" }.  Regresa null si el simbolo no esta en el arbol.
export function caminoDeSimbolo(raiz, simbolo) {
  if (!raiz) return null;
  if (raiz.esHoja()) return raiz.simbolo === simbolo ? { ids: [raiz.id], bits: "0" } : null;
  const ids = [];
  const bits = [];
  const buscar = (nodo) => {
    ids.push(nodo.id);
    if (nodo.esHoja()) {
      if (nodo.simbolo === simbolo) return true;
      ids.pop(); // hoja equivocada: se descarta tambien su id
      return false;
    }
    for (const [hijo, bit] of [[nodo.izquierdo, "0"], [nodo.derecho, "1"]]) {
      bits.push(bit);
      if (buscar(hijo)) return true;
      bits.pop();
    }
    ids.pop();
    return false;
  };
  return buscar(raiz) ? { ids, bits: bits.join("") } : null;
}
