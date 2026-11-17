// Proxy gratuito para Project Gutenberg (Cloudflare Workers, plan gratis).
// Por que existe: gutenberg.org no envia cabeceras CORS, asi que el navegador no puede
// leerlo directo. Este proxy solo reenvia DOS rutas fijas y agrega CORS. Nada mas.
//
// Despliegue:  npx wrangler deploy proxy/worker.js --name huffman-gutenberg --compatibility-date 2026-01-01
// Luego pon la URL resultante en src/modules/input/config.js (GUTENBERG_PROXY).
const ORIGEN = "https://www.gutenberg.org";
const RUTAS = [
  /^\/ebooks\/search\.opds\/?$/, // catalogo OPDS (buscar por titulo, autor o tema)
  /^\/cache\/epub\/\d+\/pg\d+\.txt$/, // texto plano de un libro
];
const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, OPTIONS",
  "access-control-allow-headers": "content-type",
};

export async function manejar(request, buscar = fetch) {
  const url = new URL(request.url);
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
  if (request.method !== "GET") return new Response("Metodo no permitido", { status: 405, headers: CORS });
  if (!RUTAS.some((regla) => regla.test(url.pathname)) || url.search.length > 300) {
    return new Response("Ruta no permitida", { status: 403, headers: CORS });
  }
  let respuesta;
  try {
    respuesta = await buscar(ORIGEN + url.pathname + url.search, {
      headers: { "user-agent": "huffman-web-compressor (proyecto escolar)" },
      redirect: "follow",
    });
  } catch {
    return new Response("No se pudo contactar a gutenberg.org", { status: 502, headers: CORS });
  }
  const cabeceras = new Headers(CORS);
  cabeceras.set("content-type", respuesta.headers.get("content-type") ?? "text/plain; charset=utf-8");
  cabeceras.set("cache-control", "public, max-age=3600");
  return new Response(respuesta.body, { status: respuesta.status, headers: cabeceras });
}

export default { fetch: (request) => manejar(request) };
