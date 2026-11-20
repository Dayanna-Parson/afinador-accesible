"""Pruebas del banco de sonidos grabados para el tono de referencia."""

import os
import tempfile
import unittest
import wave

import numpy as np

from app.motor_audio import estimar_frecuencia_yin, frecuencia_con_desplazamiento, nota_a_frecuencia
from app.muestras_referencia import RUTA_SONIDOS_REFERENCIA, BancoMuestrasReferencia, frecuencia_desde_nombre

TASA = 44100


def _escribir_cuerda_sintetica(ruta, frecuencia, segundos=3.0):
    tiempo = np.arange(int(TASA * segundos)) / TASA
    onda = sum(np.sin(2 * np.pi * frecuencia * armonico * tiempo) / armonico for armonico in (1, 2, 3))
    onda *= np.exp(-tiempo * 1.5)
    onda = (onda / np.max(np.abs(onda)) * 0.45 * 32767).astype("<i2")
    with wave.open(ruta, "wb") as archivo:
        archivo.setnchannels(1)
        archivo.setsampwidth(2)
        archivo.setframerate(TASA)
        archivo.writeframes(onda.tobytes())


def _frecuencia_medida(onda):
    return estimar_frecuencia_yin(onda[int(0.1 * TASA):int(0.3 * TASA)], TASA)


def _cents(medida, esperada):
    return 1200 * np.log2(medida / esperada)


class PruebasMuestrasReferencia(unittest.TestCase):
    def test_lee_la_frecuencia_del_nombre_con_coma_o_punto(self):
        self.assertAlmostEqual(frecuencia_desde_nombre("01_cuerda_1_Sol3_196,00Hz.wav"), 196.0)
        self.assertAlmostEqual(frecuencia_desde_nombre("guitarra_Mi2_82.41 Hz.wav"), 82.41)
        self.assertIsNone(frecuencia_desde_nombre("sin_frecuencia.wav"))

    def test_sin_sonidos_devuelve_none_para_recaer_en_el_sintetico(self):
        with tempfile.TemporaryDirectory() as carpeta:
            banco = BancoMuestrasReferencia(carpeta)
            self.assertFalse(banco.hay_muestras())
            self.assertIsNone(banco.generar_onda(440.0, 1.0, TASA, 0.45))

    def test_suena_exactamente_en_la_frecuencia_pedida_aunque_no_haya_sonido_de_esa_nota(self):
        with tempfile.TemporaryDirectory() as carpeta:
            _escribir_cuerda_sintetica(os.path.join(carpeta, "Sol3_196,00Hz.wav"), 196.0)
            _escribir_cuerda_sintetica(os.path.join(carpeta, "La4_440,00Hz.wav"), 440.0)
            banco = BancoMuestrasReferencia(carpeta)
            objetivos = {
                "Mi2 de guitarra": nota_a_frecuencia(4, 2),
                "Do4 de ukelele": nota_a_frecuencia(0, 4),
                "La4 con un cuarto de tono": frecuencia_con_desplazamiento(9, 4, 1),
                "La4 a 442": 442.0,
            }
            for descripcion, frecuencia in objetivos.items():
                onda = banco.generar_onda(frecuencia, 1.0, TASA, 0.45)
                self.assertIsNotNone(onda, descripcion)
                self.assertLess(abs(_cents(_frecuencia_medida(onda), frecuencia)), 3.0, descripcion)
                self.assertAlmostEqual(float(np.max(np.abs(onda))), 0.45, places=2)

    def test_la_subcarpeta_del_instrumento_tiene_prioridad(self):
        with tempfile.TemporaryDirectory() as carpeta:
            _escribir_cuerda_sintetica(os.path.join(carpeta, "general_440,00Hz.wav"), 440.0)
            os.makedirs(os.path.join(carpeta, "guitarra"))
            _escribir_cuerda_sintetica(os.path.join(carpeta, "guitarra", "Mi2_82,41Hz.wav"), 82.41)
            banco = BancoMuestrasReferencia(carpeta)
            self.assertEqual(banco._candidatos("guitarra")[0][0], 82.41)
            self.assertEqual(banco._candidatos("ukelele")[0][0], 440.0)

    @unittest.skipUnless(os.path.isdir(RUTA_SONIDOS_REFERENCIA), "no hay sonidos de referencia en el proyecto")
    def test_los_sonidos_del_proyecto_sirven_para_las_cuerdas_de_guitarra(self):
        banco = BancoMuestrasReferencia()
        for indice_nota, octava in ((4, 2), (9, 2), (2, 3), (7, 3), (11, 3), (4, 4)):
            frecuencia = nota_a_frecuencia(indice_nota, octava)
            onda = banco.generar_onda(frecuencia, 2.0, TASA, 0.45)
            self.assertIsNotNone(onda)
            self.assertLess(abs(_cents(_frecuencia_medida(onda), frecuencia)), 3.0)


if __name__ == "__main__":
    unittest.main()
