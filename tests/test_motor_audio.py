"""Pruebas del algoritmo YIN y la lógica de notas/instrucciones de motor_audio.py.

Las señales de prueba no son senoidales puras: simulan una cuerda pulsada real,
con armónicos, envolvente de decaimiento y ruido de fondo, porque ese es
precisamente el caso donde YIN puede fallar (saltos de octava) si la
implementación no es robusta.
"""

import unittest

import numpy as np

from app.motor_audio import (
    calcular_instruccion,
    estimar_frecuencia_yin,
    frecuencia_a_nota,
    GeneradorTonos,
    nota_a_frecuencia,
)

TASA_MUESTREO_PRUEBA = 44100


def generar_cuerda_pulsada(frecuencia, duracion, tasa_muestreo=TASA_MUESTREO_PRUEBA,
                            num_armonicos=6, proporcion_ruido=0.02, semilla=0):
    """Sintetiza una señal parecida a una cuerda pulsada real: fundamental + armónicos
    con amplitud decreciente, envolvente de decaimiento exponencial y ruido de fondo."""
    generador_aleatorio = np.random.default_rng(semilla)
    muestras = int(tasa_muestreo * duracion)
    tiempo = np.linspace(0, duracion, muestras, endpoint=False)

    señal = np.zeros(muestras)
    for indice_armonico in range(1, num_armonicos + 1):
        amplitud = 1.0 / indice_armonico
        fase = generador_aleatorio.uniform(0, 2 * np.pi)
        señal += amplitud * np.sin(2 * np.pi * frecuencia * indice_armonico * tiempo + fase)

    envolvente = np.exp(-tiempo * 1.5)
    señal *= envolvente

    señal /= np.max(np.abs(señal))
    ruido = generador_aleatorio.normal(0, proporcion_ruido, muestras)
    return (señal * 0.8 + ruido).astype(np.float64)


class PruebasEstimacionYIN(unittest.TestCase):
    TOLERANCIA_CENTS = 15.0

    def _verificar_frecuencia(self, frecuencia_objetivo, nombre_caso):
        señal = generar_cuerda_pulsada(frecuencia_objetivo, duracion=0.15)
        frecuencia_estimada = estimar_frecuencia_yin(señal, TASA_MUESTREO_PRUEBA)
        self.assertIsNotNone(frecuencia_estimada, f"no se detectó frecuencia para {nombre_caso}")
        cents_error = 1200 * np.log2(frecuencia_estimada / frecuencia_objetivo)
        self.assertLessEqual(
            abs(cents_error), self.TOLERANCIA_CENTS,
            f"{nombre_caso}: error de {cents_error:.1f} cents (objetivo {frecuencia_objetivo:.2f} Hz, "
            f"estimado {frecuencia_estimada:.2f} Hz)",
        )

    def test_guitarra_seis_cuerdas(self):
        cuerdas = {
            "Mi2 (sexta)": nota_a_frecuencia(4, 2),
            "La2 (quinta)": nota_a_frecuencia(9, 2),
            "Re3 (cuarta)": nota_a_frecuencia(2, 3),
            "Sol3 (tercera)": nota_a_frecuencia(7, 3),
            "Si3 (segunda)": nota_a_frecuencia(11, 3),
            "Mi4 (primera)": nota_a_frecuencia(4, 4),
        }
        for nombre, frecuencia in cuerdas.items():
            with self.subTest(cuerda=nombre):
                self._verificar_frecuencia(frecuencia, nombre)

    def test_ukelele(self):
        cuerdas = {
            "Sol4": nota_a_frecuencia(7, 4),
            "Do4": nota_a_frecuencia(0, 4),
            "Mi4": nota_a_frecuencia(4, 4),
            "La4": nota_a_frecuencia(9, 4),
        }
        for nombre, frecuencia in cuerdas.items():
            with self.subTest(cuerda=nombre):
                self._verificar_frecuencia(frecuencia, nombre)

    def test_lira_aklot_extremos(self):
        cuerdas = {
            "Cuerda 1 (Sol3, la más grave)": nota_a_frecuencia(7, 3),
            "Cuerda 16 (La5, la más aguda)": nota_a_frecuencia(9, 5),
        }
        for nombre, frecuencia in cuerdas.items():
            with self.subTest(cuerda=nombre):
                self._verificar_frecuencia(frecuencia, nombre)

    def test_senal_silenciosa_no_devuelve_frecuencia_fiable(self):
        generador_aleatorio = np.random.default_rng(1)
        ruido_puro = generador_aleatorio.normal(0, 0.01, int(TASA_MUESTREO_PRUEBA * 0.15))
        frecuencia = estimar_frecuencia_yin(ruido_puro, TASA_MUESTREO_PRUEBA)
        # El ruido blanco puro no tiene periodicidad real: o no encuentra candidato,
        # o si encuentra uno espurio no debe coincidir con ninguna nota musical típica.
        if frecuencia is not None:
            self.assertTrue(frecuencia < 60.0 or frecuencia > 1500.0)


class PruebasConversionNotas(unittest.TestCase):
    def test_la4_es_440hz(self):
        self.assertAlmostEqual(nota_a_frecuencia(9, 4), 440.0, places=5)

    def test_ida_y_vuelta_frecuencia_nota(self):
        for indice in range(12):
            for octava in (2, 3, 4, 5):
                frecuencia = nota_a_frecuencia(indice, octava)
                resultado = frecuencia_a_nota(frecuencia)
                self.assertAlmostEqual(resultado["cents"], 0.0, places=3)

    def test_desviacion_en_cents(self):
        frecuencia_la4_desafinada = 440.0 * (2 ** (10 / 1200))  # 10 cents por encima de La4
        resultado = frecuencia_a_nota(frecuencia_la4_desafinada)
        self.assertEqual(resultado["nombre"], "La")
        self.assertEqual(resultado["octava"], 4)
        self.assertAlmostEqual(resultado["cents"], 10.0, places=2)


class PruebasCalculoInstruccion(unittest.TestCase):
    def test_afinada_dentro_del_margen(self):
        self.assertEqual(calcular_instruccion(0.0), "AFINADA")
        self.assertEqual(calcular_instruccion(4.9), "AFINADA")
        self.assertEqual(calcular_instruccion(-4.9), "AFINADA")

    def test_sube_poco_y_bastante(self):
        self.assertEqual(calcular_instruccion(10.0), "SUBE_POCO")
        self.assertEqual(calcular_instruccion(30.0), "SUBE_BASTANTE")

    def test_baja_poco_y_bastante(self):
        self.assertEqual(calcular_instruccion(-10.0), "BAJA_POCO")
        self.assertEqual(calcular_instruccion(-30.0), "BAJA_BASTANTE")

    def test_valor_none(self):
        self.assertIsNone(calcular_instruccion(None))


class _CapturadorDePrueba:
    def __init__(self):
        self.reanudaciones = 0

    def reanudar(self):
        self.reanudaciones += 1


class PruebasCoordinacionDeReproduccion(unittest.TestCase):
    def test_reproduccion_anterior_no_reanuda_la_captura_nueva(self):
        capturador = _CapturadorDePrueba()
        generador = GeneradorTonos(capturador=capturador)
        identificador_anterior = generador._iniciar_reproduccion()
        identificador_actual = generador._iniciar_reproduccion()

        generador._finalizar_reproduccion(identificador_anterior)
        self.assertEqual(capturador.reanudaciones, 0)

        generador._finalizar_reproduccion(identificador_actual)
        self.assertEqual(capturador.reanudaciones, 1)


if __name__ == "__main__":
    unittest.main()
