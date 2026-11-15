// Datos del inspector, sin DOM. Dos fuentes con el mismo formato de salida:
//   vistaDesdeAnalisis(analisis, entrada)   texto actual (estimacion exacta, sin generar el .hfa)
//   vistaDesdeHfa(bytes, nombreArchivo)     solo el .hfa: nada del texto original
import { aHex, codificar, construirArbol, generarCodigos, leerBits, leerHfa, metricas, simboloCorto, tabla, tamanoLegible, FIRMA } from "../../core/index.js";

const PREFIJO_BYTES = 96; // cuantos bytes de texto se codifican para la vista parcial de bits

function armar({ nombre, tamanoOriginal, tamanoFinal, totalBits, frecuencias, raiz, codigos, bitsMuestra, metadatos }) {
  const filas = tabla(frecuencias, codigos).map((f) => ({ ...f, ahorroBits: f.bitsOriginal - f.bitsTotales }));
  return { nombre, frecuencias, raiz, codigos, filas, totalBits, tamanoOriginal, tamanoFinal, metricas: metricas(tamanoOriginal, tamanoFinal, frecuencias.size), bitsMuestra, metadatos };
}

export function vistaDesdeAnalisis(analisis, entrada) {
  // Codificar solo el inicio del texto da exactamente los primeros bits del archivo final.
  const { datos, totalBits } = codificar(entrada.datos.subarray(0, PREFIJO_BYTES), analisis.codigos);
  return armar({ ...analisis, bitsMuestra: { datos, totalBits }, metadatos: null });
}

export function vistaDesdeHfa(bytes, nombreArchivo) {
  const info = leerHfa(bytes);
  const raiz = construirArbol(info.frecuencias);
  const punto = nombreArchivo.lastIndexOf(".");
  const metadatos = [
    ["Archivo", nombreArchivo],
    ["Extensión", punto >= 0 ? nombreArchivo.slice(punto) : "—"],
    ["Formato / versión", `${FIRMA} v${info.version}`],
    ["Nombre original", info.nombreOriginal],
    ["Total de bits codificados", info.totalBits.toLocaleString("en-US")],
    ["Bits válidos del último byte", String(info.bitsUltimoByte)],
    ["Tamaño del encabezado", tamanoLegible(info.tamanoEncabezado)],
    ["Tamaño de los datos", tamanoLegible(info.datos.length)],
    ["SHA-256 del original", aHex(info.sha256)],
  ];
  return { ...armar({ nombre: info.nombreOriginal, tamanoOriginal: info.tamanoOriginal, tamanoFinal: bytes.length, totalBits: info.totalBits, frecuencias: info.frecuencias, raiz, codigos: generarCodigos(raiz), bitsMuestra: { datos: info.datos, totalBits: info.totalBits }, metadatos }), info };
}

// Los primeros bytes en binario y hexadecimal: [{ binario: "01101110", hex: "6E" }]
export function bytesMuestra({ datos, totalBits }, cantidad = 12) {
  return Array.from({ length: Math.min(cantidad, Math.ceil(totalBits / 8)) }, (_, i) => ({
    binario: leerBits(datos, i * 8, Math.min(8, totalBits - i * 8)),
    hex: datos[i].toString(16).toUpperCase().padStart(2, "0"),
  }));
}

// Recorre el arbol sobre los primeros bits y separa las palabras de codigo:
// [{ bits: "110", simbolo: 98, etiqueta: "b" }, ...]  (hasta `maximo` simbolos)
export function segmentarBits({ datos, totalBits }, raiz, maximo = 24) {
  if (!raiz) return [];
  if (raiz.esHoja()) return Array.from({ length: Math.min(maximo, totalBits) }, () => ({ bits: "0", simbolo: raiz.simbolo, etiqueta: simboloCorto(raiz.simbolo) }));
  const salida = [];
  let nodo = raiz;
  let palabra = "";
  for (let i = 0; i < totalBits && salida.length < maximo; i++) {
    const bit = (datos[i >> 3] >> (7 - (i & 7))) & 1;
    palabra += bit;
    nodo = bit === 0 ? nodo.izquierdo : nodo.derecho;
    if (nodo.esHoja()) {
      salida.push({ bits: palabra, simbolo: nodo.simbolo, etiqueta: simboloCorto(nodo.simbolo) });
      nodo = raiz;
      palabra = "";
    }
  }
  return salida;
}
