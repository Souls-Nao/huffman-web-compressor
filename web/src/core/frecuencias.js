// Bloque 1 - Frecuencias. Un simbolo es un byte (0-255), igual que en la version Python.
// Regresa Map<byte, frecuencia> ordenado por simbolo (el orden hace el arbol determinista).
export function contarFrecuencias(datos) {
  const conteo = new Uint32Array(256);
  for (let i = 0; i < datos.length; i++) conteo[datos[i]]++;
  const frecuencias = new Map();
  for (let simbolo = 0; simbolo < 256; simbolo++) {
    if (conteo[simbolo] > 0) frecuencias.set(simbolo, conteo[simbolo]);
  }
  return frecuencias;
}
