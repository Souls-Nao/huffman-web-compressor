import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { parsearOpds, decodificarXml } from "./opds.js";
import { buscar, descargar, GutenbergError } from "./gutenberg.js";
import { manejar } from "../../../proxy/worker.js";

const xml = readFileSync(new URL("./fixtures/opds-muestra.xml", import.meta.url), "utf8");
const respuesta = (cuerpo, init = {}) => new Response(cuerpo, init);

test("opds: lista libros, decodifica entidades y descarta navegacion y repetidos", () => {
  const libros = parsearOpds(xml);
  assert.deepEqual(libros.map((l) => l.id), [2000, 17989]);
  assert.equal(libros[0].titulo, "Don Quijote");
  assert.equal(libros[1].titulo, 'Tom & Jerry: "Cuentos" épicos');
  assert.equal(libros[1].autor, "Autor <Anónimo>");
  assert.equal(decodificarXml("&#x41;&amp;"), "A&");
});

test("gutenberg.buscar: arma la URL y limita resultados", async () => {
  let pedida;
  const fetchFn = async (url) => (pedida = url, respuesta(xml));
  const libros = await buscar("don quijote", { proxy: "/g", fetchFn, limite: 1 });
  assert.equal(pedida, "/g/ebooks/search.opds/?query=don%20quijote");
  assert.equal(libros.length, 1);
  assert.deepEqual(await buscar("   ", { fetchFn }), []);
});

test("gutenberg.descargar: bytes, progreso y errores claros", async () => {
  const datos = new TextEncoder().encode("hola libro");
  const progresos = [];
  const ok = await descargar(7, { proxy: "/g", fetchFn: async (u) => (assert.equal(u, "/g/cache/epub/7/pg7.txt"), respuesta(datos, { headers: { "content-length": String(datos.length) } })), alProgreso: (f) => progresos.push(f) });
  assert.deepEqual(ok, datos);
  assert.equal(progresos.at(-1), 1);
  await assert.rejects(descargar(7, { fetchFn: async () => respuesta("", { status: 404 }) }), /texto plano/);
  await assert.rejects(descargar(7, { fetchFn: async () => { throw new TypeError("red"); } }), GutenbergError);
  await assert.rejects(descargar(7, { maxBytes: 3, fetchFn: async () => respuesta(datos) }), /20 MB/);
  await assert.rejects(descargar(-1), /inválido/);
});

test("proxy: solo reenvia las dos rutas permitidas y agrega CORS", async () => {
  const vistas = [];
  const buscarFalso = async (url) => (vistas.push(url), respuesta("ok", { headers: { "content-type": "text/plain" } }));
  const r1 = await manejar(new Request("http://x/ebooks/search.opds/?query=a"), buscarFalso);
  assert.equal(r1.status, 200);
  assert.equal(r1.headers.get("access-control-allow-origin"), "*");
  assert.equal(vistas[0], "https://www.gutenberg.org/ebooks/search.opds/?query=a");
  assert.equal((await manejar(new Request("http://x/cache/epub/84/pg84.txt"), buscarFalso)).status, 200);
  for (const ruta of ["/etc/passwd", "/ebooks/84", "/cache/epub/84/pg84.txt/../../x", "/cache/epub/a/pga.txt"]) assert.equal((await manejar(new Request("http://x" + ruta), buscarFalso)).status, 403, ruta);
  assert.equal((await manejar(new Request("http://x/ebooks/search.opds/", { method: "POST" }), buscarFalso)).status, 405);
  assert.equal((await manejar(new Request("http://x/ebooks/search.opds/", { method: "OPTIONS" }), buscarFalso)).status, 204);
  assert.equal((await manejar(new Request("http://x/ebooks/search.opds/?query=a"), async () => { throw new Error("caido"); })).status, 502);
  assert.equal(vistas.length, 2);
});
