// Bloque 6 - Compresor, descompresor, integridad (SHA-256) y metricas.
//   comprimir:    datos -> frecuencias -> arbol -> codigos -> bits -> .hfa
//   descomprimir: .hfa -> arbol -> bits -> datos -> verificar SHA-256
import { construirArbol } from "./arbol.js";
import { codificar } from "./bits.js";
import { generarCodigos } from "./codigos.js";
import { escribirHfa, leerHfa } from "./formato.js";
import { contarFrecuencias } from "./frecuencias.js";

export async function sha256(datos) {
  return new Uint8Array(await globalThis.crypto.subtle.digest("SHA-256", datos));
}

export function aHex(bytes) {
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

export async function comprimir(datos, nombre) {
  const frecuencias = contarFrecuencias(datos);
  const codigos = generarCodigos(construirArbol(frecuencias));
  const { datos: empaquetados, totalBits, bitsUltimoByte } = codificar(datos, codigos);
  return escribirHfa({
    nombre,
    tamanoOriginal: datos.length,
    sha256: await sha256(datos),
    frecuencias,
    datos: empaquetados,
    totalBits,
    bitsUltimoByte,
  });
}

// Recorre el arbol con cada bit (0 = izquierda, 1 = derecha). Al llegar a una hoja
// se emite el simbolo y se vuelve a la raiz. Se aplana el arbol a arreglos para ir rapido.
export function decodificar(datos, totalBits, raiz, tamanoOriginal) {
  if (!raiz) return new Uint8Array(0);
  if (raiz.esHoja()) return new Uint8Array(tamanoOriginal).fill(raiz.simbolo); // un solo simbolo
  const izq = [];
  const der = [];
  const sim = [];
  const aplanar = (nodo) => {
    const i = sim.length;
    sim.push(nodo.simbolo ?? -1);
    izq.push(-1);
    der.push(-1);
    if (!nodo.esHoja()) {
      izq[i] = aplanar(nodo.izquierdo);
      der[i] = aplanar(nodo.derecho);
    }
    return i;
  };
  aplanar(raiz);
  const salida = new Uint8Array(tamanoOriginal);
  let escritos = 0;
  let actual = 0;
  for (let pos = 0; pos < totalBits; pos++) {
    const bit = (datos[pos >> 3] >> (7 - (pos & 7))) & 1;
    actual = bit === 0 ? izq[actual] : der[actual];
    if (sim[actual] >= 0) {
      if (escritos === tamanoOriginal) break; // mas simbolos de los declarados: archivo alterado
      salida[escritos++] = sim[actual];
      actual = 0;
    }
  }
  return escritos === tamanoOriginal ? salida : salida.subarray(0, escritos);
}

// Regresa { datos, integridadOk, info }. integridadOk es true si el SHA-256 coincide.
export async function descomprimir(contenido) {
  const info = leerHfa(contenido);
  const raiz = construirArbol(info.frecuencias);
  const datos = decodificar(info.datos, info.totalBits, raiz, info.tamanoOriginal);
  const hash = await sha256(datos);
  const integridadOk = hash.length === info.sha256.length && hash.every((b, i) => b === info.sha256[i]);
  return { datos, integridadOk, info };
}

// El tamano comprimido es el del .hfa completo (encabezado + datos).
export function metricas(tamanoOriginal, tamanoComprimido, numSimbolos) {
  const ahorro = tamanoOriginal - tamanoComprimido;
  return {
    original: tamanoOriginal,
    comprimido: tamanoComprimido,
    ahorro,
    reduccion: tamanoOriginal ? (ahorro / tamanoOriginal) * 100 : 0,
    razon: tamanoComprimido ? tamanoOriginal / tamanoComprimido : 0,
    simbolos: numSimbolos,
  };
}

// 2225803 -> "2,225,803 B (2.12 MB)". 1 KB = 1024 B.
export function tamanoLegible(bytes) {
  const unidad = Math.abs(bytes) >= 1024 ** 2 ? `${(bytes / 1024 ** 2).toFixed(2)} MB` : `${(bytes / 1024).toFixed(2)} KB`;
  return `${bytes.toLocaleString("en-US")} B (${unidad})`;
}
