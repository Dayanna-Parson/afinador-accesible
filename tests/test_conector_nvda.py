"""Pruebas de la elección de salida de voz y de la detección de «está hablando»."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app import conector_nvda
from app.conector_nvda import SALIDA_LECTOR, SALIDA_VOZ_PROPIA, AnunciadorNVDA


class _VozSapiFalsa:
    """Imita la salida SAPI5 de accessible_output3 sin necesitar Windows."""

    def __init__(self):
        self.object = SimpleNamespace(Status=SimpleNamespace(RunningState=1))
        self.textos = []
        self.voz = "Voz A"

    def list_voices(self):
        return ["Voz A", "Voz B"]

    def get_voice(self):
        return self.voz

    def set_voice(self, nombre):
        self.voz = nombre

    def set_rate(self, valor):
        self.velocidad = valor

    def set_volume(self, valor):
        self.volumen = valor

    def speak(self, texto, interrupt=False):
        self.textos.append((texto, interrupt))


class _Reloj:
    def __init__(self):
        self.ahora = 1000.0

    def __call__(self):
        return self.ahora


class PruebasConectorNVDA(unittest.TestCase):
    def setUp(self):
        self.reloj = _Reloj()
        parche = patch.object(conector_nvda.time, "monotonic", self.reloj)
        parche.start()
        self.addCleanup(parche.stop)

    def test_sin_voz_propia_disponible_se_queda_en_el_lector(self):
        with patch.object(conector_nvda, "_crear_voz_propia", return_value=None):
            anunciador = AnunciadorNVDA()
            self.assertEqual(anunciador.configurar_salida(SALIDA_VOZ_PROPIA), SALIDA_LECTOR)

    def test_voz_propia_aplica_voz_velocidad_y_volumen(self):
        voz = _VozSapiFalsa()
        with patch.object(conector_nvda, "_crear_voz_propia", return_value=voz):
            anunciador = AnunciadorNVDA()
            activo = anunciador.configurar_salida(SALIDA_VOZ_PROPIA, "Voz B", velocidad=3, volumen=80)
        self.assertEqual(activo, SALIDA_VOZ_PROPIA)
        self.assertEqual((voz.voz, voz.velocidad, voz.volumen), ("Voz B", 3, 80))
        anunciador.hablar("Afinada")
        self.assertEqual(voz.textos, [("Afinada", False)])

    def test_con_el_lector_se_estima_la_duracion_por_la_longitud(self):
        anunciador = AnunciadorNVDA()
        anunciador.hablar("Sube bastante")
        self.assertTrue(anunciador.esta_hablando())
        self.reloj.ahora += 30.0
        self.assertFalse(anunciador.esta_hablando())

    def test_con_voz_propia_se_consulta_el_estado_real_de_sapi(self):
        voz = _VozSapiFalsa()
        with patch.object(conector_nvda, "_crear_voz_propia", return_value=voz):
            anunciador = AnunciadorNVDA()
            anunciador.configurar_salida(SALIDA_VOZ_PROPIA)
        anunciador.hablar("Una indicación muy larga que la estimación tardaría en dar por terminada")
        voz.object.Status.RunningState = 2
        self.reloj.ahora += 0.5
        self.assertTrue(anunciador.esta_hablando())
        voz.object.Status.RunningState = 1
        self.reloj.ahora += 0.1
        self.assertTrue(anunciador.esta_hablando(), "el margen de reverberación aún no ha pasado")
        self.reloj.ahora += 1.0
        self.assertFalse(anunciador.esta_hablando(), "SAPI ya calló: no hay que esperar a la estimación")

    def test_instrucciones_con_voz_propia_sustituyen_a_la_anterior(self):
        voz = _VozSapiFalsa()
        with patch.object(conector_nvda, "_crear_voz_propia", return_value=voz):
            anunciador = AnunciadorNVDA()
            anunciador.configurar_salida(SALIDA_VOZ_PROPIA)
        anunciador.procesar_instruccion("Sube bastante")
        self.reloj.ahora += 0.5
        anunciador.procesar_instruccion("Sube bastante")
        self.assertEqual(voz.textos, [("Sube bastante", True)])


if __name__ == "__main__":
    unittest.main()
