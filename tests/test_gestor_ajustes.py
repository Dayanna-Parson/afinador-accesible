"""Pruebas de persistencia recuperable de ajustes."""

import os
import tempfile
import unittest
from unittest.mock import patch
import json

from app import gestor_ajustes


class PruebasPersistenciaAjustes(unittest.TestCase):
    def _rutas_temporales(self, carpeta):
        return {
            "RUTA_CONFIGURACIONES": carpeta,
            "RUTA_AJUSTES_LEGADOS": os.path.join(carpeta, "ajustes.json"),
            "RUTA_CONFIGURACION_AUDIO": os.path.join(carpeta, "configuracion_audio.json"),
            "RUTA_AJUSTES_AFINACION": os.path.join(carpeta, "ajustes_afinacion.json"),
            "RUTA_COPIAS_CONFIGURACION_AUDIO": os.path.join(carpeta, "copias_configuracion_audio"),
            "RUTA_COPIAS_AJUSTES_AFINACION": os.path.join(carpeta, "copias_ajustes_afinacion"),
        }

    def test_separa_y_copia_solo_el_tipo_que_cambia(self):
        with tempfile.TemporaryDirectory() as carpeta:
            rutas = self._rutas_temporales(carpeta)
            with patch.multiple(gestor_ajustes, **rutas):
                gestor_ajustes.guardar_ajustes({"instrumento": "Lira", "ganancia": 1.0})
                self.assertTrue(os.path.isfile(rutas["RUTA_CONFIGURACION_AUDIO"]))
                self.assertTrue(os.path.isfile(rutas["RUTA_AJUSTES_AFINACION"]))

                gestor_ajustes.guardar_ajustes({"instrumento": "Guitarra", "ganancia": 1.0})
                self.assertEqual(len(os.listdir(rutas["RUTA_COPIAS_AJUSTES_AFINACION"])), 1)
                self.assertFalse(os.path.exists(rutas["RUTA_COPIAS_CONFIGURACION_AUDIO"]))

    def test_migra_el_archivo_antiguo_sin_borrarlo(self):
        with tempfile.TemporaryDirectory() as carpeta:
            rutas = self._rutas_temporales(carpeta)
            with open(rutas["RUTA_AJUSTES_LEGADOS"], "w", encoding="utf-8") as archivo:
                json.dump({"instrumento": "Lira", "ganancia": 1.4, "escala": "Maqam Rast (sobre Sol)"}, archivo)
            with patch.multiple(gestor_ajustes, **rutas):
                datos = gestor_ajustes.cargar_ajustes()
                self.assertEqual(datos["instrumento"], "Lira")
                self.assertEqual(datos["ganancia"], 1.4)
                self.assertTrue(os.path.isfile(rutas["RUTA_AJUSTES_LEGADOS"]))
                self.assertTrue(os.path.isfile(rutas["RUTA_CONFIGURACION_AUDIO"]))
                self.assertTrue(os.path.isfile(rutas["RUTA_AJUSTES_AFINACION"]))
