// Servidor local sin dependencias:  npm start  ->  http://localhost:8080
// Sirve web/ y, en /gutenberg/*, reutiliza el MISMO proxy del Worker (mismo origen = sin CORS).
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { manejar } from "./worker.js";

const RAIZ = resolve(fileURLToPath(new URL("..", import.meta.url)));
const PUERTO = Number(process.env.PORT ?? 8080);
const TIPOS = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".json": "application/json", ".svg": "image/svg+xml", ".txt": "text/plain; charset=utf-8" };

createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  try {
    if (url.pathname.startsWith("/gutenberg/")) {
      const destino = new Request(`http://local${url.pathname.slice("/gutenberg".length)}${url.search}`, { method: req.method });
      const respuesta = await manejar(destino);
      res.writeHead(respuesta.status, Object.fromEntries(respuesta.headers));
      res.end(Buffer.from(await respuesta.arrayBuffer()));
      return;
    }
    const ruta = normalize(decodeURIComponent(url.pathname === "/" ? "/index.html" : url.pathname));
    const archivo = join(RAIZ, ruta);
    if (archivo !== RAIZ && !archivo.startsWith(RAIZ + sep)) throw Object.assign(new Error("fuera de la raiz"), { codigo: 403 });
    const cuerpo = await readFile(archivo);
    res.writeHead(200, { "content-type": TIPOS[extname(archivo)] ?? "application/octet-stream" });
    res.end(cuerpo);
  } catch (error) {
    res.writeHead(error.codigo ?? 404, { "content-type": "text/plain; charset=utf-8" });
    res.end("No encontrado");
  }
}).listen(PUERTO, () => console.log(`Huffman Web Compressor en http://localhost:${PUERTO}`));
