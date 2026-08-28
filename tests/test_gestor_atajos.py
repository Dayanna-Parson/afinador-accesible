"""Pruebas del gestor de atajos de teclado configurables."""

import os
import tempfile
import unittest
from unittest.mock import patch

from app import gestor_atajos


class PruebasGestorAtajos(unittest.TestCase):
    def _rutas_temporales(self, carpeta):
        return {
            "_RUTA_DEFAULTS": os.path.join(carpeta, "teclas_predeterminadas.json"),
            "_RUTA_USUARIO": os.path.join(carpeta, "teclas_usuario.json"),
            "RUTA_CONFIGURACIONES": carpeta,
        }

    def test_cargar_atajos_sin_overrides_devuelve_los_valores_de_fabrica(self):
        with tempfile.TemporaryDirectory() as carpeta:
            with patch.multiple(gestor_atajos, **self._rutas_temporales(carpeta)):
                atajos = gestor_atajos.cargar_atajos()
                self.assertEqual(atajos["alternar_escucha"]["tecla"], "E")
                self.assertEqual(atajos["alternar_escucha"]["modificador"], "Ctrl")

    def test_guardar_override_no_toca_los_defaults(self):
        with tempfile.TemporaryDirectory() as carpeta:
            with patch.multiple(gestor_atajos, **self._rutas_temporales(carpeta)):
                gestor_atajos.guardar_atajo_usuario("alternar_escucha", "Ctrl+Shift", "L")
                atajos = gestor_atajos.cargar_atajos()
                self.assertEqual(atajos["alternar_escucha"]["modificador"], "Ctrl+Shift")
                self.assertEqual(atajos["alternar_escucha"]["tecla"], "L")

                defaults = gestor_atajos.cargar_defaults()
                self.assertEqual(defaults["alternar_escucha"]["modificador"], "Ctrl")
                self.assertEqual(defaults["alternar_escucha"]["tecla"], "E")

    def test_eliminar_override_restaura_el_valor_de_fabrica(self):
        with tempfile.TemporaryDirectory() as carpeta:
            with patch.multiple(gestor_atajos, **self._rutas_temporales(carpeta)):
                gestor_atajos.guardar_atajo_usuario("reproducir_referencia", "Ctrl+Alt", "T")
                gestor_atajos.eliminar_atajo_usuario("reproducir_referencia")
                atajos = gestor_atajos.cargar_atajos()
                self.assertEqual(atajos["reproducir_referencia"]["modificador"], "Ctrl")
                self.assertEqual(atajos["reproducir_referencia"]["tecla"], "P")

    def test_restablecer_todos_borra_todos_los_overrides(self):
        with tempfile.TemporaryDirectory() as carpeta:
            with patch.multiple(gestor_atajos, **self._rutas_temporales(carpeta)):
                gestor_atajos.guardar_atajo_usuario("alternar_escucha", "Ctrl+Shift", "L")
                gestor_atajos.guardar_atajo_usuario("deshacer_retoque", "Alt", "Z")
                gestor_atajos.restablecer_todos()
                atajos = gestor_atajos.cargar_atajos()
                self.assertEqual(atajos["alternar_escucha"]["tecla"], "E")
                self.assertEqual(atajos["deshacer_retoque"]["tecla"], "Z")
                self.assertEqual(atajos["deshacer_retoque"]["modificador"], "Ctrl+Shift")

    def test_una_version_nueva_anade_atajos_que_faltaban_sin_perder_overrides(self):
        with tempfile.TemporaryDirectory() as carpeta:
            rutas = self._rutas_temporales(carpeta)
            with patch.multiple(gestor_atajos, **rutas):
                gestor_atajos.guardar_atajo_usuario("alternar_escucha", "Ctrl+Shift", "L")
                gestor_atajos.cargar_atajos()  # crea teclas_predeterminadas.json si no existía
                # Simula una instalación con teclas_predeterminadas.json ya creado,
                # de una versión anterior a la que añadió "repetir_instruccion".
                import json
                with open(rutas["_RUTA_DEFAULTS"], "r", encoding="utf-8") as archivo:
                    defaults = json.load(archivo)
                del defaults["repetir_instruccion"]
                with open(rutas["_RUTA_DEFAULTS"], "w", encoding="utf-8") as archivo:
                    json.dump(defaults, archivo)

                atajos = gestor_atajos.cargar_atajos()
                self.assertIn("repetir_instruccion", atajos)
                self.assertEqual(atajos["alternar_escucha"]["tecla"], "L")

    def test_texto_atajo_formatea_modificador_y_tecla(self):
        self.assertEqual(
            gestor_atajos.texto_atajo({"modificador": "Ctrl+Shift", "tecla": "P"}), "Ctrl+Shift+P"
        )
        self.assertEqual(gestor_atajos.texto_atajo({"modificador": "", "tecla": "F1"}), "F1")
        self.assertEqual(gestor_atajos.texto_atajo({"modificador": "", "tecla": ""}), "(sin asignar)")


if __name__ == "__main__":
    unittest.main()
