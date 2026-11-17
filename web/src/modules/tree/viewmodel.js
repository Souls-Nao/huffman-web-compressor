// Datos del modulo del arbol, sin DOM (reutilizable en React Native).
import { caminoDeSimbolo, simboloLegible, tabla } from "../../core/index.js";

// Filas de la tabla de codigos, listas para mostrar.
export const filasCodigos = (frecuencias, codigos) => tabla(frecuencias, codigos);

// Explica un camino: "b -> 110: raiz, 1 (derecha), 1 (derecha), 0 (izquierda)".
export function describirCamino(raiz, codigos, simbolo) {
  const camino = caminoDeSimbolo(raiz, simbolo);
  if (!camino) return null;
  const codigo = codigos.get(simbolo);
  const pasos = [...camino.bits].map((b) => (b === "0" ? "0 (izquierda)" : "1 (derecha)"));
  return { simbolo, etiqueta: simboloLegible(simbolo), codigo, ids: camino.ids, pasos, texto: `${simboloLegible(simbolo)} → ${codigo}` };
}

// Serie para la grafica frecuencia vs bits: los `maximo` simbolos mas frecuentes.
// altura en [0,1] (escala log si hay mucha diferencia) y bits = largo del codigo.
export function serieGrafica(filas, maximo = 28) {
  const top = filas.slice(0, maximo);
  if (!top.length) return { barras: [], maxBits: 0 };
  const mayor = top[0].frecuencia;
  const usarLog = mayor / Math.max(1, top[top.length - 1].frecuencia) > 50;
  const escala = (f) => (usarLog ? Math.log(f + 1) / Math.log(mayor + 1) : f / mayor);
  return {
    barras: top.map((f) => ({ byte: f.byte, etiqueta: f.simbolo, frecuencia: f.frecuencia, bits: f.bits, altura: escala(f.frecuencia) })),
    maxBits: Math.max(...top.map((f) => f.bits)),
    escalaLog: usarLog,
  };
}
