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
from huffman.compresor import comprimir, metricas, tamano_legible
from huffman.formato import EXTENSION
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
    st.info("Sección en construcción (tarea B7-03).")
