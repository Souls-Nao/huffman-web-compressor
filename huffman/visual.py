"""Bloque 10 — Visualización: tablas.

Solo prepara los datos para mostrarlos; la interfaz (app.py) los dibuja.
"""

NOMBRES_ESPECIALES = {9: "\\t (tab)", 10: "\\n (salto)", 13: "\\r (retorno)", 32: "␣ (espacio)"}


def simbolo_legible(simbolo: int) -> str:
    """Byte -> texto para mostrar: 97 -> "a", 10 -> "\\n (salto)", 195 -> "0xC3"."""
    if simbolo in NOMBRES_ESPECIALES:
        return NOMBRES_ESPECIALES[simbolo]
    if 33 <= simbolo <= 126:  # caracteres ASCII imprimibles
        return chr(simbolo)
    return f"0x{simbolo:02X}"


def tabla(frecuencias: dict[int, int], codigos: dict[int, str] | None = None) -> list[dict]:
    """Filas para mostrar: símbolo, byte, frecuencia, % y, si se dan, código y su largo.
    Ordenadas de mayor a menor frecuencia."""
    total = sum(frecuencias.values())
    filas = []
    for simbolo, frecuencia in sorted(frecuencias.items(), key=lambda par: -par[1]):
        fila = {
            "Símbolo": simbolo_legible(simbolo),
            "Byte": simbolo,
            "Frecuencia": frecuencia,
            "%": round(frecuencia / total * 100, 3),
        }
        if codigos is not None:
            fila["Código"] = codigos[simbolo]
            fila["Bits"] = len(codigos[simbolo])
        filas.append(fila)
    return filas

