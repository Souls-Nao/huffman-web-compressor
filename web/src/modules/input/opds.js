// Lee el catalogo OPDS (Atom/XML) de Project Gutenberg sin DOMParser, para poder
// probarlo en Node. Regresa [{ id, titulo, autor }] y descarta entradas de navegacion.
const ENTIDADES = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'" };

export function decodificarXml(texto) {
  return texto
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")
    .replace(/&(#x[0-9a-f]+|#\d+|amp|lt|gt|quot|apos);/gi, (_, e) => {
      if (e[0] === "#") return String.fromCodePoint(e[1].toLowerCase() === "x" ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10));
      return ENTIDADES[e.toLowerCase()];
    })
    .trim();
}

const etiqueta = (entrada, nombre) => {
  const m = entrada.match(new RegExp(`<${nombre}\\b[^>]*>([\\s\\S]*?)</${nombre}>`, "i"));
  return m ? decodificarXml(m[1]) : "";
};

export function parsearOpds(xml) {
  const libros = [];
  const vistos = new Set();
  for (const [entrada] of xml.matchAll(/<entry\b[\s\S]*?<\/entry>/gi)) {
    const m = entrada.match(/\/ebooks\/(\d+)(?!\d)/); // /ebooks/2000.opds; /ebooks/author/12 no coincide
    if (!m || vistos.has(m[1])) continue;
    vistos.add(m[1]);
    libros.push({ id: Number(m[1]), titulo: etiqueta(entrada, "title") || `Libro ${m[1]}`, autor: etiqueta(entrada, "content") });
  }
  return libros;
}
