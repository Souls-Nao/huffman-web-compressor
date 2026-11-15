import test from "node:test";
import assert from "node:assert/strict";
import { analizar, comprimir, FormatoError } from "../../core/index.js";
import { bytesMuestra, segmentarBits, vistaDesdeAnalisis, vistaDesdeHfa } from "./viewmodel.js";

const texto = new TextEncoder().encode("abracadabra");

test("vista desde el texto actual: tamano final exacto y bits por caracter", async () => {
  const entrada = { nombre: "abra.txt", datos: texto };
  const v = vistaDesdeAnalisis(analizar(texto, "abra.txt"), entrada);
  assert.equal(v.tamanoFinal, (await comprimir(texto, "abra.txt")).length);
  assert.equal(v.filas[0].bits, 1);
  assert.equal(v.filas[0].ahorroBits, 40 - 5);
  assert.equal(v.metadatos, null);
});

test("vista desde el .hfa: metadatos y misma tabla, sin el texto original", async () => {
  const v = vistaDesdeHfa(await comprimir(texto, "abra.txt"), "abra.hfa");
  const meta = Object.fromEntries(v.metadatos);
  assert.equal(meta["Formato / versión"], "HUFA v1");
  assert.equal(meta["Extensión"], ".hfa");
  assert.equal(meta["Total de bits codificados"], "23");
  assert.equal(meta["SHA-256 del original"].length, 64);
  assert.equal(v.tamanoFinal, 94);
  assert.throws(() => vistaDesdeHfa(new Uint8Array([1, 2, 3]), "x.hfa"), FormatoError);
});

test("bits: bytes en binario/hex y palabras de codigo", async () => {
  const v = vistaDesdeHfa(await comprimir(texto, "abra.txt"), "abra.hfa");
  const bytes = bytesMuestra(v.bitsMuestra);
  assert.deepEqual(bytes.map((b) => b.hex), ["6E", "8A", "DC"]);
  assert.equal(bytes[2].binario, "1101110"); // 7 bits validos
  const seg = segmentarBits(v.bitsMuestra, v.raiz);
  assert.equal(seg.map((s) => s.etiqueta).join(""), "abracadabra");
  assert.equal(seg.map((s) => s.bits).join(""), "01101110100010101101110");
  assert.equal(segmentarBits(v.bitsMuestra, v.raiz, 3).length, 3);
});

test("vista del texto actual coincide con el .hfa real en los primeros bits", async () => {
  const largo = new TextEncoder().encode("hola mundo, hola huffman ".repeat(30));
  const a = vistaDesdeAnalisis(analizar(largo, "l.txt"), { datos: largo });
  const b = vistaDesdeHfa(await comprimir(largo, "l.txt"), "l.hfa");
  const sa = segmentarBits(a.bitsMuestra, a.raiz, 40).map((s) => s.bits).join("");
  const sb = segmentarBits(b.bitsMuestra, b.raiz, 40).map((s) => s.bits).join("");
  assert.equal(sa, sb);
});
