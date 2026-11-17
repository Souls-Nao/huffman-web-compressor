"""Datos del inspector (sin Streamlit). Dos fuentes con el mismo formato de salida:

    vista_desde_texto(nombre, datos, frecuencias)   texto actual: el tamaño final se calcula, no se genera el .hfa
    vista_desde_hfa(contenido, nombre_archivo)      solo el .hfa: nada del texto original

Es el equivalente de web/src/modules/inspector/viewmodel.js.
"""

from pathlib import Path

from .arbol import construir_arbol
from .bits import empaquetar
from .codigos import generar_codigos
from .compresor import metricas, tamano_legible
from .formato import FIRMA, leer_hfa, tamano_hfa

PREFIJO_BYTES = 96  # bytes de texto que se codifican para la vista parcial de bits


def _armar(nombre, tamano_original, tamano_final, total_bits, frecuencias, datos_muestra, metadatos):
    raiz = construir_arbol(frecuencias)
    return {
        "nombre": nombre, "frecuencias": frecuencias, "raiz": raiz, "codigos": generar_codigos(raiz),
        "total_bits": total_bits, "tamano_original": tamano_original, "tamano_final": tamano_final,
        "metricas": metricas(tamano_original, tamano_final, len(frecuencias)),
        "muestra": datos_muestra,  # (bytes, total_bits) de lo que se enseña en "Primeros bits"
        "metadatos": metadatos,
    }


def vista_desde_texto(nombre: str, datos: bytes, frecuencias: dict) -> dict:
    raiz = construir_arbol(frecuencias)
    codigos = generar_codigos(raiz)
    total_bits = sum(frecuencias[s] * len(codigos[s]) for s in frecuencias)
    # Codificar solo el inicio del texto da exactamente los primeros bits del archivo final.
    bits = "".join(codigos[b] for b in datos[:PREFIJO_BYTES])
    empaquetados, _ = empaquetar(bits)
    return _armar(nombre, len(datos), tamano_hfa(nombre, len(frecuencias), total_bits), total_bits,
                  frecuencias, (empaquetados, len(bits)), None)


def vista_desde_hfa(contenido: bytes, nombre_archivo: str) -> dict:
    """Lanza ValueError si el archivo no es un .hfa válido."""
    info = leer_hfa(contenido)
    metadatos = [
        ("Archivo", nombre_archivo),
        ("Extensión", Path(nombre_archivo).suffix or "—"),
        ("Formato / versión", f"{FIRMA.decode()} v{info['version']}"),
        ("Nombre original", info["nombre_original"]),
        ("Total de bits codificados", f"{info['total_bits']:,}"),
        ("Bits válidos del último byte", str(info["bits_ultimo_byte"])),
        ("Tamaño del encabezado", tamano_legible(info["tamano_encabezado"])),
        ("Tamaño de los datos", tamano_legible(len(info["datos"]))),
        ("SHA-256 del original", info["sha256"].hex()),
    ]
    vista = _armar(info["nombre_original"], info["tamano_original"], len(contenido), info["total_bits"],
                   info["frecuencias"], (info["datos"], info["total_bits"]), metadatos)
    vista["info"] = info
    return vista
