// Geometria pura del arbol (sin DOM): cada hoja ocupa una columna, cada padre se centra
// sobre sus hijos y la profundidad es la fila. Las vistas (SVG, React Native SVG) solo dibujan.

// Regresa { nodos: [{id, x, y, nodo}], aristas: [{de, a, bit}], columnas, filas }
// x en columnas (0..columnas-1), y en niveles (0..filas-1). `desdeColumna` permite colocar
// varios arboles lado a lado (bosque).
export function distribuirArbol(raiz, desdeColumna = 0) {
  const nodos = [];
  const aristas = [];
  let columna = desdeColumna;
  let filas = 0;
  const colocar = (nodo, nivel) => {
    filas = Math.max(filas, nivel + 1);
    let x;
    if (nodo.esHoja()) {
      x = columna++;
    } else {
      const xi = colocar(nodo.izquierdo, nivel + 1);
      const xd = colocar(nodo.derecho, nivel + 1);
      aristas.push({ de: nodo.id, a: nodo.izquierdo.id, bit: "0" }, { de: nodo.id, a: nodo.derecho.id, bit: "1" });
      x = (xi + xd) / 2;
    }
    nodos.push({ id: nodo.id, x, y: nivel, nodo });
    return x;
  };
  if (raiz) colocar(raiz, 0);
  return { nodos, aristas, columnas: columna - desdeColumna, filas };
}

// Varios arboles (la cola de prioridad en un paso): se colocan uno junto a otro con un hueco.
export function distribuirBosque(raices, hueco = 1) {
  const total = { nodos: [], aristas: [], columnas: 0, filas: 0, raices: [] };
  let columna = 0;
  for (const raiz of raices) {
    const parcial = distribuirArbol(raiz, columna);
    total.nodos.push(...parcial.nodos);
    total.aristas.push(...parcial.aristas);
    total.raices.push({ id: raiz.id, x: parcial.nodos[parcial.nodos.length - 1].x });
    total.filas = Math.max(total.filas, parcial.filas);
    columna += parcial.columnas + hueco;
  }
  total.columnas = Math.max(0, columna - hueco);
  return total;
}
