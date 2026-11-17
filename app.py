"""Bloque 7 — Interfaz web (Streamlit).

Ejecutar:  streamlit run app.py

Flujo:  SUBIR TXT / BUSCAR LIBRO / ESCRIBIR TEXTO → ANALIZAR → CONSTRUIR HUFFMAN (paso a paso)
        → CÓDIGOS Y ÁRBOL → COMPRIMIR → INSPECCIONAR → DESCOMPRIMIR → VERIFICAR → DESCARGAR

Es la misma funcionalidad y el mismo aspecto que la versión web en JavaScript (web/): cabecera con
barra de flujo, fichas de la cola de prioridad, bits coloreados, barra comparativa e inspector.
El HTML y el CSS viven en huffman/ui.py; los datos del inspector en huffman/inspector.py.

Gutenberg y proxy: si gutenberg.org no responde desde el servidor (mantenimiento o IP
bloqueada), define GUTENBERG_PROXY_URL y/o GUTENBERG_HTTP_PROXY en los Secrets de Streamlit
o como variables de entorno (ver .streamlit/secrets.toml.example y huffman/gutenberg.py).
"""

import hashlib
import time
from pathlib import Path

import streamlit as st

from huffman import gutenberg, ui
from huffman.arbol import construir_arbol
from huffman.codigos import generar_codigos
from huffman.compresor import comprimir, descomprimir, metricas, tamano_legible
from huffman.formato import EXTENSION, tamano_hfa
from huffman.frecuencias import contar_frecuencias
from huffman.inspector import vista_desde_hfa, vista_desde_texto
from huffman.visual import (arbol_dot, bytes_muestra, camino_a_simbolo, ids_subarbol, pasos_construccion,
                            segmentar_bits, simbolo_corto, tabla, tabla_bits, texto_paso)

MAX_BYTES = 20 * 1024 * 1024   # la versión con bits en texto recomienda <= ~20 MB
MAX_RESULTADOS = 25            # igual que la versión JS
MAX_HOJAS_ARBOL = 64           # por encima, el árbol se dibuja solo si la persona lo pide
ORIGEN = {"archivo": "archivo local", "texto": "texto escrito", "gutenberg": "Project Gutenberg"}


# ---------- Configuración del proxy de Gutenberg ----------

def configurar_gutenberg():
    """Lee los Secrets de Streamlit (si existen) y se los pasa a huffman.gutenberg.

    Sin secrets.toml, st.secrets lanza un error: se ignora y se usan las variables de entorno.
    """
    try:
        proxy_url = st.secrets.get("GUTENBERG_PROXY_URL", "")
        proxy_http = st.secrets.get("GUTENBERG_HTTP_PROXY", "")
    except Exception:
        return
    if proxy_url or proxy_http:
        gutenberg.configurar(proxy_url=str(proxy_url), proxy_http=str(proxy_http))


# ---------- Utilidades de la interfaz ----------

@st.cache_data(show_spinner=False, max_entries=8)
def frecuencias_de(datos: bytes) -> dict:
    """Cuenta los bytes una sola vez por texto (Streamlit vuelve a ejecutar todo en cada clic)."""
    return contar_frecuencias(datos)


def html(contenido: str):
    st.markdown(contenido, unsafe_allow_html=True)


def encabezado(numero, titulo: str):
    html(ui.encabezado_seccion(numero, titulo))


def fijar_entrada(entrada: dict | None):
    """Cambia el texto de trabajo y descarta lo que dependía del anterior."""
    if entrada:
        st.session_state["entrada"] = entrada
    else:
        st.session_state.pop("entrada", None)
    for clave in ("comprimido", "recuperado", "progreso", "paso"):
        st.session_state.pop(clave, None)


def marcar(clave: str):
    """Anota un paso del flujo como hecho (lo dibuja la cabecera al final de la página)."""
    st.session_state.setdefault("progreso", {})[clave] = True


def mostrar_metricas(m: dict):
    """Tarjetas con las métricas de compresión."""
    c1, c2, c3 = st.columns(3)
    c1.metric("Original", tamano_legible(m["original"]))
    c2.metric("Comprimido", tamano_legible(m["comprimido"]), help="Incluye el encabezado del .hfa.")
    c3.metric("Ahorro", tamano_legible(m["ahorro"]))
    c4, c5, c6 = st.columns(3)
    c4.metric("Reducción", f"{m['reduccion']:.2f} %")
    c5.metric("Razón de compresión", f"{m['razon']:.2f} : 1")
    c6.metric("Símbolos diferentes", m["simbolos"])


def configuracion_tabla_bits():
    """Columnas de la tabla de códigos: 'Bits' como barra sobre 8, como en la versión JS."""
    return {
        "Bits": st.column_config.ProgressColumn("Bits por carácter", min_value=0, max_value=8, format="%d / 8"),
        "Bits originales": st.column_config.NumberColumn("Sin comprimir (bits)"),
    }


def dibujar_arbol(dot: str, hojas: int, clave: str):
    """Dibuja el árbol; si tiene muchas hojas pide confirmación (se vuelve lento y ancho)."""
    if hojas > MAX_HOJAS_ARBOL and not st.checkbox(
            f"Dibujar el árbol completo ({hojas} hojas, puede tardar y verse muy ancho)", key=clave):
        st.caption("Usa la tabla de códigos o elige un símbolo para ver su camino.")
        return
    st.graphviz_chart(dot)


# ---------- Pestaña COMPRIMIR ----------

def panel_archivo():
    """Subir un .txt local."""
    archivo = st.file_uploader("Archivo de texto", type=["txt"], key=f"subida_txt_{st.session_state.get('subida_n', 0)}")
    if archivo:
        datos = archivo.getvalue()
        visto = (archivo.name, len(datos))
        # Solo se toma el archivo cuando cambia: si no, cada recarga pisaría un libro o texto elegido después.
        if st.session_state.get("archivo_visto") != visto:
            st.session_state["archivo_visto"] = visto
            fijar_entrada({"nombre": archivo.name, "datos": datos, "origen": "archivo"})
            st.rerun()


def panel_texto():
    """Escribir o pegar un texto corto."""
    texto = st.text_area("Texto a comprimir", key="texto_escrito", height=120,
                         placeholder="Escribe o pega un texto, por ejemplo: abracadabra")
    c1, c2, c3 = st.columns([2, 1, 1])
    if c1.button("Usar este texto", type="primary", disabled=not texto):
        fijar_entrada({"nombre": "texto.txt", "datos": texto.encode("utf-8"), "origen": "texto"})
        st.rerun()
    if c2.button("Ejemplo: abracadabra"):
        fijar_entrada({"nombre": "texto.txt", "datos": b"abracadabra", "origen": "texto"})
        st.rerun()
    if c3.button("Ejemplo con acentos"):
        fijar_entrada({"nombre": "texto.txt", "datos": "¡Hola, ñandú! Adiós, canción.".encode("utf-8"), "origen": "texto"})
        st.rerun()
    st.caption("Con textos muy cortos el .hfa pesa más que el original: el encabezado ocupa más que el ahorro.")


def panel_gutenberg():
    """Buscar en Project Gutenberg (título, autor o tema) y usar un libro."""
    st.caption(f"Conexión: {gutenberg.describir_conexion()}.")
    with st.form("buscador_gutenberg"):
        c1, c2 = st.columns([3, 1])
        consulta = c1.text_input("Título, autor o tema", placeholder="quijote, Mary Shelley, pirates…")
        campo = c2.selectbox("Buscar por", ["titulo", "autor", "tema"],
                             format_func=lambda c: {"titulo": "Título", "autor": "Autor", "tema": "Tema"}[c])
        buscar = st.form_submit_button("Buscar", type="primary")

    if buscar:
        try:
            with st.spinner("Buscando…"):
                libros = gutenberg.buscar(consulta, campo)[:MAX_RESULTADOS]
            st.session_state["libros"] = libros
            st.session_state["sin_resultados"] = not libros
            st.session_state.pop("error_gutenberg", None)
        except (ValueError, ConnectionError) as error:
            st.session_state["libros"] = []
            st.session_state["sin_resultados"] = False
            st.session_state["error_gutenberg"] = str(error)

    if st.session_state.get("error_gutenberg"):
        st.error(st.session_state["error_gutenberg"])
        st.info("Si Gutenberg está en mantenimiento, sube un .txt o escribe un texto en las otras pestañas. "
                "Para rodear bloqueos configura GUTENBERG_PROXY_URL (ver README).")
    elif st.session_state.get("sin_resultados"):
        st.warning("Sin resultados. Prueba con otro título, autor o tema.")

    libros = st.session_state.get("libros", [])
    if libros:
        st.caption(f"Se muestran los primeros {MAX_RESULTADOS} resultados del catálogo oficial.")
    for libro in libros:
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"**{libro['titulo']}**  \n{libro['autor'] or 'Autor desconocido'} · #{libro['id']}")
            if not c2.button("Usar este libro", key=f"usar_{libro['id']}"):
                continue
            try:
                with st.spinner(f"Descargando «{libro['titulo']}»…"):
                    datos = gutenberg.descargar(libro["id"])
            except (ValueError, ConnectionError) as error:
                st.error(str(error))
                continue
            if len(datos) > MAX_BYTES:
                st.error("El libro supera el límite de 20 MB.")
                continue
            fijar_entrada({"nombre": f"pg{libro['id']}.txt", "datos": datos, "origen": "gutenberg", "libro": libro})
            st.rerun()


def seccion_entrada():
    """1. Entrada: archivo local, libro de Gutenberg o texto escrito. Regresa (nombre, datos) o None."""
    encabezado(1, "Entrada")
    tab_archivo, tab_gutenberg, tab_texto = st.tabs(["Subir .txt", "Buscar en Project Gutenberg", "Escribir un texto corto"])
    with tab_archivo:
        panel_archivo()
    with tab_gutenberg:
        panel_gutenberg()
    with tab_texto:
        panel_texto()

    entrada = st.session_state.get("entrada")
    if not entrada:
        return None
    libro = entrada.get("libro")
    c1, c2 = st.columns([6, 1])
    detalle = [libro["autor"] if libro else "", entrada["nombre"], tamano_legible(len(entrada["datos"])),
               ORIGEN[entrada["origen"]]]
    c1.success(f"**{libro['titulo'] if libro else entrada['nombre']}** · " + " · ".join(d for d in detalle if d))
    if c2.button("Quitar"):
        fijar_entrada(None)
        st.session_state.pop("archivo_visto", None)
        # Clave nueva = el cargador de archivos queda vacío (si no, volvería a tomar el mismo .txt).
        st.session_state["subida_n"] = st.session_state.get("subida_n", 0) + 1
        st.rerun()
    return entrada["nombre"], entrada["datos"]


def seccion_analisis(datos: bytes, frecuencias: dict):
    """2. Analizar: tabla de frecuencias."""
    encabezado(2, "Analizar: frecuencias")
    st.write(f"**{tamano_legible(len(datos))}** · **{len(frecuencias)}** símbolos diferentes (cada símbolo es un byte)")
    st.dataframe(tabla(frecuencias), hide_index=True, height=300)


def ir_a_paso(k: int):
    st.session_state["paso"] = k


def seccion_pasos(frecuencias: dict):
    """3. Construcción paso a paso con la cola de prioridad."""
    encabezado(3, "Construcción paso a paso (cola de prioridad)")
    st.caption("Estrategia voraz: en cada paso se unen los dos nodos de menor frecuencia. "
               "Con n símbolos hay n − 1 uniones y cada una cuesta O(log n).")
    vista = pasos_construccion(frecuencias)
    total = len(vista["pasos"])
    if total == 0:
        st.info(texto_paso(0, vista))
        return

    st.session_state["paso"] = min(max(st.session_state.get("paso", 0), 0), total)
    k = st.session_state["paso"]
    b1, b2, b3, b4, resto = st.columns([1, 1, 1, 1, 8])
    b1.button("⏮", on_click=ir_a_paso, args=(0,), disabled=k == 0, help="Cola inicial")
    b2.button("◀", on_click=ir_a_paso, args=(k - 1,), disabled=k == 0, help="Paso anterior")
    b3.button("▶", on_click=ir_a_paso, args=(k + 1,), disabled=k == total, help="Paso siguiente")
    b4.button("⏭", on_click=ir_a_paso, args=(total,), disabled=k == total, help="Árbol completo")
    with resto:
        st.slider("Paso de la construcción", 0, total, key="paso", help="0 = cola inicial; el último paso deja el árbol completo.")
    k = st.session_state["paso"]

    html(ui.texto_del_paso(texto_paso(k, vista)))
    if k == 0:
        html(ui.fichas_cola("Cola de prioridad", vista["inicial"],
                            nota="El primero de la cola es el de menor frecuencia."))
        nuevo = None
        cola = vista["inicial"]
    else:
        paso = vista["pasos"][k - 1]
        antes = vista["inicial"] if k == 1 else vista["pasos"][k - 2]["cola"]
        html(ui.fichas_cola("Antes del paso (cola ordenada de menor a mayor)", antes,
                            {id(paso["izquierdo"]): "izquierdo", id(paso["derecho"]): "derecho"},
                            nota="Salen siempre los dos primeros."))
        html(ui.fichas_cola("Después del paso", paso["cola"], {id(paso["padre"]): "nuevo"}))
        nuevo = paso["padre"]
        cola = paso["cola"]

    st.write("**Bosque en este paso**")
    if len(cola) <= MAX_HOJAS_ARBOL:
        st.graphviz_chart(arbol_dot(cola, nuevo=nuevo))
    else:
        st.caption("El bosque es muy grande para dibujarlo; avanza con el deslizador para ver cómo se reduce.")


def seccion_huffman(frecuencias: dict, raiz, codigos: dict):
    """4. Códigos de Huffman y árbol, con el camino de bits de un símbolo."""
    encabezado(4, "Códigos y árbol de Huffman")
    st.caption("Los símbolos más frecuentes reciben los códigos más cortos.")
    filas = tabla_bits(frecuencias, codigos)
    st.dataframe(filas, hide_index=True, height=300, column_config=configuracion_tabla_bits())

    st.write("**Frecuencia contra longitud del código**")
    st.scatter_chart({"Frecuencia": [f["Frecuencia"] for f in filas],
                      "Bits por carácter": [f["Bits"] for f in filas]},
                     x="Frecuencia", y="Bits por carácter")
    st.caption("Cada punto es un símbolo: los más frecuentes (a la derecha) quedan con códigos más cortos (abajo).")

    simbolos = sorted(frecuencias, key=lambda s: (-frecuencias[s], s))
    elegido = st.selectbox("Resalta el camino de un símbolo", simbolos,
                           format_func=lambda s: f"{simbolo_corto(s)}  (byte {s}) → {codigos[s]}")
    html(f"Camino de <b>{ui.e(simbolo_corto(elegido))}</b>: " + (
        " → ".join(f"{'izquierda' if b == '0' else 'derecha'} ({ui.bits_html(b)})" for b in codigos[elegido])
        if not raiz.es_hoja() else "es la única hoja: se le asigna el código " + ui.bits_html("0"))
         + f" · código completo {ui.bits_html(codigos[elegido])}")
    dot = arbol_dot(raiz, camino_a_simbolo(raiz, elegido))
    dibujar_arbol(dot, len(frecuencias), "arbol_completo")
    st.download_button("Descargar el árbol (.dot)", arbol_dot(raiz), file_name="arbol_huffman.dot",
                       mime="text/vnd.graphviz", help="Código Graphviz del árbol completo: ábrelo en cualquier visor DOT.")


def seccion_comprimir(nombre: str, datos: bytes, frecuencias: dict, total_bits: int):
    """5. Comprimir y medir: genera el .hfa, muestra métricas y permite descargarlo."""
    encabezado(5, "Comprimir y medir")
    clave = (nombre, datos)  # identifica la entrada actual
    estimado = tamano_hfa(nombre, len(frecuencias), total_bits)
    st.write(f"Tamaño final estimado del `{EXTENSION}`: **{tamano_legible(estimado)}** (encabezado + bits de Huffman).")
    if st.button("Comprimir", type="primary"):
        inicio = time.perf_counter()
        hfa = comprimir(datos, nombre)
        st.session_state["comprimido"] = (clave, hfa, (time.perf_counter() - inicio) * 1000)
    guardado = st.session_state.get("comprimido")
    if not guardado or guardado[0] != clave:
        return
    _, hfa, ms = guardado
    m = metricas(len(datos), len(hfa), len(frecuencias))
    mostrar_metricas(m)
    proporcion = min(100.0, m["comprimido"] / max(1, m["original"]) * 100)
    html(ui.comparacion(m["original"], m["comprimido"], "Original", f"{proporcion:.1f} %"))
    st.caption(f"Comprimido en {ms:.1f} ms.")
    nombre_hfa = Path(nombre).stem + EXTENSION
    st.download_button(f"Descargar {nombre_hfa}", hfa, file_name=nombre_hfa, mime="application/octet-stream")
    if m["reduccion"] < 0:
        st.warning("El .hfa pesa más que el original: con textos muy cortos el encabezado ocupa más que el ahorro.")
    st.info("Siguiente paso: abre la pestaña **Inspector / Descomprimir**; ahí puedes usar este archivo "
            "directamente o subir otro .hfa.")


# ---------- Pestaña INSPECTOR / DESCOMPRIMIR ----------

def obtener_hfa():
    """Origen del .hfa: el recién comprimido o uno subido. Regresa (nombre_archivo, bytes) o None."""
    guardado = st.session_state.get("comprimido")
    if guardado:
        (nombre, _), hfa, _ = guardado
        nombre_hfa = Path(nombre).stem + EXTENSION
        if st.toggle(f"Usar {nombre_hfa} recién comprimido", value=True, key="usar_reciente"):
            return nombre_hfa, hfa
    archivo = st.file_uploader(f"Archivo comprimido {EXTENSION}", type=[EXTENSION[1:]])
    if not archivo:
        st.caption(f"Sube un {EXTENSION}: el inspector muestra su estructura sin necesitar el .txt original. "
                   "El texto solo aparece después de pulsar DESCOMPRIMIR.")
    return (archivo.name, archivo.getvalue()) if archivo else None


def panel_inspector(vista: dict, hfa: bytes | None):
    """Metadatos, tamaños, bits por carácter, árbol y primeros bits. `hfa` = bytes si viene de un archivo."""
    if vista["metadatos"]:
        st.subheader("Metadatos del encabezado")
        st.table({"Campo": [c for c, _ in vista["metadatos"]], "Valor": [v for _, v in vista["metadatos"]]})

    m = vista["metricas"]
    mostrar_metricas(m)
    if hfa is None:
        st.caption("Tamaño final calculado sin generar el archivo.")
    proporcion = min(100.0, vista["tamano_final"] / max(1, vista["tamano_original"]) * 100)
    html(ui.comparacion(vista["tamano_original"], vista["tamano_final"],
                        f"Original · {vista['tamano_original']:,} B",
                        f"Final · {vista['tamano_final']:,} B ({proporcion:.1f} %)"))

    st.subheader("Tabla de frecuencias y bits por carácter")
    st.caption("Cada carácter ocupa 8 bits sin comprimir; con Huffman ocupa solo la longitud de su código. "
               f"En total: {vista['total_bits']:,} bits.")
    st.dataframe(tabla_bits(vista["frecuencias"], vista["codigos"]), hide_index=True, height=300,
                 column_config=configuracion_tabla_bits())

    with st.expander("Árbol de Huffman reconstruido", expanded=False):
        dibujar_arbol(arbol_dot(vista["raiz"]), len(vista["frecuencias"]), f"arbol_inspector_{'hfa' if hfa else 'texto'}")

    datos_muestra, bits_muestra = vista["muestra"]
    st.subheader("Primeros bits")
    html(ui.bytes_html(bytes_muestra(datos_muestra, bits_muestra)))
    st.caption("Los mismos bits separados por palabra de código:")
    html(ui.palabras_html(segmentar_bits(datos_muestra, bits_muestra, vista["raiz"])))


def bloque_descomprimir(nombre_archivo: str, contenido: bytes, nombre_original: str):
    """7. Descomprimir y verificar (SHA-256)."""
    st.subheader("7. Descomprimir y verificar")
    st.caption("El texto original solo aparece después de este botón.")
    clave = (nombre_archivo, contenido)  # identifica el .hfa actual
    if st.button("DESCOMPRIMIR", type="primary"):
        st.session_state["recuperado"] = (clave, descomprimir(contenido))
        marcar("descomprimido")
        if st.session_state["recuperado"][1][1]:
            marcar("verificado")
    guardado = st.session_state.get("recuperado")
    if not guardado or guardado[0] != clave:
        return
    datos, integridad_ok = guardado[1]
    if integridad_ok:
        st.success("Integridad verificada: el SHA-256 del texto recuperado es idéntico al original.")
    else:
        st.error("Integridad fallida: el texto recuperado NO coincide con el original.")
    st.caption(f"SHA-256 recuperado: {hashlib.sha256(datos).hexdigest()}")
    st.text_area("Texto recuperado", datos[:5000].decode("utf-8", errors="replace"), height=250)
    if len(datos) > 5000:
        st.caption("Vista previa de los primeros 5,000 bytes.")
    st.download_button("Descargar texto recuperado (.txt)", datos,
                       file_name="recuperado_" + nombre_original, mime="text/plain")


def seccion_inspector():
    """6. Inspector: del texto actual o de un .hfa (sin el original); este último permite DESCOMPRIMIR."""
    encabezado(6, "Inspector del archivo comprimido")
    fuente = st.radio("Qué inspeccionar", ["Texto actual", f"Archivo {EXTENSION}"], horizontal=True,
                      label_visibility="collapsed")

    if fuente == "Texto actual":
        entrada = st.session_state.get("entrada")
        if not entrada or not entrada["datos"]:
            st.info("Carga un texto en el paso 1 para inspeccionar su tabla de frecuencias, códigos y tamaño final.")
            return
        frecuencias = frecuencias_de(entrada["datos"])
        panel_inspector(vista_desde_texto(entrada["nombre"], entrada["datos"], frecuencias), None)
        st.caption(f"Para descomprimir y verificar, usa la opción «Archivo {EXTENSION}».")
        return

    origen = obtener_hfa()
    if not origen:
        return
    nombre_archivo, contenido = origen
    try:
        vista = vista_desde_hfa(contenido, nombre_archivo)
    except ValueError as error:
        st.error(str(error))
        return
    marcar("inspeccionado")
    # Todo sale del .hfa: la tabla de frecuencias reconstruye el mismo árbol, sin el texto original.
    panel_inspector(vista, contenido)
    bloque_descomprimir(nombre_archivo, contenido, vista["nombre"])


# ---------- Página ----------

st.set_page_config(page_title="Huffman Web Compressor", layout="wide")
configurar_gutenberg()
html(ui.estilos())
marcador_flujo = st.empty()  # la cabecera se dibuja al final, cuando ya se sabe qué pasos van hechos

tab_comprimir, tab_inspector = st.tabs(["Comprimir", "Inspector / Descomprimir"])
frecuencias = {}
with tab_comprimir:
    entrada = seccion_entrada()
    if entrada:
        nombre, datos = entrada
        frecuencias = frecuencias_de(datos)
        if frecuencias:
            seccion_analisis(datos, frecuencias)
            raiz = construir_arbol(frecuencias)
            codigos = generar_codigos(raiz)
            total_bits = sum(frecuencias[s] * len(codigos[s]) for s in frecuencias)
            seccion_pasos(frecuencias)
            seccion_huffman(frecuencias, raiz, codigos)
            seccion_comprimir(nombre, datos, frecuencias, total_bits)
        else:
            st.warning("El archivo está vacío.")
with tab_inspector:
    seccion_inspector()
html(ui.pie())

guardado = st.session_state.get("comprimido")
actual = st.session_state.get("entrada")
progreso = st.session_state.get("progreso", {})
marcador_flujo.markdown(ui.cabecera({
    "entrada": bool(actual),
    "analizar": bool(frecuencias),
    "huffman": bool(frecuencias),
    "comprimir": bool(guardado and actual and guardado[0] == (actual["nombre"], actual["datos"])),
    "inspeccionar": bool(progreso.get("inspeccionado")),
    "descomprimir": bool(progreso.get("descomprimido")),
    "verificar": bool(progreso.get("verificado")),
}), unsafe_allow_html=True)
