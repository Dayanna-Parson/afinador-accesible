"""Pruebas de persistencia recuperable de ajustes."""

import os
import tempfile
import unittest
from unittest.mock import patch

from app import gestor_ajustes


class PruebasPersistenciaAjustes(unittest.TestCase):
    def test_crea_copia_de_la_version_anterior_solo_al_cambiar(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta_ajustes = os.path.join(carpeta, "ajustes.json")
            ruta_copias = os.path.join(carpeta, "copias_ajustes")
            with patch.object(gestor_ajustes, "RUTA_CONFIGURACIONES", carpeta), \
                 patch.object(gestor_ajustes, "RUTA_AJUSTES", ruta_ajustes), \
                 patch.object(gestor_ajustes, "RUTA_COPIAS_AJUSTES", ruta_copias):
                gestor_ajustes.guardar_ajustes({"instrumento": "Lira"})
                self.assertFalse(os.path.exists(ruta_copias))

                gestor_ajustes.guardar_ajustes({"instrumento": "Guitarra"})
                copias = os.listdir(ruta_copias)
                self.assertEqual(len(copias), 1)

                gestor_ajustes.guardar_ajustes({"instrumento": "Guitarra"})
                self.assertEqual(os.listdir(ruta_copias), copias)
