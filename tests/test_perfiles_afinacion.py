"""Pruebas de persistencia y migración de perfiles de afinación."""

import unittest

from app.perfiles_afinacion import guardar_perfil, migrar_perfiles, nombres_perfiles


class PruebasPerfilesAfinacion(unittest.TestCase):
    def test_migra_las_afinaciones_antiguas_sin_perderlas(self):
        ajustes = {"afinaciones_guardadas_lira": {"Mi rast": {"escala_base": "Rast"}}}
        perfiles = migrar_perfiles(ajustes, "Lira")
        self.assertEqual(perfiles["Lira"]["Mi rast"]["escala_base"], "Rast")

    def test_los_perfiles_quedan_separados_por_instrumento(self):
        perfiles = {}
        guardar_perfil(perfiles, "Guitarra", "Drop propio", "Estándar", {"Cuerda 6": -4})
        guardar_perfil(perfiles, "Ukelele", "Concierto", "Estándar", {})
        self.assertEqual(nombres_perfiles(perfiles, "Guitarra"), ["Drop propio"])
        self.assertEqual(nombres_perfiles(perfiles, "Ukelele"), ["Concierto"])

