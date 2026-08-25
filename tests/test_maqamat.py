"""Pruebas de coherencia de las afinaciones de lira."""

import math
import unittest

from app.interfaz.ventana_principal import ESCALAS_POR_INSTRUMENTO, NOMBRE_LIRA, PRESETS_INSTRUMENTO
from app.motor_audio import frecuencia_con_desplazamiento
from app.afinaciones_maqam_lira import (
    AFINACIONES_LIRA_MAQAM_24EDO,
    FAMILIAS_MAQAM_LIRA,
    NOMBRE_AFINACION_FABRICA_LIRA,
    NOMBRE_AFINACION_PERSONALIZADA_LIRA,
    REFERENCIAS_GRADOS_MAQAM_24EDO,
    calcular_retoques_referencia_lira,
)


class PruebasMaqamatLira(unittest.TestCase):
    """Evitan que un cálculo de maqam convierta dos cuerdas consecutivas en la misma nota."""

    def test_los_maqamat_no_duplican_cuerdas_consecutivas(self):
        cuerdas = PRESETS_INSTRUMENTO[NOMBRE_LIRA]
        for nombre_maqam, desplazamientos in ESCALAS_POR_INSTRUMENTO[NOMBRE_LIRA].items():
            frecuencias = [
                frecuencia_con_desplazamiento(indice_nota, octava, desplazamientos.get(nombre_cuerda, 0))
                for nombre_cuerda, indice_nota, octava in cuerdas
            ]
            for posicion in range(len(frecuencias) - 1):
                diferencia_cents = 1200 * math.log2(frecuencias[posicion + 1] / frecuencias[posicion])
                self.assertGreater(
                    diferencia_cents,
                    1.0,
                    "{} duplica {} y {}".format(
                        nombre_maqam, cuerdas[posicion][0], cuerdas[posicion + 1][0]
                    ),
                )

    def test_afinacion_de_fabrica_no_tiene_ningun_retoque(self):
        self.assertEqual(AFINACIONES_LIRA_MAQAM_24EDO[NOMBRE_AFINACION_FABRICA_LIRA], {})

    def test_cada_maqam_pertenece_a_una_sola_familia(self):
        maqamat_ordenados = [nombre for familia in FAMILIAS_MAQAM_LIRA.values() for nombre in familia]
        maqamat_definidos = set(AFINACIONES_LIRA_MAQAM_24EDO) - {
            NOMBRE_AFINACION_FABRICA_LIRA,
            NOMBRE_AFINACION_PERSONALIZADA_LIRA,
        }
        self.assertEqual(set(maqamat_ordenados), maqamat_definidos)
        self.assertEqual(len(maqamat_ordenados), len(set(maqamat_ordenados)))

    def test_cada_afinacion_coincide_con_sus_siete_grados_de_referencia(self):
        cuerdas = PRESETS_INSTRUMENTO[NOMBRE_LIRA]
        for nombre_maqam, (tonica, cents_tonica, grados) in REFERENCIAS_GRADOS_MAQAM_24EDO.items():
            with self.subTest(maqam=nombre_maqam):
                esperado = calcular_retoques_referencia_lira(cuerdas, tonica, cents_tonica, grados)
                self.assertEqual(AFINACIONES_LIRA_MAQAM_24EDO[nombre_maqam], esperado)
