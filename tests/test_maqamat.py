"""Pruebas de coherencia de las afinaciones de lira."""

import math
import unittest

from app.interfaz_gui import ESCALAS_POR_INSTRUMENTO, NOMBRE_LIRA, PRESETS_INSTRUMENTO
from app.motor_audio import frecuencia_con_desplazamiento


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
