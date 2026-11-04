"""Bloque 4 — Empaquetado de bits.

Los códigos de Huffman son texto como "0110...". Para guardarlos de verdad
se juntan de 8 en 8 y cada grupo se convierte en un byte.
Si el total no es múltiplo de 8, al último byte se le agregan ceros
a la derecha (relleno), y se guarda cuántos bits de ese byte son válidos.
"""


def empaquetar(bits: str) -> tuple[bytes, int]:
    """Convierte "0100000101" en (b"\\x41\\x40", 2).

    Regresa los bytes y cuántos bits son válidos en el último byte (1–8, o 0 si no hay bits).
    """
    if not bits:
        return b"", 0
    bits_ultimo_byte = len(bits) % 8 or 8
    bits = bits + "0" * (8 - bits_ultimo_byte)  # relleno
    datos = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
    return datos, bits_ultimo_byte


def desempaquetar(datos: bytes, total_bits: int) -> str:
    """Operación inversa: bytes -> "0101...", quitando el relleno final."""
    bits = "".join(format(byte, "08b") for byte in datos)
    return bits[:total_bits]
