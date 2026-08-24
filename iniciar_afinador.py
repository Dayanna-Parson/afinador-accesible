"""Punto de entrada de AfinadorAccesible."""

import logging
import os
import sys
import threading
from logging.handlers import RotatingFileHandler

import wx

from app.interfaz_gui import VentanaPrincipal

RUTA_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "afinador.log")
TAMANO_MAXIMO_LOG = 2 * 1024 * 1024
NUMERO_RESPALDOS_LOG = 3


def _configurar_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            RotatingFileHandler(RUTA_LOG, maxBytes=TAMANO_MAXIMO_LOG, backupCount=NUMERO_RESPALDOS_LOG,
                                 encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def _registrar_excepcion_no_controlada(tipo, valor, traza):
    """Conserva el detalle de un cierre inesperado en afinador.log."""
    logging.getLogger(__name__).critical("cierre inesperado de la aplicación", exc_info=(tipo, valor, traza))


def _registrar_excepcion_hilo(argumentos):
    _registrar_excepcion_no_controlada(argumentos.exc_type, argumentos.exc_value, argumentos.exc_traceback)


def main():
    _configurar_logging()
    sys.excepthook = _registrar_excepcion_no_controlada
    threading.excepthook = _registrar_excepcion_hilo
    aplicacion = wx.App(False)
    VentanaPrincipal()
    aplicacion.MainLoop()


if __name__ == "__main__":
    main()
