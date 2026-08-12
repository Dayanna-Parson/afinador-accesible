"""Rutas absolutas del proyecto."""

import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_CONFIGURACIONES = os.path.join(RAIZ, "configuraciones")
RUTA_AJUSTES = os.path.join(RUTA_CONFIGURACIONES, "ajustes.json")
