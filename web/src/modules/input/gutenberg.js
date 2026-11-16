// Bloque 8 - Integracion con Project Gutenberg (via proxy, ver proxy/worker.js).
import { GUTENBERG_PROXY, MAX_BYTES, MAX_RESULTADOS } from "./config.js";
import { parsearOpds } from "./opds.js";

export class GutenbergError extends Error {}

async function pedir(url, fetchFn, senal) {
  let respuesta;
  try {
    respuesta = await fetchFn(url, { signal: senal });
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new GutenbergError("No se pudo contactar el proxy de Gutenberg. Ejecuta `npm start` o configura GUTENBERG_PROXY (ver README).");
  }
  if (respuesta.status === 404) throw new GutenbergError("Ese libro no tiene versión de texto plano en Gutenberg.");
  if (!respuesta.ok) throw new GutenbergError(`Gutenberg respondió con el error ${respuesta.status}.`);
  return respuesta;
}

// Una sola busqueda cubre titulo, autor y tema. Regresa hasta `limite` libros.
export async function buscar(texto, { proxy = GUTENBERG_PROXY, fetchFn = fetch, limite = MAX_RESULTADOS, senal } = {}) {
  const consulta = texto.trim();
  if (!consulta) return [];
  const respuesta = await pedir(`${proxy}/ebooks/search.opds/?query=${encodeURIComponent(consulta)}`, fetchFn, senal);
  return parsearOpds(await respuesta.text()).slice(0, limite);
}

// Descarga el texto plano. `alProgreso(fraccion)` se llama si el servidor informa el tamano.
export async function descargar(id, { proxy = GUTENBERG_PROXY, fetchFn = fetch, senal, alProgreso, maxBytes = MAX_BYTES } = {}) {
  if (!Number.isInteger(id) || id <= 0) throw new GutenbergError("Identificador de libro inválido.");
  const respuesta = await pedir(`${proxy}/cache/epub/${id}/pg${id}.txt`, fetchFn, senal);
  const total = Number(respuesta.headers.get("content-length")) || 0;
  if (total > maxBytes) throw new GutenbergError("El libro supera el límite de 20 MB.");
  if (!respuesta.body?.getReader) {
    const datos = new Uint8Array(await respuesta.arrayBuffer());
    if (datos.length > maxBytes) throw new GutenbergError("El libro supera el límite de 20 MB.");
    return datos;
  }
  const lector = respuesta.body.getReader();
  const trozos = [];
  let recibidos = 0;
  for (;;) {
    const { done, value } = await lector.read();
    if (done) break;
    recibidos += value.length;
    if (recibidos > maxBytes) throw new GutenbergError("El libro supera el límite de 20 MB.");
    trozos.push(value);
    if (total) alProgreso?.(recibidos / total);
  }
  const datos = new Uint8Array(recibidos);
  let pos = 0;
  for (const trozo of trozos) {
    datos.set(trozo, pos);
    pos += trozo.length;
  }
  return datos;
}
