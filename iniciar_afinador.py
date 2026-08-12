"""Punto de entrada de AfinadorAccesible."""

import logging
import os

import wx

from app.interfaz_gui import VentanaPrincipal

RUTA_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "afinador.log")


def _configurar_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(RUTA_LOG, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def main():
    _configurar_logging()
    aplicacion = wx.App(False)
    VentanaPrincipal()
    aplicacion.MainLoop()


if __name__ == "__main__":
    main()
