"""Piezas de la interfaz (HTML y CSS) para app.py, sin depender de Streamlit.

Reproducen el aspecto de la versión web en JavaScript (web/src/styles y los módulos):
cabecera con la barra de flujo, encabezados numerados, fichas de la cola de prioridad,
bits coloreados (0 azul, 1 ámbar), barra comparativa y tarjetas de bytes/palabras de código.

Todo el texto que viene del usuario (símbolos, nombres) pasa por html.escape, porque
app.py lo muestra con unsafe_allow_html. Las funciones regresan HTML en UNA línea, sin
sangrías ni líneas en blanco, para que Markdown no lo convierta en bloque de código.
"""

import html

from .visual import etiqueta_nodo

PASOS_FLUJO = [
    ("entrada", "Subir / buscar"), ("analizar", "Analizar"), ("huffman", "Construir Huffman"),
    ("comprimir", "Comprimir"), ("inspeccionar", "Inspeccionar"), ("descomprimir", "Descomprimir"),
    ("verificar", "Verificar"),
]

# Colores con transparencia y "inherit": se ven bien en el tema claro y en el oscuro de Streamlit.
CSS = """
.hfa-cabecera { background: linear-gradient(135deg, #312e81, #4f46e5 55%, #0d9488); color: #fff; padding: 1.3rem 1.5rem 1rem; border-radius: 12px; margin-bottom: 1rem; }
.hfa-cabecera h1 { color: #fff; font-size: clamp(1.5rem, 3vw, 2.1rem); margin: 0; padding: 0; }
.hfa-cabecera p { margin: .15rem 0 .9rem; opacity: .88; color: #fff; }
.hfa-cabecera code { background: rgb(255 255 255 / 18%); color: #fff; padding: .05rem .4rem; border-radius: 6px; }
.hfa-flujo { list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: .4rem; counter-reset: paso; }
.hfa-flujo li { counter-increment: paso; font-size: .8rem; font-weight: 600; padding: .3rem .7rem .3rem .5rem; border-radius: 999px; background: rgb(255 255 255 / 14%); display: flex; align-items: center; gap: .4rem; margin: 0; }
.hfa-flujo li::before { content: counter(paso); display: grid; place-items: center; width: 1.3rem; height: 1.3rem; border-radius: 50%; background: rgb(255 255 255 / 25%); font-size: .75rem; }
.hfa-flujo li.hecho { background: rgb(255 255 255 / 92%); color: #14532d; }
.hfa-flujo li.hecho::before { content: "✓"; background: #bbf7d0; }
.hfa-flujo li.actual { outline: 2px solid #fff; outline-offset: 1px; }
.hfa-seccion { display: flex; align-items: center; gap: .6rem; margin: 1.6rem 0 .5rem; }
.hfa-seccion .numero { display: grid; place-items: center; min-width: 2rem; height: 2rem; border-radius: 50%; background: #4f46e5; color: #fff; font-weight: 700; font-size: .95rem; }
.hfa-seccion h2 { margin: 0; padding: 0; font-size: 1.45rem; }
.hfa-b0 { color: #3b82f6; font-weight: 700; }
.hfa-b1 { color: #f59e0b; font-weight: 700; }
.hfa-codigo { font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; letter-spacing: .08em; }
.hfa-cola-titulo { font-weight: 600; margin: .6rem 0 .3rem; }
.hfa-cola-titulo span { font-weight: 400; opacity: .65; }
.hfa-cola { display: flex; flex-wrap: wrap; gap: .4rem; margin: 0 0 .3rem; }
.hfa-ficha { display: inline-flex; flex-direction: column; align-items: center; min-width: 3.2rem; padding: .3rem .6rem; border-radius: 8px; border: 2px solid rgb(128 128 128 / 35%); background: rgb(128 128 128 / 12%); font: 700 .95rem ui-monospace, Menlo, Consolas, monospace; }
.hfa-ficha small { font: 600 .65rem system-ui, sans-serif; opacity: .7; }
.hfa-ficha.hoja { background: rgb(79 70 229 / 16%); }
.hfa-ficha.izquierdo, .hfa-ficha.derecho { border-color: #d97706; background: rgb(217 119 6 / 18%); }
.hfa-ficha.nuevo { border-color: #15803d; background: rgb(21 128 61 / 20%); }
.hfa-ficha.mas { border-style: dashed; opacity: .7; }
.hfa-texto-paso { padding: .6rem .8rem; border-left: 4px solid #4f46e5; background: rgb(79 70 229 / 12%); border-radius: 0 8px 8px 0; margin: .5rem 0; }
.hfa-comparacion { display: grid; gap: .35rem; margin: .5rem 0 1rem; }
.hfa-barra { padding: .35rem .7rem; border-radius: 8px; color: #fff; font-weight: 600; font-size: .85rem; white-space: nowrap; overflow: hidden; }
.hfa-barra.original { background: #5b6279; width: 100%; }
.hfa-barra.comprimido { background: #0d9488; min-width: 4.5rem; }
.hfa-bytes, .hfa-palabras { display: flex; flex-wrap: wrap; gap: .4rem; margin-bottom: .5rem; }
.hfa-byte, .hfa-palabra { display: inline-flex; flex-direction: column; align-items: center; padding: .3rem .5rem; border-radius: 8px; border: 1px solid rgb(128 128 128 / 35%); background: rgb(128 128 128 / 12%); }
.hfa-palabra { background: rgb(79 70 229 / 14%); border-color: #4f46e5; }
.hfa-byte small, .hfa-palabra small { font-family: ui-monospace, Menlo, Consolas, monospace; font-weight: 700; opacity: .7; }
.hfa-pie { opacity: .65; font-size: .85rem; padding: 1.5rem 0 1rem; }
"""


def e(texto) -> str:
    """Escapa texto para HTML (incluye comillas)."""
    return html.escape(str(texto), quote=True)


def estilos() -> str:
    return f"<style>{CSS}</style>"


def encabezado_seccion(numero, titulo: str) -> str:
    return f'<div class="hfa-seccion"><span class="numero">{e(numero)}</span><h2>{e(titulo)}</h2></div>'


def estado_flujo(hechos: dict) -> list[dict]:
    """[{clave, etiqueta, hecho, actual}]: 'actual' es el primer paso que falta."""
    pasos, hay_actual = [], False
    for clave, etiqueta in PASOS_FLUJO:
        hecho = bool(hechos.get(clave))
        actual = not hecho and not hay_actual
        hay_actual = hay_actual or actual
        pasos.append({"clave": clave, "etiqueta": etiqueta, "hecho": hecho, "actual": actual})
    return pasos


def cabecera(hechos: dict) -> str:
    items = "".join(
        f'<li class="{" ".join(c for c in ("hecho" if p["hecho"] else "", "actual" if p["actual"] else "") if c)}">{e(p["etiqueta"])}</li>'
        for p in estado_flujo(hechos))
    return ('<div class="hfa-cabecera"><h1>Huffman Web Compressor</h1>'
            '<p>Compresión voraz de texto · formato propio <code>.hfa</code></p>'
            f'<ol class="hfa-flujo" aria-label="Flujo de la aplicación">{items}</ol></div>')


def bits_html(bits: str) -> str:
    """'0110' con el 0 en azul y el 1 en ámbar."""
    celdas = "".join(f'<span class="hfa-b{b}">{b}</span>' for b in bits if b in "01")
    return f'<span class="hfa-codigo">{celdas}</span>'


def fichas_cola(titulo: str, nodos: list, marcas: dict | None = None, nota: str | None = None, maximo: int = 14) -> str:
    """Cola de prioridad como fichas. `marcas`: {id(nodo): "izquierdo" | "derecho" | "nuevo"}."""
    marcas = marcas or {}
    textos_marca = {"izquierdo": "sale · 0", "derecho": "sale · 1", "nuevo": "nuevo"}
    fichas = []
    for nodo in nodos[:maximo]:
        marca = marcas.get(id(nodo), "")
        extra = f"<small>{textos_marca[marca]}</small>" if marca else ""
        clase = f'hfa-ficha {"hoja" if nodo.es_hoja() else "interno"} {marca}'.rstrip()
        fichas.append(f'<div class="{clase}"><span>{e(etiqueta_nodo(nodo))}</span>{extra}</div>')
    if len(nodos) > maximo:
        fichas.append(f'<div class="hfa-ficha mas">… +{len(nodos) - maximo}</div>')
    plural = "nodo" if len(nodos) == 1 else "nodos"
    pie = f'<small style="opacity:.7">{e(nota)}</small>' if nota else ""
    return (f'<div class="hfa-cola-titulo">{e(titulo)} <span>· {len(nodos)} {plural}</span></div>'
            f'<div class="hfa-cola">{"".join(fichas)}</div>{pie}')


def texto_del_paso(texto: str) -> str:
    return f'<div class="hfa-texto-paso">{e(texto)}</div>'


def comparacion(original: int, final: int, etiqueta_original: str, etiqueta_final: str) -> str:
    """Dos barras: el original al 100 % y el final en proporción (mínimo 8 % para que se lea)."""
    proporcion = min(100.0, final / max(1, original) * 100)
    ancho = max(proporcion, 8)
    return (f'<div class="hfa-comparacion" role="img" aria-label="El resultado ocupa el {proporcion:.1f} % del original">'
            f'<div class="hfa-barra original">{e(etiqueta_original)}</div>'
            f'<div class="hfa-barra comprimido" style="width:{ancho:.1f}%">{e(etiqueta_final)}</div></div>')


def bytes_html(filas: list[dict]) -> str:
    """Tarjetas de los primeros bytes: binario (coloreado) y hexadecimal."""
    tarjetas = "".join(f'<div class="hfa-byte">{bits_html(f["Binario"])}<small>{e(f["Hex"])}</small></div>' for f in filas)
    return f'<div class="hfa-bytes">{tarjetas}</div>'


def palabras_html(segmentos: list[dict]) -> str:
    """Los primeros bits separados por palabra de código, con el símbolo que representa cada una."""
    chips = "".join(f'<div class="hfa-palabra">{bits_html(s["Bits"])}<small>{e(s["Símbolo"])}</small></div>' for s in segmentos)
    return f'<div class="hfa-palabras">{chips}</div>'


def pie() -> str:
    return '<div class="hfa-pie">Análisis de Algoritmos · 2026B · Huffman implementado por el equipo, sin bibliotecas de compresión.</div>'
