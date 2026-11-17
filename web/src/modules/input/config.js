// Ajustes de la entrada. En produccion cambia GUTENBERG_PROXY por la URL de tu Worker.
//   desarrollo (npm start):  "/gutenberg"   (mismo origen, lo atiende proxy/dev-server.mjs)
//   produccion (GitHub Pages): "https://huffman-gutenberg.TU-USUARIO.workers.dev"
export const GUTENBERG_PROXY = "/gutenberg";
export const MAX_RESULTADOS = 25;
export const MAX_BYTES = 20 * 1024 * 1024; // la version con bits en texto recomienda <= ~20 MB
