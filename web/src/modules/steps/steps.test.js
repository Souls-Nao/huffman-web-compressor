import test from "node:test";
import assert from "node:assert/strict";
import { analizar } from "../../core/index.js";
import { crearVistaPasos, idsDeSubarbol } from "./viewmodel.js";

const analisis = analizar(new TextEncoder().encode("abracadabra"), "a.txt");
const vista = crearVistaPasos(analisis);

test("paso 0: cola inicial ordenada, sin union", () => {
  const e = vista.estado(0);
  assert.equal(vista.total, 4);
  assert.deepEqual(e.despues.map((x) => x.frecuencia), [1, 1, 2, 2, 5]);
  assert.equal(e.paso, null);
  assert.equal(e.antes, null);
});

test("paso 1: salen c y d, nace un nodo de 2", () => {
  const e = vista.estado(1);
  assert.deepEqual([e.paso.izquierdo.etiqueta, e.paso.derecho.etiqueta], ["c:1", "d:1"]);
  assert.equal(e.paso.padre.frecuencia, 2);
  assert.deepEqual(e.antes.filter((x) => x.marca).map((x) => x.marca), ["izquierdo", "derecho"]);
  assert.equal(e.despues.filter((x) => x.marca === "nuevo").length, 1);
  assert.match(e.texto, /Paso 1 de 4/);
});

test("ultimo paso: una sola raiz de 11 y el bosque la contiene completa", () => {
  const e = vista.estado(4);
  assert.deepEqual(e.despues.map((x) => x.frecuencia), [11]);
  assert.equal(idsDeSubarbol(e.raices[0]).size, 9);
  assert.match(e.texto, /completo/);
});

test("fuera de rango y un solo simbolo", () => {
  assert.throws(() => vista.estado(5), RangeError);
  const uno = crearVistaPasos(analizar(new TextEncoder().encode("zzz"), "z.txt"));
  assert.equal(uno.total, 0);
  assert.match(uno.estado(0).texto, /Un solo símbolo/);
});
