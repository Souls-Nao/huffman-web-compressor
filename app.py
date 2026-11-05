"""Bloque 7 — Interfaz web (Streamlit).

Ejecutar:  streamlit run app.py

Flujo:  SUBIR TXT / BUSCAR LIBRO → ANALIZAR → CONSTRUIR HUFFMAN → COMPRIMIR
        → INSPECCIONAR → DESCOMPRIMIR → VERIFICAR → DESCARGAR

Cada sección de la página es una función. La parte de abajo del archivo
decide el orden en que se muestran.
"""

import streamlit as st

from huffman.arbol import construir_arbol
from huffman.codigos import generar_codigos
from huffman.compresor import tamano_legible
from huffman.frecuencias import contar_frecuencias
from huffman.visual import tabla


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


# ---------- Página ----------

st.set_page_config(page_title="Huffman Web Compressor", layout="wide")
st.title("Huffman Web Compressor")
st.caption("SUBIR TXT / BUSCAR LIBRO → ANALIZAR → CONSTRUIR HUFFMAN → COMPRIMIR → INSPECCIONAR → DESCOMPRIMIR → VERIFICAR")

tab_comprimir, tab_inspector = st.tabs(["Comprimir", "Inspector / Descomprimir"])
with tab_comprimir:
    entrada = seccion_entrada()
    if entrada:
        _, datos = entrada
        frecuencias = seccion_analisis(datos)
        if frecuencias:
            seccion_huffman(frecuencias)
        else:
            st.warning("El archivo está vacío.")
with tab_inspector:
    st.info("Sección en construcción (tarea B7-03).")
