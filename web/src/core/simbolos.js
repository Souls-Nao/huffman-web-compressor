// Bloque 10 - Datos listos para mostrar (sin DOM, reutilizable en React Native).
const ESPECIALES = { 9: "\\t (tab)", 10: "\\n (salto)", 13: "\\r (retorno)", 32: "␣ (espacio)" };

// 97 -> "a", 10 -> "\n (salto)", 195 -> "0xC3"
export function simboloLegible(simbolo) {
  if (ESPECIALES[simbolo]) return ESPECIALES[simbolo];
  if (simbolo >= 33 && simbolo <= 126) return String.fromCharCode(simbolo);
  return "0x" + simbolo.toString(16).toUpperCase().padStart(2, "0");
}

// Etiqueta corta para nodos del arbol (una sola celda).
export function simboloCorto(simbolo) {
  if (simbolo === 32) return "␣";
  if (simbolo === 10) return "\\n";
  if (simbolo === 13) return "\\r";
  if (simbolo === 9) return "\\t";
  return simbolo >= 33 && simbolo <= 126 ? String.fromCharCode(simbolo) : simboloLegible(simbolo).slice(2);
}

// Filas: simbolo, byte, frecuencia, %, y si hay codigos: codigo, bits, bitsTotales, bitsOriginal.
// Ordenadas de mayor a menor frecuencia.
export function tabla(frecuencias, codigos = null) {
  const total = [...frecuencias.values()].reduce((a, b) => a + b, 0);
  return [...frecuencias]
    .sort((a, b) => b[1] - a[1] || a[0] - b[0])
    .map(([byte, frecuencia]) => {
      const fila = { simbolo: simboloLegible(byte), byte, frecuencia, porcentaje: Math.round((frecuencia / total) * 100000) / 1000 };
      if (codigos) {
        const codigo = codigos.get(byte);
        Object.assign(fila, { codigo, bits: codigo.length, bitsTotales: codigo.length * frecuencia, bitsOriginal: 8 * frecuencia });
      }
      return fila;
    });
}
