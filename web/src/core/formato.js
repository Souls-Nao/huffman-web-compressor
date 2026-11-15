// Bloque 5 - Formato propio .hfa (version 1). Identico al de Python (docs/FORMATO.md).
//
//   firma "HUFA" (4) | version (1) | tamano original (8) | total de bits (8)
//   | bits validos del ultimo byte (1) | SHA-256 del original (32)
//   | largo del nombre N (2) | nombre (N) | numero de simbolos S (2)
//   | tabla: S x [simbolo (1) + frecuencia (4)] | datos comprimidos (resto)
//
// Enteros sin signo, little-endian. Se guarda la tabla de frecuencias, NO el arbol.

export const FIRMA = "HUFA";
export const VERSION = 1;
export const EXTENSION = ".hfa";
export const TAMANO_FIJO = 58; // 4+1+8+8+1+32+2+2 (incluye el campo "numero de simbolos")

export class FormatoError extends Error {}

// Bytes del .hfa sin construirlo: sirve para mostrar el tamano final antes de comprimir.
export function tamanoHfa(nombre, numSimbolos, totalBits) {
  return TAMANO_FIJO + new TextEncoder().encode(nombre).length + 5 * numSimbolos + Math.ceil(totalBits / 8);
}

export function escribirHfa({ nombre, tamanoOriginal, sha256, frecuencias, datos, totalBits, bitsUltimoByte }) {
  const nombreBytes = new TextEncoder().encode(nombre);
  const encabezado = TAMANO_FIJO + nombreBytes.length + 5 * frecuencias.size;
  const salida = new Uint8Array(encabezado + datos.length);
  const vista = new DataView(salida.buffer);
  salida.set(new TextEncoder().encode(FIRMA), 0);
  vista.setUint8(4, VERSION);
  vista.setBigUint64(5, BigInt(tamanoOriginal), true);
  vista.setBigUint64(13, BigInt(totalBits), true);
  vista.setUint8(21, bitsUltimoByte);
  salida.set(sha256, 22);
  vista.setUint16(54, nombreBytes.length, true);
  salida.set(nombreBytes, 56);
  let pos = 56 + nombreBytes.length;
  vista.setUint16(pos, frecuencias.size, true);
  pos += 2;
  for (const [simbolo, frecuencia] of frecuencias) {
    vista.setUint8(pos, simbolo);
    vista.setUint32(pos + 1, frecuencia, true);
    pos += 5;
  }
  salida.set(datos, pos);
  return salida;
}

// Lee un .hfa y regresa sus campos. Lanza FormatoError si no es valido.
export function leerHfa(contenido) {
  const rechazar = (mensaje) => {
    throw new FormatoError(mensaje);
  };
  if (contenido.length < 4 || new TextDecoder().decode(contenido.subarray(0, 4)) !== FIRMA) {
    rechazar("No es un archivo .hfa válido (firma incorrecta).");
  }
  if (contenido.length < TAMANO_FIJO) rechazar("El archivo .hfa está incompleto o dañado.");
  const vista = new DataView(contenido.buffer, contenido.byteOffset, contenido.byteLength);
  const version = vista.getUint8(4);
  if (version !== VERSION) rechazar(`Versión ${version} no soportada (se esperaba ${VERSION}).`);
  const tamanoOriginal = Number(vista.getBigUint64(5, true));
  const totalBits = Number(vista.getBigUint64(13, true));
  const bitsUltimoByte = vista.getUint8(21);
  const sha256 = contenido.slice(22, 54);
  const largoNombre = vista.getUint16(54, true);
  let pos = 56;
  if (pos + largoNombre + 2 > contenido.length) rechazar("El archivo .hfa está incompleto o dañado.");
  let nombre;
  try {
    nombre = new TextDecoder("utf-8", { fatal: true }).decode(contenido.subarray(pos, pos + largoNombre));
  } catch {
    rechazar("El archivo .hfa está incompleto o dañado.");
  }
  pos += largoNombre;
  const numSimbolos = vista.getUint16(pos, true);
  pos += 2;
  if (numSimbolos > 256 || pos + 5 * numSimbolos > contenido.length) rechazar("El archivo .hfa está incompleto o dañado.");
  const frecuencias = new Map();
  let suma = 0;
  for (let i = 0; i < numSimbolos; i++) {
    const simbolo = vista.getUint8(pos);
    const frecuencia = vista.getUint32(pos + 1, true);
    if (frecuencias.has(simbolo)) rechazar("Tabla de frecuencias con símbolos repetidos.");
    frecuencias.set(simbolo, frecuencia);
    suma += frecuencia;
    pos += 5;
  }
  const datos = contenido.subarray(pos);
  // Coherencia interna: detecta archivos truncados o con encabezado alterado.
  if (suma !== tamanoOriginal) rechazar("La tabla de frecuencias no coincide con el tamaño original.");
  if (totalBits < tamanoOriginal) rechazar("El total de bits es menor que el tamaño original (cada símbolo usa al menos 1 bit).");
  if (datos.length !== Math.ceil(totalBits / 8)) rechazar("Los datos comprimidos están truncados o sobran bytes.");
  if (totalBits > 0 && bitsUltimoByte !== (totalBits % 8 || 8)) rechazar("Bits válidos del último byte inconsistentes.");
  return { version, nombreOriginal: nombre, tamanoOriginal, totalBits, bitsUltimoByte, sha256, frecuencias, tamanoEncabezado: pos, datos };
}
