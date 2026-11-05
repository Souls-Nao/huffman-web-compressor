"""Bloque 11 — Pruebas unitarias. Ejecutar desde la raíz: python -m unittest -v"""

import unittest

from huffman.arbol import construir_arbol
from huffman.bits import desempaquetar, empaquetar
from huffman.codigos import generar_codigos
from huffman.compresor import comprimir, descomprimir, metricas
from huffman.formato import leer_hfa
from huffman.frecuencias import contar_frecuencias


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


if __name__ == "__main__":
    unittest.main()
