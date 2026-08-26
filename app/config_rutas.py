"""Rutas absolutas del proyecto."""

import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_CONFIGURACIONES = os.path.join(RAIZ, "configuraciones")
RUTA_REGISTROS = os.path.join(RAIZ, "registros")
RUTA_ERRORES = os.path.join(RUTA_REGISTROS, "errores")
RUTA_AYUDA = os.path.join(RAIZ, "ayuda.html")
