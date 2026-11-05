"""Bloque 3 — Códigos de Huffman.

El código de un símbolo es el camino desde la raíz hasta su hoja:
ir a la izquierda agrega un "0" y a la derecha un "1".
Como los símbolos solo están en las hojas, ningún código es prefijo
de otro, y por eso se puede decodificar sin separadores.
"""

from .arbol import Nodo


def generar_codigos(raiz: Nodo | None) -> dict[int, str]:
    """Regresa {símbolo: código}, ordenado por símbolo. Ejemplo: {97: "0", 98: "110"}."""
    if raiz is None:
        return {}
    # Caso especial: un solo símbolo distinto. La raíz es hoja y no hay camino,
    # así que se le asigna "0" (1 bit por símbolo).
    if raiz.es_hoja():
        return {raiz.simbolo: "0"}

    codigos = {}

    def recorrer(nodo, codigo):
        if nodo.es_hoja():
            codigos[nodo.simbolo] = codigo
            return
        recorrer(nodo.izquierdo, codigo + "0")
        recorrer(nodo.derecho, codigo + "1")

    recorrer(raiz, "")
    return dict(sorted(codigos.items()))
