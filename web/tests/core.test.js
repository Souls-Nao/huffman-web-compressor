// Pruebas unitarias del nucleo (equivalentes a tests/test_huffman.py y mas).
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { aHex, caminoDeSimbolo, codificar, comprimir, construirArbol, construirConPasos, contarFrecuencias, descomprimir, desempaquetar, distribuirArbol, distribuirBosque, empaquetar, escribirHfa, generarCodigos, leerHfa, metricas, simboloLegible, tabla, tamanoHfa, tamanoLegible, FormatoError } from "../src/core/index.js";

const bytes = (t) => new TextEncoder().encode(t);
const abra = bytes("abracadabra");

test("frecuencias de abracadabra", () => {
  assert.deepEqual([...contarFrecuencias(abra)], [[97, 5], [98, 2], [99, 1], [100, 1], [114, 2]]);
});

test("codigos calculados a mano (c+d, b+r, cd+br, a+resto)", () => {
  const codigos = generarCodigos(construirArbol(contarFrecuencias(abra)));
  assert.deepEqual([...codigos], [[97, "0"], [98, "110"], [99, "100"], [100, "101"], [114, "111"]]);
});

test("ningun codigo es prefijo de otro (256 simbolos)", () => {
  const datos = new Uint8Array([...Array(256).keys(), ...Array(256).keys(), 97, 97, 97, 98]);
  const codigos = [...generarCodigos(construirArbol(contarFrecuencias(datos))).values()];
  assert.equal(codigos.length, 256);
  for (const a of codigos) for (const b of codigos) if (a !== b) assert.ok(!b.startsWith(a));
});

test("casos borde del arbol: vacio y un solo simbolo", () => {
  assert.equal(construirArbol(new Map()), null);
  assert.deepEqual([...generarCodigos(null)], []);
  assert.deepEqual([...generarCodigos(construirArbol(contarFrecuencias(bytes("aaaa"))))], [[97, "0"]]);
});

test("la cola registrada coincide con el orden real de salida", () => {
  const { raiz, inicial, pasos } = construirConPasos(contarFrecuencias(abra));
  assert.equal(pasos.length, 4); // n - 1 uniones
  assert.deepEqual(inicial.map((n) => n.frecuencia), [1, 1, 2, 2, 5]);
  let previa = inicial;
  for (const p of pasos) {
    assert.equal(p.izquierdo, previa[0]); // salen siempre los dos primeros
    assert.equal(p.derecho, previa[1]);
    assert.ok(p.izquierdo.frecuencia <= p.derecho.frecuencia);
    assert.equal(p.cola.length, previa.length - 1);
    assert.ok(p.cola.includes(p.padre));
    previa = p.cola;
  }
  assert.equal(previa[0], raiz);
});

test("camino de un simbolo: ids y bits coherentes", () => {
  const raiz = construirArbol(contarFrecuencias(abra));
  const codigos = generarCodigos(raiz);
  for (const [simbolo, codigo] of codigos) {
    const c = caminoDeSimbolo(raiz, simbolo);
    assert.equal(c.bits, codigo);
    assert.equal(c.ids.length, codigo.length + 1); // sin ids de ramas descartadas
    assert.equal(c.ids[0], raiz.id);
  }
  assert.equal(caminoDeSimbolo(raiz, 200), null);
});

test("bits: empaquetar con relleno e ida y vuelta", () => {
  assert.deepEqual(empaquetar("0100000101"), { datos: new Uint8Array([0x41, 0x40]), bitsUltimoByte: 2 });
  assert.deepEqual(empaquetar("01000001"), { datos: new Uint8Array([0x41]), bitsUltimoByte: 8 });
  assert.deepEqual(empaquetar(""), { datos: new Uint8Array(0), bitsUltimoByte: 0 });
  for (const bits of ["", "1", "0101", "01010101", "110010101"]) assert.equal(desempaquetar(empaquetar(bits).datos, bits.length), bits);
});

test("codificar (eficiente) produce lo mismo que empaquetar(texto de bits)", () => {
  const datos = bytes("el veloz murcielago hindu comia feliz cardillo y kiwi");
  const codigos = generarCodigos(construirArbol(contarFrecuencias(datos)));
  const texto = [...datos].map((b) => codigos.get(b)).join("");
  const a = codificar(datos, codigos);
  const b = empaquetar(texto);
  assert.deepEqual(a.datos, b.datos);
  assert.equal(a.totalBits, texto.length);
  assert.equal(a.bitsUltimoByte, b.bitsUltimoByte);
});

test("formato: el ejemplo documentado de abracadabra (94 bytes) sale byte a byte igual", async () => {
  const hfa = await comprimir(abra, "abra.txt");
  const doc = readFileSync(new URL("./fixtures/abra.hfa", import.meta.url)); // generado con el compresor Python
  assert.equal(hfa.length, 94);
  assert.equal(aHex(hfa), doc.toString("hex"));
  assert.ok(aHex(hfa).endsWith("6e8adc"));
});

test("formato: campos del encabezado", async () => {
  const info = leerHfa(await comprimir(abra, "abra.txt"));
  assert.equal(info.version, 1);
  assert.equal(info.nombreOriginal, "abra.txt");
  assert.equal(info.tamanoOriginal, 11);
  assert.equal(info.totalBits, 23);
  assert.equal(info.bitsUltimoByte, 7);
  assert.equal(info.tamanoEncabezado, 58 + 8 + 5 * 5);
  assert.equal(info.datos.length, 3);
  assert.equal(tamanoHfa("abra.txt", 5, 23), 94);
});

test("formato: no guarda el texto original", async () => {
  const hfa = await comprimir(bytes("texto secreto que no debe aparecer ".repeat(20)), "x.txt");
  assert.ok(!Buffer.from(hfa).includes("texto secreto"));
});

test("formato: rechaza archivos invalidos, truncados o alterados", async () => {
  const bueno = await comprimir(bytes("abracadabra".repeat(10)), "a.txt");
  assert.throws(() => leerHfa(bytes("esto no es hfa")), FormatoError);
  assert.throws(() => leerHfa(new Uint8Array(0)), FormatoError);
  assert.throws(() => leerHfa(bueno.slice(0, 20)), FormatoError);
  assert.throws(() => leerHfa(bueno.slice(0, bueno.length - 1)), FormatoError); // datos truncados
  const version = bueno.slice(); version[4] = 9;
  assert.throws(() => leerHfa(version), /Versión 9/);
  const tamano = bueno.slice(); tamano[5] ^= 1; // tamano original alterado
  assert.throws(() => leerHfa(tamano), FormatoError);
});

const CASOS = {
  "texto normal": bytes("abracadabra"),
  "vacio": new Uint8Array(0),
  "un solo simbolo": bytes("aaaaaaa"),
  "un solo byte": bytes("x"),
  "acentos y saltos de Windows": bytes("¡Hola, ñandú!\r\nAdiós.\r\n"),
  "latin-1": Uint8Array.from("canción", (c) => c.charCodeAt(0)),
  "los 256 bytes": Uint8Array.from({ length: 1024 }, (_, i) => i % 256),
};
for (const [nombre, datos] of Object.entries(CASOS)) {
  test(`integridad ida y vuelta: ${nombre}`, async () => {
    const { datos: recuperado, integridadOk } = await descomprimir(await comprimir(datos, "prueba.txt"));
    assert.deepEqual(recuperado, datos);
    assert.ok(integridadOk);
  });
}

test("integridad: 200 entradas aleatorias reproducibles", async () => {
  let semilla = 12345;
  const azar = () => (semilla = (semilla * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
  for (let i = 0; i < 200; i++) {
    const largo = Math.floor(azar() * 400);
    const variedad = 1 + Math.floor(azar() * 255);
    const datos = Uint8Array.from({ length: largo }, () => Math.floor(azar() ** 2 * variedad));
    const { datos: r, integridadOk } = await descomprimir(await comprimir(datos, "r.txt"));
    assert.deepEqual(r, datos);
    assert.ok(integridadOk);
  }
});

test("integridad: detecta un bit cambiado en los datos", async () => {
  const hfa = await comprimir(bytes("abracadabra".repeat(10)), "p.txt");
  hfa[hfa.length - 3] ^= 0x80;
  const { integridadOk } = await descomprimir(hfa);
  assert.equal(integridadOk, false);
});

test("metricas y tamano legible", () => {
  const m = metricas(1000, 600, 40);
  assert.equal(m.ahorro, 400);
  assert.ok(Math.abs(m.reduccion - 40) < 1e-9);
  assert.ok(Math.abs(m.razon - 1000 / 600) < 1e-9);
  assert.equal(metricas(0, 0, 0).reduccion, 0);
  assert.equal(tamanoLegible(2225803), "2,225,803 B (2.12 MB)");
  assert.equal(tamanoLegible(1024), "1,024 B (1.00 KB)");
});

test("simbolos y tabla", () => {
  assert.equal(simboloLegible(97), "a");
  assert.equal(simboloLegible(10), "\\n (salto)");
  assert.equal(simboloLegible(195), "0xC3");
  const f = contarFrecuencias(abra);
  const filas = tabla(f, generarCodigos(construirArbol(f)));
  assert.equal(filas[0].simbolo, "a");
  assert.equal(filas[0].bitsTotales, 5);
  assert.equal(filas[1].bitsOriginal, 16);
});

test("layout: cada hoja una columna y padres centrados", () => {
  const raiz = construirArbol(contarFrecuencias(abra));
  const d = distribuirArbol(raiz);
  assert.equal(d.nodos.length, 9);
  assert.equal(d.aristas.length, 8);
  assert.equal(d.columnas, 5);
  const x = new Map(d.nodos.map((n) => [n.id, n.x]));
  for (const a of d.aristas) assert.ok(x.has(a.de) && x.has(a.a));
  const b = distribuirBosque([raiz, raiz.izquierdo], 1);
  assert.ok(b.columnas > d.columnas);
});

test("escribirHfa/leerHfa: tabla de 256 simbolos", () => {
  const f = new Map([...Array(256).keys()].map((i) => [i, 1]));
  const hfa = escribirHfa({ nombre: "ñ.txt", tamanoOriginal: 256, sha256: new Uint8Array(32), frecuencias: f, datos: new Uint8Array(32), totalBits: 256, bitsUltimoByte: 8 });
  assert.equal(leerHfa(hfa).frecuencias.size, 256);
});
