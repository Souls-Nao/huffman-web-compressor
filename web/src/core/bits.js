// Bloque 4 - Empaquetado de bits. Los codigos se juntan de 8 en 8; si el total no es
// multiplo de 8, al ultimo byte se le agregan ceros (relleno) y se guarda cuantos bits son validos.

// Version didactica: texto "0101..." -> bytes. Regresa { datos, bitsUltimoByte }.
export function empaquetar(bits) {
  if (!bits) return { datos: new Uint8Array(0), bitsUltimoByte: 0 };
  const bitsUltimoByte = bits.length % 8 || 8;
  const datos = new Uint8Array(Math.ceil(bits.length / 8));
  for (let i = 0; i < bits.length; i++) if (bits[i] === "1") datos[i >> 3] |= 0x80 >> (i & 7);
  return { datos, bitsUltimoByte };
}

// Operacion inversa: bytes -> "0101...", quitando el relleno final.
export function desempaquetar(datos, totalBits) {
  return leerBits(datos, 0, totalBits);
}

// Lee `cuantos` bits desde la posicion `desde` como texto (para la vista parcial del inspector).
export function leerBits(datos, desde, cuantos) {
  const hasta = Math.min(desde + cuantos, datos.length * 8);
  let texto = "";
  for (let i = desde; i < hasta; i++) texto += (datos[i >> 3] >> (7 - (i & 7))) & 1;
  return texto;
}

// Version eficiente que usa el compresor: escribe los bits directo en un Uint8Array
// sin construir una cadena gigante. Resultado identico a empaquetar(codigos concatenados).
export function codificar(datos, codigos) {
  const tabla = new Array(256);
  let totalBits = 0;
  for (const [simbolo, codigo] of codigos) tabla[simbolo] = codigo;
  for (let i = 0; i < datos.length; i++) totalBits += tabla[datos[i]].length;
  const salida = new Uint8Array(Math.ceil(totalBits / 8));
  let pos = 0;
  for (let i = 0; i < datos.length; i++) {
    const codigo = tabla[datos[i]];
    for (let j = 0; j < codigo.length; j++, pos++) {
      if (codigo.charCodeAt(j) === 49) salida[pos >> 3] |= 0x80 >> (pos & 7);
    }
  }
  return { datos: salida, totalBits, bitsUltimoByte: totalBits === 0 ? 0 : totalBits % 8 || 8 };
}
