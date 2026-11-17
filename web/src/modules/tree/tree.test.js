import test from "node:test";
import assert from "node:assert/strict";
import { construirArbol, contarFrecuencias, generarCodigos } from "../../core/index.js";
import { describirCamino, filasCodigos, serieGrafica } from "./viewmodel.js";

const f = contarFrecuencias(new TextEncoder().encode("abracadabra"));
const raiz = construirArbol(f);
const codigos = generarCodigos(raiz);

test("describirCamino de b", () => {
  const c = describirCamino(raiz, codigos, 98);
  assert.equal(c.texto, "b → 110");
  assert.equal(c.ids.length, 4);
  assert.deepEqual(c.pasos, ["1 (derecha)", "1 (derecha)", "0 (izquierda)"]);
  assert.equal(describirCamino(raiz, codigos, 1), null);
});

test("serieGrafica: orden por frecuencia, alturas en [0,1] y bits", () => {
  const { barras, maxBits } = serieGrafica(filasCodigos(f, codigos));
  assert.equal(barras[0].etiqueta, "a");
  assert.equal(barras[0].altura, 1);
  assert.equal(maxBits, 3);
  assert.ok(barras.every((b) => b.altura > 0 && b.altura <= 1));
  assert.deepEqual(serieGrafica([]), { barras: [], maxBits: 0 });
});
