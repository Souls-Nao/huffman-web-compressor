"""Bloque 8 — Gutenberg: buscar libros y descargarlos.

Fuente: Project Gutenberg (catálogo OPDS, un feed Atom/XML).
    buscar:    consulta -> petición OPDS -> lista de {id, titulo, autor}
    descargar: id -> texto plano del libro, en bytes tal cual (sin decodificar),
               listo para pasarlo a comprimir() (un símbolo es un byte).

Errores (para que app.py los muestre con st.error):
    ValueError:      entrada inválida, libro no encontrado o libro vacío.
    ConnectionError: timeout, falla de red, HTTP >= 500, mantenimiento o respuesta
                     ilegible (la integrada de Python, no requests.ConnectionError).

Proxy (opcional). gutenberg.org a veces bloquea las IP de los servidores en la nube
o está en mantenimiento. Hay dos formas de rodearlo, y se pueden combinar:

    GUTENBERG_PROXY_URL   URL base de un proxy inverso que reenvía las MISMAS rutas
                          (por ejemplo el Cloudflare Worker de web/proxy/worker.js).
                          Se prueba primero; si falla, se intenta gutenberg.org directo.
    GUTENBERG_HTTP_PROXY  proxy HTTP(S) clásico (http://usuario:clave@host:puerto) por el
                          que salen las peticiones. Además, `requests` ya respeta las
                          variables estándar HTTP_PROXY / HTTPS_PROXY / NO_PROXY.

Se leen de las variables de entorno o se fijan desde código con configurar()
(app.py lo hace con st.secrets).
"""

import os
import re
import xml.etree.ElementTree as ET

import requests

ORIGEN = "https://www.gutenberg.org"
RUTA_BUSQUEDA = "/ebooks/search.opds/"
RUTA_LIBRO = "/cache/epub/{id}/pg{id}.txt"
# Se conservan por compatibilidad: la URL directa (sin proxy).
URL_BUSQUEDA = ORIGEN + RUTA_BUSQUEDA
URL_LIBRO = ORIGEN + RUTA_LIBRO
TIMEOUT = 15  # segundos
ENCABEZADOS = {"User-Agent": "huffman-web-compressor (proyecto escolar)"}

# Prefijos de la búsqueda de Gutenberg: "a.twain" busca por autor, etc.
PREFIJOS = {"titulo": "t.", "autor": "a.", "tema": "s."}

ATOM = "{http://www.w3.org/2005/Atom}"
# Solo las entradas cuyo id es un libro (".../ebooks/2000.opds") cuentan;
# "Next Page" y el aviso "No records found." se ignoran.
ID_LIBRO = re.compile(r"/ebooks/(\d+)\.opds$")

# Ajustes puestos desde código (tienen prioridad sobre las variables de entorno).
_ajustes = {"proxy_url": None, "proxy_http": None}


def configurar(proxy_url: str | None = None, proxy_http: str | None = None) -> None:
    """Fija el proxy inverso y/o el proxy HTTP. Cadena vacía o None = no usar."""
    _ajustes["proxy_url"] = (proxy_url or "").strip() or None
    _ajustes["proxy_http"] = (proxy_http or "").strip() or None


def _proxy_url() -> str | None:
    valor = _ajustes["proxy_url"] or os.environ.get("GUTENBERG_PROXY_URL", "").strip()
    return valor.rstrip("/") or None


def _proxy_http() -> str | None:
    return _ajustes["proxy_http"] or os.environ.get("GUTENBERG_HTTP_PROXY", "").strip() or None


def describir_conexion() -> str:
    """Texto corto para la interfaz: por dónde saldrán las peticiones (sin mostrar claves)."""
    partes = []
    if _proxy_url():
        partes.append("proxy inverso, con respaldo directo")
    else:
        partes.append("directa a gutenberg.org")
    if _proxy_http():
        partes.append("proxy HTTP configurado")
    return " · ".join(partes)


def _bases() -> list[str]:
    """Orígenes a intentar, en orden: el proxy inverso (si hay) y luego gutenberg.org."""
    proxy = _proxy_url()
    return [proxy, ORIGEN] if proxy else [ORIGEN]


def _pedir_a(url: str, **opciones) -> requests.Response:
    """Un GET con timeout. 404 -> ValueError; fallas de red/5xx -> ConnectionError."""
    proxy_http = _proxy_http()
    if proxy_http:
        opciones.setdefault("proxies", {"http": proxy_http, "https": proxy_http})
    try:
        respuesta = requests.get(url, timeout=TIMEOUT, headers=ENCABEZADOS, **opciones)
        if respuesta.status_code == 404:
            raise ValueError("No se encontró el libro en Gutenberg.")
        if respuesta.status_code in (502, 503, 504):
            raise ConnectionError(
                f"Gutenberg no está disponible (HTTP {respuesta.status_code}); "
                "puede estar en mantenimiento. Intenta más tarde.")
        respuesta.raise_for_status()
    except (requests.Timeout, requests.exceptions.ConnectionError, requests.HTTPError) as error:
        raise ConnectionError(f"No se pudo obtener la respuesta de Gutenberg: {error}") from error
    return respuesta


def _pedir(ruta: str, **opciones) -> requests.Response:
    """Pide `ruta` a cada origen en orden. Si un origen falla por red, prueba el siguiente.

    Un 404 (ValueError) no se reintenta: el libro no existe en ningún origen.
    """
    ultimo_error = None
    for base in _bases():
        try:
            return _pedir_a(base + ruta, **opciones)
        except ConnectionError as error:
            ultimo_error = error
    raise ultimo_error


def _parece_pagina_html(contenido: bytes) -> bool:
    """Una página de mantenimiento llega como HTML con código 200; un libro nunca empieza así."""
    inicio = contenido[:200].lstrip().lower()
    return inicio.startswith((b"<!doctype html", b"<html"))


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
    respuesta = _pedir(RUTA_BUSQUEDA, params={"query": PREFIJOS[campo] + consulta.strip()})
    if _parece_pagina_html(respuesta.content):
        raise ConnectionError("Gutenberg regresó una página web en vez del catálogo "
                              "(posible mantenimiento). Intenta más tarde.")
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
    contenido = _pedir(RUTA_LIBRO.format(id=id)).content
    if not contenido:
        raise ValueError("Gutenberg regresó el libro vacío.")
    if _parece_pagina_html(contenido):
        raise ConnectionError("Gutenberg regresó una página web en vez del libro "
                              "(posible mantenimiento). Intenta más tarde.")
    return contenido
