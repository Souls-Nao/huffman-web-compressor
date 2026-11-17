"""Pruebas de la interfaz de Streamlit sin Streamlit: HTML seguro, flujo, tamaño estimado e inspector."""

import unittest

from huffman import ui, visual
from huffman.compresor import comprimir
from huffman.formato import tamano_hfa
from huffman.frecuencias import contar_frecuencias
from huffman.inspector import PREFIJO_BYTES, vista_desde_hfa, vista_desde_texto

TEXTOS = [b"abracadabra", b"aaaaaaa", "¡Hola, ñandú! Adiós, canción.\r\n".encode() * 30, bytes(range(256)) * 2]


class TamanoEstimado(unittest.TestCase):
    def test_tamano_hfa_coincide_con_el_archivo_real(self):
        for datos in TEXTOS:
            for nombre in ("t.txt", "pg2000.txt", "ñandú.txt"):
                frecuencias = contar_frecuencias(datos)
                vista = vista_desde_texto(nombre, datos, frecuencias)
                self.assertEqual(vista["tamano_final"], len(comprimir(datos, nombre)), (nombre, len(datos)))
                self.assertEqual(vista["tamano_final"], tamano_hfa(nombre, len(frecuencias), vista["total_bits"]))


class VistasDelInspector(unittest.TestCase):
    def test_texto_actual_y_hfa_dan_los_mismos_bits(self):
        for datos in TEXTOS:
            hfa = comprimir(datos, "t.txt")
            actual = vista_desde_texto("t.txt", datos, contar_frecuencias(datos))
            archivo = vista_desde_hfa(hfa, "t.hfa")
            self.assertEqual(actual["total_bits"], archivo["total_bits"])
            self.assertEqual(actual["codigos"], archivo["codigos"])
            self.assertEqual(actual["tamano_final"], archivo["tamano_final"])
            # Los primeros bits de la muestra del texto son un prefijo de los del archivo.
            bytes_a, bits_a = actual["muestra"]
            bytes_h, _ = archivo["muestra"]
            self.assertEqual(bytes_a[: bits_a // 8], bytes_h[: bits_a // 8])

    def test_la_muestra_del_texto_se_limita(self):
        datos = b"abcd" * 1000
        _, bits = vista_desde_texto("t.txt", datos, contar_frecuencias(datos))["muestra"]
        self.assertEqual(bits, sum(len(c) for c in [vista_desde_texto("t.txt", datos, contar_frecuencias(datos))["codigos"][b] for b in datos[:PREFIJO_BYTES]]))

    def test_metadatos_solo_en_hfa(self):
        datos = TEXTOS[0]
        self.assertIsNone(vista_desde_texto("t.txt", datos, contar_frecuencias(datos))["metadatos"])
        metadatos = dict(vista_desde_hfa(comprimir(datos, "t.txt"), "t.hfa")["metadatos"])
        self.assertEqual(metadatos["Nombre original"], "t.txt")
        self.assertEqual(len(metadatos["SHA-256 del original"]), 64)

    def test_hfa_invalido(self):
        with self.assertRaises(ValueError):
            vista_desde_hfa(b"no es un hfa", "x.hfa")


class FlujoYHtml(unittest.TestCase):
    def test_el_actual_es_el_primero_que_falta(self):
        pasos = ui.estado_flujo({"entrada": True, "analizar": True, "huffman": True})
        self.assertEqual([p["hecho"] for p in pasos], [True, True, True, False, False, False, False])
        self.assertEqual([p["clave"] for p in pasos if p["actual"]], ["comprimir"])
        self.assertEqual([p["clave"] for p in ui.estado_flujo({}) if p["actual"]], ["entrada"])
        self.assertFalse(any(p["actual"] for p in ui.estado_flujo({c: True for c, _ in ui.PASOS_FLUJO})))

    def test_cabecera_marca_hechos(self):
        cabecera = ui.cabecera({"entrada": True})
        self.assertEqual(cabecera.count('class="hecho"'), 1)
        self.assertEqual(cabecera.count('class="actual"'), 1)
        self.assertEqual(cabecera.count("<li"), 7)

    def test_el_html_no_trae_saltos_de_linea(self):
        vista = visual.pasos_construccion(contar_frecuencias(b"abracadabra"))
        for fragmento in (ui.cabecera({}), ui.estilos().split("</style>")[1], ui.fichas_cola("t", vista["inicial"]),
                          ui.comparacion(100, 40, "a", "b"), ui.bits_html("0110"), ui.encabezado_seccion(1, "x")):
            self.assertNotIn("\n", fragmento)

    def test_escapa_lo_que_viene_del_texto(self):
        vista = visual.pasos_construccion(contar_frecuencias(b"<b>&\"'"))
        fichas = ui.fichas_cola("<img>", vista["inicial"])
        self.assertNotIn("<b>", fichas)
        self.assertNotIn("<img>", fichas)
        self.assertIn("&lt;", fichas)
        self.assertNotIn("<script", ui.palabras_html([{"Bits": "01", "Símbolo": "<script>"}]))
        self.assertNotIn("<x>", ui.encabezado_seccion(1, "<x>"))

    def test_bits_coloreados(self):
        self.assertEqual(ui.bits_html("01"), '<span class="hfa-codigo"><span class="hfa-b0">0</span><span class="hfa-b1">1</span></span>')
        self.assertEqual(ui.bits_html("0x1").count("hfa-b"), 2)  # lo que no es bit se ignora

    def test_fichas_marcan_la_union_y_resumen_la_cola_larga(self):
        vista = visual.pasos_construccion(contar_frecuencias(bytes(range(40))))
        nodos = vista["inicial"]
        fichas = ui.fichas_cola("Antes", nodos, {id(nodos[0]): "izquierdo", id(nodos[1]): "derecho"}, maximo=14)
        self.assertIn("sale · 0", fichas)
        self.assertIn("sale · 1", fichas)
        self.assertIn("… +26", fichas)
        self.assertIn("40 nodos", fichas)

    def test_comparacion_minimo_visible(self):
        self.assertIn("width:8.0%", ui.comparacion(1000, 1, "o", "f"))
        self.assertIn("width:100.0%", ui.comparacion(10, 50, "o", "f"))  # nunca se pasa del 100 %

    def test_bytes_y_palabras(self):
        self.assertEqual(ui.bytes_html([{"Byte": 0, "Binario": "0110", "Hex": "6E"}]).count("hfa-byte"), 2)  # contenedor + tarjeta
        self.assertIn("hfa-palabra", ui.palabras_html([{"Bits": "110", "Símbolo": "b", "Byte": 98}]))


if __name__ == "__main__":
    unittest.main()
