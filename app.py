"""Bloque 7 — Interfaz web (Streamlit).

Ejecutar:  streamlit run app.py

Flujo:  SUBIR TXT / BUSCAR LIBRO → ANALIZAR → CONSTRUIR HUFFMAN → COMPRIMIR
        → INSPECCIONAR → DESCOMPRIMIR → VERIFICAR → DESCARGAR

Cada sección de la página es una función. La parte de abajo del archivo
decide el orden en que se muestran.
"""

from pathlib import Path

import streamlit as st

from huffman.arbol import construir_arbol
from huffman.codigos import generar_codigos
from huffman.compresor import comprimir, descomprimir, metricas, tamano_legible
from huffman.formato import EXTENSION, FIRMA, leer_hfa
from huffman.frecuencias import contar_frecuencias
from huffman.visual import tabla


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


# ---------- Pestaña COMPRIMIR ----------

def seccion_entrada():
    """1. Entrada: archivo .txt local. Regresa (nombre, datos) o None."""
    st.header("1. Entrada")
    archivo = st.file_uploader("Archivo de texto", type=["txt"])
    return (archivo.name, archivo.getvalue()) if archivo else None


def seccion_analisis(datos: bytes) -> dict:
    """2. Analizar: tabla de frecuencias."""
    st.header("2. Analizar: frecuencias")
    frecuencias = contar_frecuencias(datos)
    st.write(f"**{tamano_legible(len(datos))}** · **{len(frecuencias)}** símbolos diferentes (cada símbolo es un byte)")
    st.dataframe(tabla(frecuencias), hide_index=True, height=300)
    return frecuencias


def seccion_huffman(frecuencias: dict):
    """3. Construir Huffman: códigos."""
    st.header("3. Construir Huffman: códigos")
    raiz = construir_arbol(frecuencias)
    codigos = generar_codigos(raiz)
    st.caption("Los símbolos más frecuentes reciben los códigos más cortos.")
    st.dataframe(tabla(frecuencias, codigos), hide_index=True, height=300)


def seccion_comprimir(nombre: str, datos: bytes, frecuencias: dict):
    """4. Comprimir y medir: genera el .hfa, muestra métricas y permite descargarlo."""
    st.header("4. Comprimir y medir")
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
    st.info("Siguiente paso: abre la pestaña **Inspector / Descomprimir** y sube el archivo descargado.")


# ---------- Pestaña INSPECTOR / DESCOMPRIMIR ----------

def seccion_inspector():
    """5. Inspector: examina el .hfa sin el original; después permite DESCOMPRIMIR."""
    st.header("5. Inspector del archivo comprimido")
    archivo = st.file_uploader(f"Archivo comprimido {EXTENSION}", type=[EXTENSION[1:]])
    if not archivo:
        return
    contenido = archivo.getvalue()
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
        "Valor": [archivo.name, Path(archivo.name).suffix, f"{FIRMA.decode()} v{info['version']}",
                  info["nombre_original"], f"{info['total_bits']:,}", str(info["bits_ultimo_byte"]),
                  tamano_legible(info["tamano_encabezado"]), tamano_legible(len(info["datos"])),
                  info["sha256"].hex()],
    })
    mostrar_metricas(metricas(info["tamano_original"], len(contenido), len(info["frecuencias"])))

    st.subheader("6. Descomprimir y verificar")
    clave = (archivo.name, contenido)  # identifica el .hfa actual
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
st.title("Huffman Web Compressor")
st.caption("SUBIR TXT / BUSCAR LIBRO → ANALIZAR → CONSTRUIR HUFFMAN → COMPRIMIR → INSPECCIONAR → DESCOMPRIMIR → VERIFICAR")

tab_comprimir, tab_inspector = st.tabs(["Comprimir", "Inspector / Descomprimir"])
with tab_comprimir:
    entrada = seccion_entrada()
    if entrada:
        nombre, datos = entrada
        frecuencias = seccion_analisis(datos)
        if frecuencias:
            seccion_huffman(frecuencias)
            seccion_comprimir(nombre, datos, frecuencias)
        else:
            st.warning("El archivo está vacío.")
with tab_inspector:
    seccion_inspector()
