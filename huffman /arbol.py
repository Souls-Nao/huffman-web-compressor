"""Bloque 2 — Árbol de Huffman (técnica voraz).

Estrategia voraz: en cada paso se toman los DOS nodos de menor frecuencia
y se unen en un nodo padre cuya frecuencia es la suma. Se repite hasta
que queda un solo nodo: la raíz.

Para obtener siempre el mínimo rápido se usa una cola de prioridad (heapq).
"""

import heapq


class Nodo:
    """Nodo del árbol.

    - Hoja: tiene `simbolo` (un byte) y su frecuencia.
    - Nodo interno: no tiene símbolo; tiene hijo izquierdo (bit 0) y derecho (bit 1).
    """

    def __init__(self, frecuencia, simbolo=None, izquierdo=None, derecho=None):
        self.frecuencia = frecuencia
        self.simbolo = simbolo
        self.izquierdo = izquierdo
        self.derecho = derecho

    def es_hoja(self):
        return self.izquierdo is None and self.derecho is None


def construir_arbol(frecuencias: dict[int, int], pasos: list | None = None) -> Nodo | None:
    """Construye el árbol de Huffman y regresa la raíz (None si no hay símbolos).

    Cada elemento de la cola es (frecuencia, orden, nodo):
    - `frecuencia` decide quién sale primero (la menor).
    - `orden` desempata: entre frecuencias iguales sale el que llegó antes.
      Así el compresor y el descompresor construyen exactamente el mismo árbol.

    Si se pasa una lista en `pasos`, se guarda en ella cada unión como
    (izquierdo, derecho, padre). La interfaz la usa para mostrar la construcción paso a paso.
    """
    if not frecuencias:
        return None

    cola = []
    orden = 0
    # Las hojas entran ordenadas por símbolo.
    for simbolo in sorted(frecuencias):
        heapq.heappush(cola, (frecuencias[simbolo], orden, Nodo(frecuencias[simbolo], simbolo)))
        orden += 1

    # Paso voraz: unir los dos menores hasta que quede uno.
    while len(cola) > 1:
        frec_izq, _, izquierdo = heapq.heappop(cola)
        frec_der, _, derecho = heapq.heappop(cola)
        padre = Nodo(frec_izq + frec_der, izquierdo=izquierdo, derecho=derecho)
        heapq.heappush(cola, (padre.frecuencia, orden, padre))
        orden += 1
        if pasos is not None:
            pasos.append((izquierdo, derecho, padre))

    return cola[0][2]
