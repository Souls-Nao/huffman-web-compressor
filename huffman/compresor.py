"""Bloque 6 — Compresor, descompresor, integridad y métricas.

Une los bloques anteriores:
    comprimir:    datos -> frecuencias (B1) -> árbol (B2) -> códigos (B3)
                  -> bits empaquetados (B4) -> archivo .hfa (B5)
    descomprimir: .hfa (B5) -> árbol (B2) -> bits (B4) -> datos -> verificar SHA-256
"""

import hashlib

from .arbol import construir_arbol
from .bits import desempaquetar, empaquetar
from .codigos import generar_codigos
from .formato import escribir_hfa, leer_hfa
from .frecuencias import contar_frecuencias


def comprimir(datos: bytes, nombre: str) -> bytes:
    """Comprime `datos` y regresa el contenido del archivo .hfa."""
    frecuencias = contar_frecuencias(datos)
    codigos = generar_codigos(construir_arbol(frecuencias))
    # Codificar: reemplazar cada byte por su código de Huffman.
    bits = "".join(codigos[byte] for byte in datos)
    empaquetados, bits_ultimo_byte = empaquetar(bits)
    sha256 = hashlib.sha256(datos).digest()  # huella del original para verificar después
    return escribir_hfa(nombre, len(datos), sha256, frecuencias, empaquetados, len(bits), bits_ultimo_byte)


def decodificar(bits: str, raiz, tamano_original: int) -> bytes:
    """Recorre el árbol con cada bit (0 = izquierda, 1 = derecha).
    Al llegar a una hoja se obtiene un símbolo y se vuelve a la raíz."""
    if raiz is None:  # archivo vacío
        return b""
    if raiz.es_hoja():  # un solo símbolo: cada bit "0" es ese símbolo
        return bytes([raiz.simbolo]) * tamano_original

    salida = bytearray()
    nodo = raiz
    for bit in bits:
        nodo = nodo.izquierdo if bit == "0" else nodo.derecho
        if nodo.es_hoja():
            salida.append(nodo.simbolo)
            nodo = raiz
    return bytes(salida)


def descomprimir(contenido: bytes) -> tuple[bytes, bool]:
    """Descomprime un .hfa. Regresa (datos recuperados, integridad_ok).

    integridad_ok es True si el SHA-256 de lo recuperado es igual al guardado.
    """
    info = leer_hfa(contenido)
    raiz = construir_arbol(info["frecuencias"])
    bits = desempaquetar(info["datos"], info["total_bits"])
    datos = decodificar(bits, raiz, info["tamano_original"])
    return datos, hashlib.sha256(datos).digest() == info["sha256"]


def metricas(tamano_original: int, tamano_comprimido: int, num_simbolos: int) -> dict:
    """Métricas de compresión. El tamaño comprimido es el del .hfa completo."""
    ahorro = tamano_original - tamano_comprimido
    return {
        "original": tamano_original,
        "comprimido": tamano_comprimido,
        "ahorro": ahorro,
        "reduccion": ahorro / tamano_original * 100 if tamano_original else 0.0,
        "razon": tamano_original / tamano_comprimido if tamano_comprimido else 0.0,
        "simbolos": num_simbolos,
    }


def tamano_legible(num_bytes: int) -> str:
    """2225803 -> "2,225,803 B (2.12 MB)". 1 KB = 1024 B."""
    valor = abs(num_bytes)
    if valor >= 1024 ** 2:
        unidad = f"{num_bytes / 1024 ** 2:.2f} MB"
    else:
        unidad = f"{num_bytes / 1024:.2f} KB"
    return f"{num_bytes:,} B ({unidad})"
