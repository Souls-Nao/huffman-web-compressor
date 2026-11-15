// Analisis completo de una entrada: lo calcula la app una sola vez y los modulos lo leen del store.
import { construirConPasos } from "./arbol.js";
import { generarCodigos } from "./codigos.js";
import { tamanoHfa } from "./formato.js";
import { contarFrecuencias } from "./frecuencias.js";

export function analizar(datos, nombre) {
  const frecuencias = contarFrecuencias(datos);
  const { raiz, inicial, pasos } = construirConPasos(frecuencias);
  const codigos = generarCodigos(raiz);
  let totalBits = 0;
  for (const [simbolo, frecuencia] of frecuencias) totalBits += frecuencia * codigos.get(simbolo).length;
  return {
    nombre,
    tamanoOriginal: datos.length,
    frecuencias,
    raiz,
    codigos,
    inicial,
    pasos,
    totalBits,
    tamanoFinal: tamanoHfa(nombre, frecuencias.size, totalBits), // tamano exacto del .hfa, sin generarlo
  };
}
