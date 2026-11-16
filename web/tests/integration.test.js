// Pruebas de integracion: flujo completo y compatibilidad con la version Python.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { writeFileSync } from "node:fs";
import { analizar, comprimir, descomprimir, leerHfa, sha256, aHex } from "../src/core/index.js";

const RAIZ = new URL("../../", import.meta.url).pathname;
const LICENCIA = "/usr/share/common-licenses/GPL-3";
const textoLargo = () => (existsSync(LICENCIA) ? new Uint8Array(readFileSync(LICENCIA)) : new TextEncoder().encode("Lorem ipsum dolor sit amet ".repeat(2000)));

test("flujo: original -> .hfa -> recuperado, sin el original", async () => {
  const original = textoLargo();
  const hfa = await comprimir(original, "libro.txt");
  const { datos, integridadOk, info } = await descomprimir(new Uint8Array(hfa)); // solo se usa el .hfa
  assert.ok(integridadOk);
  assert.equal(aHex(await sha256(datos)), aHex(await sha256(original)));
  assert.equal(info.nombreOriginal, "libro.txt");
  assert.ok(hfa.length < original.length * 0.7, "un texto en ingles debe comprimir bastante");
});

test("el analisis predice exactamente el tamano del .hfa real", async () => {
  const original = textoLargo();
  const analisis = analizar(original, "libro.txt");
  assert.equal(analisis.tamanoFinal, (await comprimir(original, "libro.txt")).length);
  assert.equal(analisis.totalBits, leerHfa(await comprimir(original, "libro.txt")).totalBits);
});

test("cada .hfa generado aqui tiene datos de largo ceil(bits/8)", async () => {
  for (const t of ["a", "ab", "abc", "aab", "mississippi"]) {
    const info = leerHfa(await comprimir(new TextEncoder().encode(t), "t.txt"));
    assert.equal(info.datos.length, Math.ceil(info.totalBits / 8));
  }
});

const python = spawnSync("python3", ["--version"]).status === 0;
test("compatibilidad: Python comprime, JS descomprime (y al reves, byte a byte)", { skip: !python && "python3 no disponible" }, async () => {
  const original = textoLargo();
  const ruta = (n) => join(tmpdir(), `hfa-${process.pid}-${n}`);
  writeFileSync(ruta("orig.txt"), original);
  const py = spawnSync("python3", ["-c", `
import sys; sys.path.insert(0, ${JSON.stringify(RAIZ)})
from huffman.compresor import comprimir
open(${JSON.stringify(ruta("py.hfa"))}, "wb").write(comprimir(open(${JSON.stringify(ruta("orig.txt"))}, "rb").read(), "libro.txt"))
`]);
  assert.equal(py.status, 0, py.stderr?.toString());
  const dePython = new Uint8Array(readFileSync(ruta("py.hfa")));
  const deJs = await comprimir(original, "libro.txt");
  assert.deepEqual(deJs, dePython, "JS y Python deben producir el mismo archivo");
  const { datos, integridadOk } = await descomprimir(dePython);
  assert.ok(integridadOk);
  assert.deepEqual(datos, original);
  writeFileSync(ruta("js.hfa"), deJs);
  const inverso = spawnSync("python3", ["-c", `
import sys; sys.path.insert(0, ${JSON.stringify(RAIZ)})
from huffman.compresor import descomprimir
d, ok = descomprimir(open(${JSON.stringify(ruta("js.hfa"))}, "rb").read())
sys.exit(0 if ok and d == open(${JSON.stringify(ruta("orig.txt"))}, "rb").read() else 1)
`]);
  assert.equal(inverso.status, 0, "Python debe poder leer el .hfa de JS");
});
