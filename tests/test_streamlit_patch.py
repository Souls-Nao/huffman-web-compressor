"""Pruebas del parche de Streamlit: proxy/respaldo de Gutenberg y ayudas visuales de app.py.

Ejecutar desde la raíz: python -m unittest -v   (todo es sin red).
"""

import os
import unittest
from unittest.mock import Mock, patch

import requests

from huffman import gutenberg, visual
from huffman.arbol import construir_arbol
from huffman.bits import empaquetar
from huffman.codigos import generar_codigos
from huffman.frecuencias import contar_frecuencias

OPDS = (b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><entry>'
        b"<id>https://www.gutenberg.org/ebooks/2000.opds</id><title>Quijote</title>"
        b"<content>Cervantes</content></entry></feed>")
WORKER = "https://huffman-gutenberg.ejemplo.workers.dev"


def respuesta(contenido=b"", status=200):
    r = Mock()
    r.status_code = status
    r.content = contenido
    if status >= 400:
        r.raise_for_status.side_effect = requests.HTTPError(f"HTTP {status}", response=r)
    return r


def urls(get):
    return [llamada.args[0] for llamada in get.call_args_list]


class LimpiaConfiguracion(unittest.TestCase):
    def setUp(self):
        gutenberg.configurar()
        for variable in ("GUTENBERG_PROXY_URL", "GUTENBERG_HTTP_PROXY"):
            os.environ.pop(variable, None)

    tearDown = setUp


@patch("huffman.gutenberg.requests.get")
class ProxyInverso(LimpiaConfiguracion):
    def test_sin_configurar_va_directo_a_gutenberg(self, get):
        get.return_value = respuesta(OPDS)
        gutenberg.buscar("quijote")
        self.assertEqual(urls(get), ["https://www.gutenberg.org/ebooks/search.opds/"])
        self.assertNotIn("proxies", get.call_args.kwargs)

    def test_con_proxy_usa_la_misma_ruta_en_el_worker(self, get):
        gutenberg.configurar(proxy_url=WORKER + "/")  # la barra final sobra y se quita
        get.return_value = respuesta(OPDS)
        gutenberg.buscar("quijote")
        self.assertEqual(urls(get), [WORKER + "/ebooks/search.opds/"])
        get.return_value = respuesta(b"texto del libro")
        gutenberg.descargar(2000)
        self.assertEqual(urls(get)[-1], WORKER + "/cache/epub/2000/pg2000.txt")

    def test_si_el_proxy_falla_se_prueba_gutenberg_directo(self, get):
        gutenberg.configurar(proxy_url=WORKER)
        get.side_effect = [requests.exceptions.ConnectionError(), respuesta(OPDS)]
        self.assertEqual(gutenberg.buscar("quijote")[0]["id"], 2000)
        self.assertEqual(urls(get), [WORKER + "/ebooks/search.opds/", "https://www.gutenberg.org/ebooks/search.opds/"])

    def test_si_todo_falla_es_connectionerror(self, get):
        gutenberg.configurar(proxy_url=WORKER)
        get.side_effect = requests.exceptions.Timeout()
        with self.assertRaises(ConnectionError):
            gutenberg.descargar(2000)
        self.assertEqual(get.call_count, 2)

    def test_404_no_se_reintenta_en_otro_origen(self, get):
        gutenberg.configurar(proxy_url=WORKER)
        get.return_value = respuesta(b"", 404)
        with self.assertRaises(ValueError):
            gutenberg.descargar(99999999)
        self.assertEqual(get.call_count, 1)

    def test_variable_de_entorno(self, get):
        os.environ["GUTENBERG_PROXY_URL"] = WORKER
        get.return_value = respuesta(OPDS)
        gutenberg.buscar("quijote")
        self.assertTrue(urls(get)[0].startswith(WORKER))

    def test_configurar_pisa_al_entorno_y_vacio_lo_desactiva(self, get):
        os.environ["GUTENBERG_PROXY_URL"] = "https://otro.ejemplo"
        gutenberg.configurar(proxy_url=WORKER)
        get.return_value = respuesta(OPDS)
        gutenberg.buscar("quijote")
        self.assertTrue(urls(get)[0].startswith(WORKER))
        del os.environ["GUTENBERG_PROXY_URL"]
        gutenberg.configurar(proxy_url="")
        gutenberg.buscar("quijote")
        self.assertTrue(urls(get)[-1].startswith("https://www.gutenberg.org"))


@patch("huffman.gutenberg.requests.get")
class ProxyHttp(LimpiaConfiguracion):
    def test_el_proxy_http_se_pasa_a_requests(self, get):
        gutenberg.configurar(proxy_http="http://usuario:clave@proxy.ejemplo:8080")
        get.return_value = respuesta(OPDS)
        gutenberg.buscar("quijote")
        esperado = {"http": "http://usuario:clave@proxy.ejemplo:8080", "https": "http://usuario:clave@proxy.ejemplo:8080"}
        self.assertEqual(get.call_args.kwargs["proxies"], esperado)

    def test_describir_conexion_no_muestra_claves(self, get):
        gutenberg.configurar(proxy_url=WORKER, proxy_http="http://usuario:clave@proxy.ejemplo:8080")
        texto = gutenberg.describir_conexion()
        self.assertNotIn("clave", texto)
        self.assertNotIn("proxy.ejemplo", texto)
        self.assertIn("proxy HTTP", texto)


@patch("huffman.gutenberg.requests.get")
class Mantenimiento(LimpiaConfiguracion):
    def test_503_avisa_que_puede_estar_en_mantenimiento(self, get):
        get.return_value = respuesta(b"", 503)
        with self.assertRaisesRegex(ConnectionError, "mantenimiento"):
            gutenberg.buscar("quijote")

    def test_pagina_html_con_200_no_se_toma_por_catalogo_ni_libro(self, get):
        pagina = b"  <!DOCTYPE html><html><body>Site under maintenance</body></html>"
        get.return_value = respuesta(pagina)
        with self.assertRaisesRegex(ConnectionError, "mantenimiento"):
            gutenberg.buscar("quijote")
        with self.assertRaisesRegex(ConnectionError, "mantenimiento"):
            gutenberg.descargar(2000)

    def test_un_libro_real_no_se_confunde_con_html(self, get):
        libro = b"The Project Gutenberg eBook of Don Quijote <html> aparece en el texto"
        get.return_value = respuesta(libro)
        self.assertEqual(gutenberg.descargar(2000), libro)


class PasosYArbol(unittest.TestCase):
    def setUp(self):
        self.frecuencias = contar_frecuencias(b"abracadabra")
        self.vista = visual.pasos_construccion(self.frecuencias)

    def test_cola_inicial_ordenada_por_frecuencia(self):
        self.assertEqual([visual.etiqueta_nodo(n) for n in self.vista["inicial"]], ["c:1", "d:1", "b:2", "r:2", "a:5"])

    def test_cada_paso_une_los_dos_menores_y_la_cola_queda_ordenada(self):
        for paso in self.vista["pasos"]:
            self.assertEqual(paso["padre"].frecuencia, paso["izquierdo"].frecuencia + paso["derecho"].frecuencia)
            frecs = [n.frecuencia for n in paso["cola"]]
            self.assertEqual(frecs, sorted(frecs))
        self.assertEqual(len(self.vista["pasos"]), len(self.frecuencias) - 1)
        self.assertIs(self.vista["pasos"][-1]["cola"][0], self.vista["raiz"])

    def test_es_el_mismo_arbol_que_se_comprime(self):
        self.assertEqual(generar_codigos(self.vista["raiz"]), generar_codigos(construir_arbol(self.frecuencias)))

    def test_textos_de_los_pasos(self):
        self.assertIn("Cola inicial: 5 hojas", visual.texto_paso(0, self.vista))
        self.assertIn("salen c:1 y d:1", visual.texto_paso(1, self.vista))
        self.assertIn("1 + 1 = 2", visual.texto_paso(1, self.vista))
        self.assertIn("El árbol está completo", visual.texto_paso(4, self.vista))

    def test_un_solo_simbolo_no_tiene_pasos(self):
        vista = visual.pasos_construccion(contar_frecuencias(b"aaaa"))
        self.assertEqual(vista["pasos"], [])
        self.assertIn("Un solo símbolo", visual.texto_paso(0, vista))

    def test_vacio(self):
        self.assertEqual(visual.pasos_construccion({})["pasos"], [])

    def test_dot_tiene_un_nodo_por_nodo_y_resalta_el_camino(self):
        raiz = self.vista["raiz"]
        dot = visual.arbol_dot(raiz, visual.camino_a_simbolo(raiz, ord("b")))
        self.assertEqual(dot.count("shape="), 2 * len(self.frecuencias) - 1)
        # b = "110": raíz, nodo 6, nodo 4 y la hoja b -> 4 nodos y 3 aristas resaltadas.
        self.assertEqual(dot.count("#ffb3b3"), 4)
        self.assertEqual(dot.count("penwidth"), 3)
        self.assertEqual(dot.count("{"), dot.count("}"))

    def test_dot_de_un_bosque_y_nodo_nuevo(self):
        paso = self.vista["pasos"][0]
        dot = visual.arbol_dot(paso["cola"], nuevo=paso["padre"])
        self.assertEqual(dot.count("#fff3b0"), 1)

    def test_camino_de_simbolo_inexistente_es_vacio(self):
        self.assertEqual(visual.camino_a_simbolo(self.vista["raiz"], 0), (set(), set()))

    def test_simbolos_cortos(self):
        self.assertEqual([visual.simbolo_corto(s) for s in (97, 32, 10, 195)], ["a", "␣", "\\n", "C3"])


class Inspector(unittest.TestCase):
    def setUp(self):
        self.texto = b"abracadabra"
        self.frecuencias = contar_frecuencias(self.texto)
        self.raiz = construir_arbol(self.frecuencias)
        self.codigos = generar_codigos(self.raiz)
        bits = "".join(self.codigos[b] for b in self.texto)
        self.datos, _ = empaquetar(bits)
        self.total_bits = len(bits)

    def test_tabla_bits_compara_con_8_bits(self):
        filas = {f["Byte"]: f for f in visual.tabla_bits(self.frecuencias, self.codigos)}
        self.assertEqual(filas[97]["Bits totales"], 5)       # 5 'a' x 1 bit
        self.assertEqual(filas[97]["Bits originales"], 40)   # 5 'a' x 8 bits
        self.assertEqual(filas[97]["Ahorro (bits)"], 35)
        self.assertEqual(sum(f["Bits totales"] for f in filas.values()), self.total_bits)

    def test_segmentar_bits_recupera_el_texto(self):
        piezas = visual.segmentar_bits(self.datos, self.total_bits, self.raiz, maximo=100)
        self.assertEqual(bytes(p["Byte"] for p in piezas), self.texto)
        self.assertEqual("".join(p["Bits"] for p in piezas), "".join(self.codigos[b] for b in self.texto))

    def test_segmentar_respeta_el_maximo_y_el_relleno(self):
        self.assertEqual(len(visual.segmentar_bits(self.datos, self.total_bits, self.raiz, maximo=3)), 3)
        # 23 bits en 3 bytes: el relleno del último byte nunca se lee como un símbolo.
        self.assertEqual(len(visual.segmentar_bits(self.datos, self.total_bits, self.raiz, maximo=100)), len(self.texto))

    def test_segmentar_un_solo_simbolo(self):
        raiz = construir_arbol(contar_frecuencias(b"aaaa"))
        piezas = visual.segmentar_bits(b"\x00", 4, raiz, maximo=24)
        self.assertEqual([p["Byte"] for p in piezas], [97] * 4)

    def test_bytes_muestra_recorta_el_ultimo_byte(self):
        filas = visual.bytes_muestra(self.datos, self.total_bits)
        self.assertEqual(len(filas), 3)
        self.assertEqual(filas[0], {"Byte": 0, "Binario": "01101110", "Hex": "6E"})
        self.assertEqual(len(filas[-1]["Binario"]), self.total_bits - 16)


if __name__ == "__main__":
    unittest.main()
