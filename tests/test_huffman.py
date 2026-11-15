"""Bloque 11 — Pruebas unitarias. Ejecutar desde la raíz: python -m unittest -v"""

import os
import requests
from unittest.mock import Mock, patch

import unittest

from huffman.arbol import construir_arbol
from huffman.bits import desempaquetar, empaquetar
from huffman.codigos import generar_codigos
from huffman.compresor import comprimir, descomprimir, metricas
from huffman.formato import leer_hfa
from huffman.frecuencias import contar_frecuencias
from huffman.gutenberg import buscar, descargar

class TextoPequeno(unittest.TestCase):
    """Prueba 1: "abracadabra", comprobable a mano (ver docs/FORMATO.md)."""

    def test_frecuencias(self):
        # a=97, b=98, c=99, d=100, r=114
        self.assertEqual(contar_frecuencias(b"abracadabra"), {97: 5, 98: 2, 99: 1, 100: 1, 114: 2})

    def test_codigos_calculados_a_mano(self):
        # 1) une c(1)+d(1)=2   2) une b(2)+r(2)=4   3) une [cd](2)+[br](4)=6   4) une a(5)+6=11
        codigos = generar_codigos(construir_arbol(contar_frecuencias(b"abracadabra")))
        self.assertEqual(codigos, {97: "0", 98: "110", 99: "100", 100: "101", 114: "111"})

    def test_ningun_codigo_es_prefijo_de_otro(self):
        codigos = list(generar_codigos(construir_arbol(contar_frecuencias(bytes(range(256)) * 3 + b"aaab"))).values())
        for c1 in codigos:
            for c2 in codigos:
                if c1 != c2:
                    self.assertFalse(c2.startswith(c1))


class Bits(unittest.TestCase):
    def test_empaquetar_con_relleno(self):
        self.assertEqual(empaquetar("0100000101"), (b"\x41\x40", 2))
        self.assertEqual(empaquetar("01000001"), (b"\x41", 8))
        self.assertEqual(empaquetar(""), (b"", 0))

    def test_ida_y_vuelta(self):
        for bits in ["", "1", "0101", "01010101", "110010101"]:
            datos, _ = empaquetar(bits)
            self.assertEqual(desempaquetar(datos, len(bits)), bits)


class Integridad(unittest.TestCase):
    """Prueba 3: comprimir -> descomprimir debe dar exactamente lo mismo."""

    CASOS = {
        "texto normal": b"abracadabra",
        "vacio": b"",
        "un solo simbolo": b"aaaaaaa",
        "acentos y saltos de Windows": "¡Hola, ñandú!\r\nAdiós.\r\n".encode("utf-8"),
        "latin-1": "canción".encode("latin-1"),
        "los 256 bytes": bytes(range(256)) * 4,
    }

    def test_ida_y_vuelta(self):
        for nombre, datos in self.CASOS.items():
            with self.subTest(nombre):
                recuperado, ok = descomprimir(comprimir(datos, "prueba.txt"))
                self.assertEqual(recuperado, datos)
                self.assertTrue(ok)

    def test_detecta_archivo_danado(self):
        hfa = bytearray(comprimir(b"abracadabra" * 10, "prueba.txt"))
        hfa[-3] ^= 0b10000000  # cambiar un bit de los datos
        _, ok = descomprimir(bytes(hfa))
        self.assertFalse(ok)


class Formato(unittest.TestCase):
    def test_campos_del_encabezado(self):
        datos = b"abracadabra"
        info = leer_hfa(comprimir(datos, "abra.txt"))
        self.assertEqual(info["version"], 1)
        self.assertEqual(info["nombre_original"], "abra.txt")
        self.assertEqual(info["tamano_original"], 11)
        self.assertEqual(info["total_bits"], 23)  # 5·1 + 2·3 + 2·3 + 1·3 + 1·3
        self.assertEqual(info["bits_ultimo_byte"], 7)  # 23 = 8 + 8 + 7
        self.assertEqual(info["tamano_encabezado"], 58 + len("abra.txt") + 5 * 5)
        self.assertEqual(len(info["datos"]), 3)

    def test_no_guarda_el_texto_original(self):
        datos = b"texto secreto que no debe aparecer " * 20
        self.assertNotIn(b"texto secreto", comprimir(datos, "x.txt"))

    def test_rechaza_archivo_invalido(self):
        with self.assertRaises(ValueError):
            leer_hfa(b"esto no es hfa")
        with self.assertRaises(ValueError):
            leer_hfa(comprimir(b"abracadabra", "a.txt")[:20])  # cortado


class Metricas(unittest.TestCase):
    def test_metricas(self):
        m = metricas(1000, 600, 40)
        self.assertEqual(m["ahorro"], 400)
        self.assertAlmostEqual(m["reduccion"], 40.0)
        self.assertAlmostEqual(m["razon"], 1000 / 600)
        self.assertEqual(m["simbolos"], 40)

OPDS_EJEMPLO = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <id>https://www.gutenberg.org/ebooks/search.opds/?query=t.quijote</id>
  <title>Books: t.quijote</title>
  <entry>
    <id>https://www.gutenberg.org/ebooks/2000.opds</id>
    <title>El ingenioso hidalgo don Quijote de la Mancha</title>
    <content type="text">Miguel de Cervantes Saavedra</content>
    <link type="application/atom+xml" rel="subsection" href="/ebooks/2000.opds"/>
  </entry>
  <entry>
    <id>https://www.gutenberg.org/ebooks/996.opds</id>
    <title>Don Quixote</title>
    <content type="text">Miguel de Cervantes Saavedra</content>
  </entry>
  <entry>
    <id>https://www.gutenberg.org/ebooks/12345.opds</id>
    <title>Cañas y barro</title>
  </entry>
  <entry>
    <id>https://www.gutenberg.org/ebooks/search.opds/?query=t.quijote&amp;start_index=26</id>
    <title>Next Page</title>
  </entry>
</feed>""".encode("utf-8")
 
# Gutenberg avisa "sin resultados" con una entrada de relleno (no es un libro).
OPDS_SIN_RESULTADOS = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry><id>urn:no-records</id><title>No records found.</title></entry>
</feed>""".encode("utf-8")
 
OPDS_VACIO = b'<?xml version="1.0" encoding="utf-8"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>'
 
 
def respuesta(contenido=b"", status=200):
    """Respuesta falsa de requests: status, bytes y raise_for_status coherentes."""
    r = Mock()
    r.status_code = status
    r.content = contenido
    r.text = contenido.decode("utf-8", errors="replace")
    if status >= 400:
        r.raise_for_status.side_effect = requests.HTTPError(f"HTTP {status}", response=r)
    return r
 
 
def peticion(get):
    """(url, params, timeout) de la última llamada a requests.get."""
    args, kwargs = get.call_args
    return args[0], kwargs.get("params", {}), kwargs.get("timeout")
 
 
@patch("huffman.gutenberg.requests.get")
class GutenbergBuscar(unittest.TestCase):
    def test_devuelve_id_titulo_autor(self, get):
        get.return_value = respuesta(OPDS_EJEMPLO)
        self.assertEqual(buscar("quijote"), [
            {"id": 2000, "titulo": "El ingenioso hidalgo don Quijote de la Mancha",
             "autor": "Miguel de Cervantes Saavedra"},
            {"id": 996, "titulo": "Don Quixote", "autor": "Miguel de Cervantes Saavedra"},
            {"id": 12345, "titulo": "Cañas y barro", "autor": ""},  # sin autor: "", no KeyError
        ])
 
    def test_id_es_entero(self, get):
        get.return_value = respuesta(OPDS_EJEMPLO)
        for libro in buscar("quijote"):
            self.assertIsInstance(libro["id"], int)
 
    def test_ignora_entradas_que_no_son_libros(self, get):
        get.return_value = respuesta(OPDS_EJEMPLO)  # incluye una entrada "Next Page"
        self.assertEqual([l["id"] for l in buscar("quijote")], [2000, 996, 12345])
 
    def test_sin_resultados_regresa_lista_vacia(self, get):
        for nombre, xml in {"relleno": OPDS_SIN_RESULTADOS, "feed vacío": OPDS_VACIO}.items():
            with self.subTest(nombre):
                get.return_value = respuesta(xml)
                self.assertEqual(buscar("zzzzqqq"), [])
 
    def test_cada_campo_arma_una_consulta_distinta(self, get):
        get.return_value = respuesta(OPDS_EJEMPLO)
        for campo, prefijo in {"titulo": "t.", "autor": "a.", "tema": "s."}.items():
            with self.subTest(campo):
                buscar("cervantes", campo)
                self.assertEqual(peticion(get)[1], {"query": prefijo + "cervantes"})
 
    def test_campo_por_omision_es_titulo(self, get):
        get.return_value = respuesta(OPDS_EJEMPLO)
        buscar("quijote")
        self.assertEqual(peticion(get)[1], {"query": "t.quijote"})
 
    def test_consulta_va_en_params_y_no_pegada_a_la_url(self, get):
        get.return_value = respuesta(OPDS_EJEMPLO)
        buscar("don quijote ñandú")  # espacios y acentos: que los codifique requests
        url, params, _ = peticion(get)
        self.assertEqual(params, {"query": "t.don quijote ñandú"})
        self.assertNotIn("quijote", url)
 
    def test_quita_espacios_de_los_extremos(self, get):
        get.return_value = respuesta(OPDS_EJEMPLO)
        buscar("  quijote  ")
        self.assertEqual(peticion(get)[1], {"query": "t.quijote"})
 
    def test_usa_timeout(self, get):
        get.return_value = respuesta(OPDS_EJEMPLO)
        buscar("quijote")
        self.assertIsNotNone(peticion(get)[2])  # sin timeout la interfaz podría colgarse
 
    def test_entradas_invalidas_no_hacen_peticion(self, get):
        for consulta, campo in [("", "titulo"), ("   ", "titulo"), ("quijote", "isbn")]:
            with self.subTest(consulta=consulta, campo=campo):
                with self.assertRaises(ValueError):
                    buscar(consulta, campo)
        get.assert_not_called()
 
    def test_fallas_de_red_son_connectionerror(self, get):
        casos = {
            "HTTP 500": dict(return_value=respuesta(b"", 500)),
            "timeout": dict(side_effect=requests.exceptions.Timeout()),
            "sin conexión": dict(side_effect=requests.exceptions.ConnectionError()),
        }
        for nombre, config in casos.items():
            with self.subTest(nombre):
                get.reset_mock(return_value=True, side_effect=True)
                get.configure_mock(**config)
                with self.assertRaises(ConnectionError):  # la integrada de Python
                    buscar("quijote")
 
    def test_xml_malformado_es_error_controlado(self, get):
        get.return_value = respuesta(b"<feed><entry>esto no cierra")
        with self.assertRaises(ConnectionError):  # no un xml.etree.ElementTree.ParseError
            buscar("quijote")
 
 
@patch("huffman.gutenberg.requests.get")
class GutenbergDescargar(unittest.TestCase):
    def test_regresa_los_bytes_sin_modificar(self, get):
        contenido = "canción\r\n".encode("latin-1") + bytes(range(256))  # ni UTF-8 válido
        get.return_value = respuesta(contenido)
        get.return_value.text = "TEXTO-INCORRECTO"  # si el código usa .text en vez de .content, falla
        self.assertEqual(descargar(2000), contenido)
 
    def test_la_url_contiene_el_id(self, get):
        get.return_value = respuesta(b"contenido")
        descargar(2000)
        url, _, timeout = peticion(get)
        self.assertIn("gutenberg.org", url)
        self.assertIn("2000", url)
        self.assertIsNotNone(timeout)
 
    def test_libro_inexistente_es_valueerror(self, get):
        get.return_value = respuesta(b"", 404)
        with self.assertRaises(ValueError):
            descargar(99999999)
 
    def test_cuerpo_vacio_es_error_no_libro_vacio(self, get):
        get.return_value = respuesta(b"", 200)
        with self.assertRaises(ValueError):
            descargar(2000)
 
    def test_id_invalido_no_hace_peticion(self, get):
        for id_malo in [-1, 0, "abc", None, 1.5]:
            with self.subTest(id=id_malo):
                with self.assertRaises(ValueError):
                    descargar(id_malo)
        get.assert_not_called()
 
    def test_fallas_de_red_son_connectionerror(self, get):
        casos = {
            "HTTP 500": dict(return_value=respuesta(b"", 500)),
            "timeout": dict(side_effect=requests.exceptions.Timeout()),
            "sin conexión": dict(side_effect=requests.exceptions.ConnectionError()),
        }
        for nombre, config in casos.items():
            with self.subTest(nombre):
                get.reset_mock(return_value=True, side_effect=True)
                get.configure_mock(**config)
                with self.assertRaises(ConnectionError):
                    descargar(2000)
 
 
class GutenbergIntegracion(unittest.TestCase):
    """El bloque nuevo encaja en el flujo: descargar -> comprimir -> descomprimir."""
 
    @patch("huffman.gutenberg.requests.get")
    def test_libro_descargado_sobrevive_ida_y_vuelta(self, get):
        libro = ("¡Hola, ñandú!\r\nCanción de Adiós.\r\n" * 50).encode("utf-8")
        get.return_value = respuesta(libro)
        recuperado, ok = descomprimir(comprimir(descargar(2000), "libro.txt"))
        self.assertEqual(recuperado, libro)
        self.assertTrue(ok)
 
 
@unittest.skipUnless(os.environ.get("HUFFMAN_ONLINE") == "1",
                     "Prueba en línea: activar con HUFFMAN_ONLINE=1")
class GutenbergEnLinea(unittest.TestCase):
    """Contra Gutenberg de verdad: detecta cambios de formato que los mocks no ven."""
 
    def test_buscar_por_titulo(self):
        ids = [libro["id"] for libro in buscar("frankenstein")]
        self.assertIn(84, ids)
 
    def test_buscar_por_autor(self):
        self.assertTrue(buscar("shelley", "autor"))
 
    def test_buscar_por_tema(self):
        self.assertTrue(buscar("science fiction", "tema"))
 
    def test_buscar_sin_resultados(self):
        self.assertEqual(buscar("zzzqqqxxxyyy"), [])
 
    def test_descargar_libro_pequeno_y_comprimirlo(self):
        datos = descargar(1)  # The Declaration of Independence (~8 KB)
        self.assertIn(b"Declaration of Independence", datos)
        recuperado, ok = descomprimir(comprimir(datos, "1.txt"))
        self.assertEqual(recuperado, datos)
        self.assertTrue(ok)
 
    def test_libro_inexistente(self):
        with self.assertRaises(ValueError):
            descargar(99999999)
        
if __name__ == "__main__":
    unittest.main()
