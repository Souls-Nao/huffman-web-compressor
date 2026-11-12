"""Bloque 8 — Gutenberg: buscar libros y descargarlos.

Fuente: Project Gutenberg (catálogo OPDS, un feed Atom/XML).
    buscar:    consulta -> petición OPDS -> lista de {id, titulo, autor}
    descargar: id -> texto plano del libro, en bytes tal cual (sin decodificar),
               listo para pasarlo a comprimir() (un símbolo es un byte).

Errores (para que app.py los muestre con st.error):
    ValueError:      entrada inválida, libro no encontrado o libro vacío.
    ConnectionError: timeout, falla de red, HTTP >= 500 o respuesta ilegible
                     (la integrada de Python, no requests.ConnectionError).
"""

import re
import xml.etree.ElementTree as ET

import requests

URL_BUSQUEDA = "https://www.gutenberg.org/ebooks/search.opds/"
URL_LIBRO = "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt"
TIMEOUT = 15  # segundos
ENCABEZADOS = {"User-Agent": "huffman-web-compressor (proyecto escolar)"}

# Prefijos de la búsqueda de Gutenberg: "a.twain" busca por autor, etc.
PREFIJOS = {"titulo": "t.", "autor": "a.", "tema": "s."}

ATOM = "{http://www.w3.org/2005/Atom}"
# Solo las entradas cuyo id es un libro (".../ebooks/2000.opds") cuentan;
# "Next Page" y el aviso "No records found." se ignoran.
ID_LIBRO = re.compile(r"/ebooks/(\d+)\.opds$")


def _pedir(url: str, **opciones) -> requests.Response:
    """GET con timeout. Traduce las fallas de red a ConnectionError y el 404 a ValueError."""
    try:
        respuesta = requests.get(url, timeout=TIMEOUT, headers=ENCABEZADOS, **opciones)
        if respuesta.status_code == 404:
            raise ValueError("No se encontró el libro en Gutenberg.")
        respuesta.raise_for_status()
    except (requests.Timeout, requests.exceptions.ConnectionError, requests.HTTPError) as error:
        raise ConnectionError(f"No se pudo obtener la respuesta de Gutenberg: {error}") from error
    return respuesta


def buscar(consulta: str, campo: str = "titulo") -> list[dict]:
    """Busca libros. `campo`: "titulo", "autor" o "tema".

    Regresa [{"id": 2000, "titulo": "...", "autor": "..."}]; [] si no hay resultados.
    El autor es "" cuando la entrada no lo trae.
    """
    if campo not in PREFIJOS:
        raise ValueError(f"Campo inválido: {campo!r} (usa {', '.join(PREFIJOS)}).")
    if not isinstance(consulta, str) or not consulta.strip():
        raise ValueError("La consulta está vacía.")

    # `params` deja que requests codifique espacios y acentos.
    respuesta = _pedir(URL_BUSQUEDA, params={"query": PREFIJOS[campo] + consulta.strip()})
    try:
        raiz = ET.fromstring(respuesta.content)
    except ET.ParseError as error:
        raise ConnectionError("Gutenberg regresó una respuesta ilegible.") from error

    libros = []
    for entrada in raiz.findall(ATOM + "entry"):
        coincidencia = ID_LIBRO.search(entrada.findtext(ATOM + "id", ""))
        if not coincidencia:
            continue
        libros.append({
            "id": int(coincidencia.group(1)),
            "titulo": entrada.findtext(ATOM + "title", "").strip(),
            "autor": (entrada.findtext(ATOM + "content") or "").strip(),
        })
    return libros


def descargar(id: int) -> bytes:
    """Descarga el texto de un libro y regresa sus bytes sin modificar."""
    if isinstance(id, bool) or not isinstance(id, int) or id <= 0:
        raise ValueError(f"Id de libro inválido: {id!r}.")
    contenido = _pedir(URL_LIBRO.format(id=id)).content
    if not contenido:
        raise ValueError("Gutenberg regresó el libro vacío.")
    return contenido
