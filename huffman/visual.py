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



# ---------- Árbol y construcción paso a paso (los usa app.py) ----------

def simbolo_corto(simbolo: int) -> str:
    """Etiqueta de una sola celda para los nodos del árbol: 97 -> "a", 32 -> "␣", 195 -> "C3"."""
    if simbolo == 32:
        return "␣"
    if simbolo in (9, 10, 13):
        return {9: "\\t", 10: "\\n", 13: "\\r"}[simbolo]
    return chr(simbolo) if 33 <= simbolo <= 126 else f"{simbolo:02X}"


def etiqueta_nodo(nodo) -> str:
    """Hoja -> "a:5"; nodo interno -> "7"."""
    return f"{simbolo_corto(nodo.simbolo)}:{nodo.frecuencia}" if nodo.es_hoja() else str(nodo.frecuencia)


def pasos_construccion(frecuencias: dict[int, int]) -> dict:
    """Reproduce la cola de prioridad de construir_arbol, paso a paso.

    Regresa {"inicial": [nodos], "pasos": [{"izquierdo", "derecho", "padre", "cola"}]}, donde
    "cola" es el estado DESPUÉS de cada unión, ordenado como lo haría el heap
    (frecuencia, y a igualdad, el que entró antes). Usa construir_arbol(pasos=...), así que
    es el mismo árbol que se comprime, no una simulación aparte.
    """
    from .arbol import construir_arbol

    uniones = []
    raiz = construir_arbol(frecuencias, uniones)
    if raiz is None:
        return {"inicial": [], "pasos": [], "raiz": None}

    orden = {}  # id(nodo) -> orden de llegada a la cola (igual que en construir_arbol)
    hojas = []

    def recoger(nodo):
        if nodo.es_hoja():
            hojas.append(nodo)
        else:
            recoger(nodo.izquierdo)
            recoger(nodo.derecho)

    recoger(raiz)
    hojas.sort(key=lambda hoja: hoja.simbolo)
    for posicion, hoja in enumerate(hojas):
        orden[id(hoja)] = posicion

    cola = list(hojas)
    clave = lambda nodo: (nodo.frecuencia, orden[id(nodo)])
    cola.sort(key=clave)
    inicial = list(cola)
    pasos = []
    for k, (izquierdo, derecho, padre) in enumerate(uniones):
        orden[id(padre)] = len(hojas) + k
        cola = [n for n in cola if n is not izquierdo and n is not derecho] + [padre]
        cola.sort(key=clave)
        pasos.append({"izquierdo": izquierdo, "derecho": derecho, "padre": padre, "cola": list(cola)})
    return {"inicial": inicial, "pasos": pasos, "raiz": raiz}


def texto_paso(k: int, vista: dict) -> str:
    """Explicación en español del paso k (0 = cola inicial)."""
    inicial, pasos = vista["inicial"], vista["pasos"]
    total = len(pasos)
    if total == 0:
        return "Un solo símbolo distinto: el árbol es una hoja y no hay uniones que hacer."
    if k == 0:
        return (f"Cola inicial: {len(inicial)} hojas ordenadas por frecuencia. "
                "En cada paso salen los dos nodos de menor frecuencia.")
    paso = pasos[k - 1]
    izq, der, padre = paso["izquierdo"], paso["derecho"], paso["padre"]
    salen = f"salen {etiqueta_nodo(izq)} y {etiqueta_nodo(der)}"
    if k == total:
        return f"Paso {k} de {total}: {salen} y se unen en la raíz ({padre.frecuencia}). El árbol está completo."
    return (f"Paso {k} de {total}: {salen}; el nuevo nodo pesa "
            f"{izq.frecuencia} + {der.frecuencia} = {padre.frecuencia} y vuelve a la cola.")


def camino_a_simbolo(raiz, simbolo: int) -> tuple[set, set]:
    """(nodos, aristas) del camino raíz -> hoja del símbolo. Vacíos si no existe.

    Los nodos se identifican con id(nodo); una arista es (id(padre), id(hijo)).
    """
    if raiz is None:
        return set(), set()

    def buscar(nodo, ruta):
        ruta = ruta + [nodo]
        if nodo.es_hoja():
            return ruta if nodo.simbolo == simbolo else None
        return buscar(nodo.izquierdo, ruta) or buscar(nodo.derecho, ruta)

    ruta = buscar(raiz, [])
    if not ruta:
        return set(), set()
    ids = [id(n) for n in ruta]
    return set(ids), set(zip(ids, ids[1:]))


def arbol_dot(raices, camino=(set(), set()), nuevo=None) -> str:
    """Código DOT (Graphviz) de uno o varios árboles, listo para st.graphviz_chart.

    - raices: un nodo o una lista de nodos (el "bosque" de la cola de prioridad).
    - camino: (nodos, aristas) a resaltar, como los regresa camino_a_simbolo.
    - nuevo: nodo recién creado en la unión del paso actual (se pinta distinto).
    """
    if raices is None:
        raices = []
    elif not isinstance(raices, (list, tuple)):
        raices = [raices]
    nodos_camino, aristas_camino = camino
    lineas = [
        "digraph Huffman {",
        '  graph [rankdir=TB, nodesep=0.25, ranksep=0.45];',
        '  node [fontname="Helvetica", fontsize=11, style=filled];',
        '  edge [fontname="Helvetica", fontsize=10];',
    ]

    def dibujar(nodo):
        nombre = f"n{id(nodo)}"
        if nodo.es_hoja():
            texto = simbolo_corto(nodo.simbolo).replace("\\", "\\\\").replace('"', '\\"')
            etiqueta = f"{texto}\\n{nodo.frecuencia}"
            forma, color = "box", "#dff0d8"
        else:
            etiqueta = str(nodo.frecuencia)
            forma, color = "circle", "#e8eefc"
        if nuevo is not None and nodo is nuevo:
            color = "#fff3b0"
        if id(nodo) in nodos_camino:
            color = "#ffb3b3"
        lineas.append(f'  {nombre} [label="{etiqueta}", shape={forma}, fillcolor="{color}"];')
        if not nodo.es_hoja():
            for bit, hijo in (("0", nodo.izquierdo), ("1", nodo.derecho)):
                dibujar(hijo)
                resaltada = (id(nodo), id(hijo)) in aristas_camino
                estilo = ', color="#d9534f", penwidth=2.2, fontcolor="#d9534f"' if resaltada else ""
                lineas.append(f'  {nombre} -> n{id(hijo)} [label="{bit}"{estilo}];')

    for raiz in raices:
        dibujar(raiz)
    lineas.append("}")
    return "\n".join(lineas)


# ---------- Inspector: bits por símbolo y primeros bytes ----------

def tabla_bits(frecuencias: dict[int, int], codigos: dict[int, str]) -> list[dict]:
    """Como tabla(), pero con el costo en bits de cada símbolo frente a los 8 bits originales."""
    filas = []
    for fila in tabla(frecuencias, codigos):
        total = fila["Bits"] * fila["Frecuencia"]
        original = 8 * fila["Frecuencia"]
        filas.append({**fila, "Bits totales": total, "Bits originales": original, "Ahorro (bits)": original - total})
    return filas


def bytes_muestra(datos: bytes, total_bits: int, cantidad: int = 12) -> list[dict]:
    """Los primeros bytes comprimidos en binario y hexadecimal (el último respeta total_bits)."""
    filas = []
    for i in range(min(cantidad, (total_bits + 7) // 8, len(datos))):
        validos = min(8, total_bits - i * 8)
        filas.append({"Byte": i, "Binario": format(datos[i], "08b")[:validos], "Hex": f"{datos[i]:02X}"})
    return filas


def segmentar_bits(datos: bytes, total_bits: int, raiz, maximo: int = 24) -> list[dict]:
    """Recorre el árbol sobre los primeros bits y separa las palabras de código.

    [{"Bits": "110", "Símbolo": "b", "Byte": 98}, ...] (hasta `maximo` símbolos).
    """
    if raiz is None:
        return []
    if raiz.es_hoja():  # un solo símbolo: cada bit "0" es ese símbolo
        return [{"Bits": "0", "Símbolo": simbolo_corto(raiz.simbolo), "Byte": raiz.simbolo}
                for _ in range(min(maximo, total_bits))]
    salida, nodo, palabra = [], raiz, ""
    for i in range(min(total_bits, len(datos) * 8)):
        if len(salida) >= maximo:
            break
        bit = (datos[i >> 3] >> (7 - (i & 7))) & 1
        palabra += str(bit)
        nodo = nodo.izquierdo if bit == 0 else nodo.derecho
        if nodo.es_hoja():
            salida.append({"Bits": palabra, "Símbolo": simbolo_corto(nodo.simbolo), "Byte": nodo.simbolo})
            nodo, palabra = raiz, ""
    return salida
