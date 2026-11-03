"""Bloque 1 — Frecuencias.

Primer paso de Huffman: contar cuántas veces aparece cada símbolo.
Un símbolo es un byte (0–255). Así cualquier .txt se recupera idéntico,
sin importar su codificación (UTF-8, Latin-1, etc.).
"""


def contar_frecuencias(datos: bytes) -> dict[int, int]:
    """Regresa {símbolo: frecuencia}, ordenado por símbolo.

    Ejemplo: b"abracadabra" -> {97: 5, 98: 2, 99: 1, 100: 1, 114: 2}
    """
    frecuencias = {}
    for byte in datos:
        frecuencias[byte] = frecuencias.get(byte, 0) + 1
    # Ordenar por símbolo hace que el árbol se construya siempre igual (ver B2).
    return dict(sorted(frecuencias.items()))
