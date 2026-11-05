"""Bloque 5 — Formato de archivo propio .hfa (versión 1).

Estructura (enteros sin signo, little-endian). Detalle en docs/FORMATO.md:

    firma "HUFA" (4 B) | versión (1 B) | tamaño original (8 B) | total de bits (8 B)
    | bits válidos del último byte (1 B) | SHA-256 del original (32 B)
    | largo del nombre N (2 B) | nombre (N B)
    | número de símbolos S (2 B) | tabla: S × [símbolo (1 B) + frecuencia (4 B)]
    | datos comprimidos (resto)

Se guarda la tabla de frecuencias (no el árbol): con ella el descompresor
vuelve a construir el mismo árbol (B2). El texto original NO se guarda.
"""

import struct

FIRMA = b"HUFA"
VERSION = 1
EXTENSION = ".hfa"

# Campos fijos: firma, versión, tamaño original, total bits, bits último byte, sha256, largo nombre.
CAMPOS_FIJOS = "<4sBQQB32sH"
TAMANO_FIJO = struct.calcsize(CAMPOS_FIJOS)  # 56 bytes


def escribir_hfa(nombre, tamano_original, sha256, frecuencias, datos, total_bits, bits_ultimo_byte) -> bytes:
    """Arma el contenido completo del archivo .hfa."""
    nombre_bytes = nombre.encode("utf-8")
    partes = [
        struct.pack(CAMPOS_FIJOS, FIRMA, VERSION, tamano_original, total_bits,
                    bits_ultimo_byte, sha256, len(nombre_bytes)),
        nombre_bytes,
        struct.pack("<H", len(frecuencias)),
    ]
    for simbolo, frecuencia in frecuencias.items():
        partes.append(struct.pack("<BI", simbolo, frecuencia))
    partes.append(datos)
    return b"".join(partes)


def leer_hfa(contenido: bytes) -> dict:
    """Lee un .hfa y regresa sus campos. Lanza ValueError si no es válido."""
    if contenido[:4] != FIRMA:
        raise ValueError("No es un archivo .hfa válido (firma incorrecta).")
    try:
        _, version, tamano_original, total_bits, bits_ultimo_byte, sha256, largo_nombre = \
            struct.unpack_from(CAMPOS_FIJOS, contenido, 0)
        if version != VERSION:
            raise ValueError(f"Versión {version} no soportada (se esperaba {VERSION}).")
        pos = TAMANO_FIJO
        nombre = contenido[pos:pos + largo_nombre].decode("utf-8")
        pos += largo_nombre
        (num_simbolos,) = struct.unpack_from("<H", contenido, pos)
        pos += 2
        frecuencias = {}
        for _ in range(num_simbolos):
            simbolo, frecuencia = struct.unpack_from("<BI", contenido, pos)
            frecuencias[simbolo] = frecuencia
            pos += 5
    except (struct.error, UnicodeDecodeError):
        raise ValueError("El archivo .hfa está incompleto o dañado.")

    return {
        "version": version,
        "nombre_original": nombre,
        "tamano_original": tamano_original,
        "total_bits": total_bits,
        "bits_ultimo_byte": bits_ultimo_byte,
        "sha256": sha256,
        "frecuencias": frecuencias,
        "tamano_encabezado": pos,
        "datos": contenido[pos:],
    }
