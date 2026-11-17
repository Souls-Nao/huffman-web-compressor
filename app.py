"""Bloque 7 — Interfaz web (Streamlit).

Ejecutar:  streamlit run app.py

Flujo:  SUBIR TXT / BUSCAR LIBRO / ESCRIBIR TEXTO → ANALIZAR → CONSTRUIR HUFFMAN (paso a paso)
        → CÓDIGOS Y ÁRBOL → COMPRIMIR → INSPECCIONAR → DESCOMPRIMIR → VERIFICAR → DESCARGAR

Es la misma funcionalidad que la versión web en JavaScript (web/), para que ambas
aplicaciones coincidan. Cada sección de la página es una función. La parte de abajo
del archivo decide el orden en que se muestran.

Gutenberg y proxy: si gutenberg.org no responde desde el servidor (mantenimiento o IP
bloqueada), define GUTENBERG_PROXY_URL y/o GUTENBERG_HTTP_PROXY en los Secrets de Streamlit
o como variables de entorno (ver .streamlit/secrets.toml.example y huffman/gutenberg.py).
"""

from pathlib import Path

import streamlit as st

from huffman import gutenberg
from huffman.arbol import construir_arbol
from huffman.codigos import generar_codigos
from huffman.compresor import comprimir, descomprimir, metricas, tamano_legible
from huffman.formato import EXTENSION, FIRMA, leer_hfa
from huffman.frecuencias import contar_frecuencias
from huffman.visual import (arbol_dot, bytes_muestra, camino_a_simbolo, pasos_construccion,
                            segmentar_bits, simbolo_corto, tabla, tabla_bits, texto_paso,
                            etiqueta_nodo)

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

def mostrar_metricas(m: dict):
    """Tarjetas con las métricas de compresión."""
    c1, c2, c3 = st.columns(3)
    c1.metric("Original", tamano_legible(m["original"]))
    c2.metric("Comprimido", tamano_legible(m["comprimido"]))
    c3.metric("Ahorro", tamano_legible(m["ahorro"]))
    c4, c5, c6 = st.columns(3)
    c4.metric("Reducción", f"{m['reduccion']:.2f} %")
    c5.metric("Razón de compresión", f"{m['razon']:.2f} : 1")
    c6.metric("Símbolos diferentes", m["simbolos"])


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
            st.session_state["entrada"] = {"nombre": archivo.name, "datos": datos, "origen": "archivo"}
            st.rerun()


def panel_texto():
    """Escribir o pegar un texto corto."""
    texto = st.text_area("Texto a comprimir", key="texto_escrito", height=120,
                         placeholder="Escribe o pega un texto, por ejemplo: abracadabra")
    c1, c2, c3 = st.columns([2, 1, 1])
    if c1.button("Usar este texto", type="primary", disabled=not texto):
        st.session_state["entrada"] = {"nombre": "texto.txt", "datos": texto.encode("utf-8"), "origen": "texto"}
        st.rerun()
    if c2.button("Ejemplo: abracadabra"):
        st.session_state["entrada"] = {"nombre": "texto.txt", "datos": b"abracadabra", "origen": "texto"}
        st.rerun()
    if c3.button("Ejemplo con acentos"):
        st.session_state["entrada"] = {"nombre": "texto.txt", "datos": "¡Hola, ñandú! Adiós, canción.".encode("utf-8"),
                                       "origen": "texto"}
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
        c1, c2 = st.columns([5, 1])
        c1.markdown(f"**{libro['titulo']}**  \n{libro['autor'] or 'Autor desconocido'} · #{libro['id']}")
        if c2.button("Usar este libro", key=f"usar_{libro['id']}"):
            try:
                with st.spinner(f"Descargando «{libro['titulo']}»…"):
                    datos = gutenberg.descargar(libro["id"])
            except (ValueError, ConnectionError) as error:
                st.error(str(error))
                continue
            if len(datos) > MAX_BYTES:
                st.error("El libro supera el límite de 20 MB.")
                continue
            st.session_state["entrada"] = {"nombre": f"pg{libro['id']}.txt", "datos": datos,
                                           "origen": "gutenberg", "libro": libro}
            st.rerun()


def seccion_entrada():
    """1. Entrada: archivo local, libro de Gutenberg o texto escrito. Regresa (nombre, datos) o None."""
    st.header("1. Entrada")
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
        st.session_state.pop("entrada")
        st.session_state.pop("archivo_visto", None)
        # Clave nueva = el cargador de archivos queda vacío (si no, volvería a tomar el mismo .txt).
        st.session_state["subida_n"] = st.session_state.get("subida_n", 0) + 1
        st.rerun()
    return entrada["nombre"], entrada["datos"]


def seccion_analisis(datos: bytes) -> dict:
    """2. Analizar: tabla de frecuencias."""
    st.header("2. Analizar: frecuencias")
    frecuencias = contar_frecuencias(datos)
    st.write(f"**{tamano_legible(len(datos))}** · **{len(frecuencias)}** símbolos diferentes (cada símbolo es un byte)")
    st.dataframe(tabla(frecuencias), hide_index=True, height=300)
    return frecuencias


def seccion_pasos(frecuencias: dict):
    """3. Construcción paso a paso con la cola de prioridad."""
    st.header("3. Construcción paso a paso")
    vista = pasos_construccion(frecuencias)
    total = len(vista["pasos"])
    if total == 0:
        st.info(texto_paso(0, vista))
        return
    k = st.slider("Paso", 0, total, 0, help="0 = cola inicial; el último paso deja el árbol completo.")
    st.write(texto_paso(k, vista))

    cola = vista["inicial"] if k == 0 else vista["pasos"][k - 1]["cola"]
    nuevo = None if k == 0 else vista["pasos"][k - 1]["padre"]
    if k > 0:
        paso = vista["pasos"][k - 1]
        st.caption(f"Salen: izquierdo (bit 0) = {etiqueta_nodo(paso['izquierdo'])} · derecho (bit 1) = {etiqueta_nodo(paso['derecho'])}")
    # Con cientos de nodos la cola es larga: se muestra el inicio y se avisa.
    visibles = cola[:40]
    st.write("**Cola de prioridad** (de menor a mayor frecuencia): "
             + " · ".join(f"`{etiqueta_nodo(n)}`" + (" ⭐" if n is nuevo else "") for n in visibles)
             + (f" … (+{len(cola) - len(visibles)} más)" if len(cola) > len(visibles) else ""))
    if len(cola) <= MAX_HOJAS_ARBOL:
        st.graphviz_chart(arbol_dot(cola, nuevo=nuevo))
    else:
        st.caption("El bosque es muy grande para dibujarlo; avanza con el deslizador para ver cómo se reduce.")


def seccion_huffman(frecuencias: dict):
    """4. Códigos de Huffman y árbol, con el camino de bits de un símbolo."""
    st.header("4. Códigos y árbol de Huffman")
    raiz = construir_arbol(frecuencias)
    codigos = generar_codigos(raiz)
    st.caption("Los símbolos más frecuentes reciben los códigos más cortos.")
    st.dataframe(tabla_bits(frecuencias, codigos), hide_index=True, height=300)

    simbolos = sorted(frecuencias, key=lambda s: (-frecuencias[s], s))
    elegido = st.selectbox("Resalta el camino de un símbolo", simbolos,
                           format_func=lambda s: f"{simbolo_corto(s)}  (byte {s}) → {codigos[s]}")
    st.write(f"Camino de `{simbolo_corto(elegido)}`: " + (
        " → ".join(f"{'izquierda' if b == '0' else 'derecha'} ({b})" for b in codigos[elegido])
        if not raiz.es_hoja() else "es la única hoja: se le asigna el código 0"))
    dibujar_arbol(arbol_dot(raiz, camino_a_simbolo(raiz, elegido)), len(frecuencias), "arbol_completo")


def seccion_comprimir(nombre: str, datos: bytes, frecuencias: dict):
    """5. Comprimir y medir: genera el .hfa, muestra métricas y permite descargarlo."""
    st.header("5. Comprimir y medir")
    clave = (nombre, datos)  # identifica la entrada actual
    if st.button("Comprimir", type="primary"):
        st.session_state["comprimido"] = (clave, comprimir(datos, nombre))
    guardado = st.session_state.get("comprimido")
    if not guardado or guardado[0] != clave:
        return
    hfa = guardado[1]
    mostrar_metricas(metricas(len(datos), len(hfa), len(frecuencias)))
    st.download_button(f"Descargar {Path(nombre).stem}{EXTENSION}", hfa,
                       file_name=Path(nombre).stem + EXTENSION, mime="application/octet-stream")
    st.info("Siguiente paso: abre la pestaña **Inspector / Descomprimir**; ahí puedes usar este archivo "
            "directamente o subir otro .hfa.")


# ---------- Pestaña INSPECTOR / DESCOMPRIMIR ----------

def obtener_hfa():
    """Origen del .hfa: el recién comprimido o uno subido. Regresa (nombre_archivo, bytes) o None."""
    guardado = st.session_state.get("comprimido")
    if guardado:
        (nombre, _), hfa = guardado
        nombre_hfa = Path(nombre).stem + EXTENSION
        if st.toggle(f"Inspeccionar el archivo recién comprimido ({nombre_hfa})", value=True, key="usar_reciente"):
            return nombre_hfa, hfa
    archivo = st.file_uploader(f"Archivo comprimido {EXTENSION}", type=[EXTENSION[1:]])
    return (archivo.name, archivo.getvalue()) if archivo else None


def seccion_inspector():
    """6. Inspector: examina el .hfa sin el original; después permite DESCOMPRIMIR."""
    st.header("6. Inspector del archivo comprimido")
    origen = obtener_hfa()
    if not origen:
        return
    nombre_archivo, contenido = origen
    try:
        info = leer_hfa(contenido)
    except ValueError as error:
        st.error(str(error))
        return

    st.subheader("Metadatos del encabezado")
    st.table({
        "Campo": ["Archivo", "Extensión", "Formato / versión", "Nombre original",
                  "Total de bits codificados", "Bits válidos del último byte",
                  "Tamaño del encabezado", "Tamaño de los datos", "SHA-256 del original"],
        "Valor": [nombre_archivo, Path(nombre_archivo).suffix, f"{FIRMA.decode()} v{info['version']}",
                  info["nombre_original"], f"{info['total_bits']:,}", str(info["bits_ultimo_byte"]),
                  tamano_legible(info["tamano_encabezado"]), tamano_legible(len(info["datos"])),
                  info["sha256"].hex()],
    })
    mostrar_metricas(metricas(info["tamano_original"], len(contenido), len(info["frecuencias"])))

    # Todo sale del .hfa: la tabla de frecuencias reconstruye el mismo árbol, sin el texto original.
    raiz = construir_arbol(info["frecuencias"])
    codigos = generar_codigos(raiz)
    st.subheader("Bits por símbolo")
    st.caption("Cada símbolo cuesta lo que mide su código en lugar de 8 bits.")
    st.dataframe(tabla_bits(info["frecuencias"], codigos), hide_index=True, height=300)

    st.subheader("Primeros bytes y palabras de código")
    c1, c2 = st.columns(2)
    c1.write("**Primeros bytes comprimidos**")
    c1.dataframe(bytes_muestra(info["datos"], info["total_bits"]), hide_index=True)
    c2.write("**Los primeros bits, separados por símbolo**")
    c2.dataframe(segmentar_bits(info["datos"], info["total_bits"], raiz), hide_index=True)

    with st.expander("Árbol reconstruido desde el encabezado"):
        dibujar_arbol(arbol_dot(raiz), len(info["frecuencias"]), "arbol_inspector")

    st.subheader("7. Descomprimir y verificar")
    clave = (nombre_archivo, contenido)  # identifica el .hfa actual
    if st.button("DESCOMPRIMIR", type="primary"):
        st.session_state["recuperado"] = (clave, descomprimir(contenido))
    guardado = st.session_state.get("recuperado")
    if not guardado or guardado[0] != clave:
        return
    datos, integridad_ok = guardado[1]
    if integridad_ok:
        st.success("Integridad verificada: el SHA-256 del texto recuperado es idéntico al original.")
    else:
        st.error("Integridad fallida: el texto recuperado NO coincide con el original.")
    st.text_area("Texto recuperado (primeros 5,000 caracteres)",
                 datos[:5000].decode("utf-8", errors="replace"), height=250)
    st.download_button("Descargar texto recuperado (.txt)", datos,
                       file_name="recuperado_" + info["nombre_original"], mime="text/plain")


# ---------- Página ----------

st.set_page_config(page_title="Huffman Web Compressor", layout="wide")
configurar_gutenberg()
st.title("Huffman Web Compressor")
st.caption("SUBIR TXT / BUSCAR LIBRO → ANALIZAR → CONSTRUIR HUFFMAN → COMPRIMIR → INSPECCIONAR → DESCOMPRIMIR → VERIFICAR")

tab_comprimir, tab_inspector = st.tabs(["Comprimir", "Inspector / Descomprimir"])
with tab_comprimir:
    entrada = seccion_entrada()
    if entrada:
        nombre, datos = entrada
        frecuencias = seccion_analisis(datos)
        if frecuencias:
            seccion_pasos(frecuencias)
            seccion_huffman(frecuencias)
            seccion_comprimir(nombre, datos, frecuencias)
        else:
            st.warning("El archivo está vacío.")
with tab_inspector:
    seccion_inspector()
