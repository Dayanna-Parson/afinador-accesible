"""Punto de entrada de AfinadorAccesible."""

import logging
import os
import sys
import threading
import faulthandler
from logging.handlers import RotatingFileHandler

import wx

from app.config_rutas import RUTA_ERRORES, RUTA_REGISTROS
from app.interfaz.ventana_principal import VentanaPrincipal

RUTA_LOG = os.path.join(RUTA_REGISTROS, "afinador.log")
TAMANO_MAXIMO_LOG = 2 * 1024 * 1024
NUMERO_RESPALDOS_LOG = 3


class _HandlerErrorIndividual(logging.Handler):
    """Escribe cada error en un archivo separado, además del registro general."""

    MAXIMO_ARCHIVOS = 20

    def __init__(self):
        super().__init__(level=logging.ERROR)
        os.makedirs(RUTA_ERRORES, exist_ok=True)
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))

    def emit(self, record):
        try:
            from datetime import datetime
            marca = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d_%H-%M-%S_%f")
            ruta = os.path.join(RUTA_ERRORES, "{}_{}.log".format(marca, record.levelname.lower()))
            with open(ruta, "w", encoding="utf-8") as archivo:
                archivo.write(self.format(record))
            archivos = sorted(
                nombre for nombre in os.listdir(RUTA_ERRORES)
                if nombre.endswith(".log") and nombre != "fallo_nativo.log"
            )
            for nombre in archivos[:-self.MAXIMO_ARCHIVOS]:
                os.remove(os.path.join(RUTA_ERRORES, nombre))
        except Exception as error:
            print("No se pudo guardar el registro individual: {}".format(error), file=sys.stderr)


def _configurar_logging():
    os.makedirs(RUTA_REGISTROS, exist_ok=True)
    os.makedirs(RUTA_ERRORES, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            RotatingFileHandler(RUTA_LOG, maxBytes=TAMANO_MAXIMO_LOG, backupCount=NUMERO_RESPALDOS_LOG,
                                 encoding="utf-8"),
            logging.StreamHandler(),
            _HandlerErrorIndividual(),
        ],
    )


def _registrar_excepcion_no_controlada(tipo, valor, traza):
    """Conserva el detalle de un cierre inesperado en afinador.log."""
    logging.getLogger(__name__).critical("cierre inesperado de la aplicación", exc_info=(tipo, valor, traza))


def _registrar_excepcion_hilo(argumentos):
    _registrar_excepcion_no_controlada(argumentos.exc_type, argumentos.exc_value, argumentos.exc_traceback)


def main():
    _configurar_logging()
    # Si un controlador de audio provoca un cierre nativo, Python no llega a ejecutar
    # una excepción normal. faulthandler deja al menos la traza nativa para diagnosticarlo.
    ruta_fallo_nativo = os.path.join(RUTA_ERRORES, "fallo_nativo.log")
    archivo_fallo_nativo = open(ruta_fallo_nativo, "a", encoding="utf-8")
    faulthandler.enable(file=archivo_fallo_nativo, all_threads=True)
    sys.excepthook = _registrar_excepcion_no_controlada
    threading.excepthook = _registrar_excepcion_hilo
    aplicacion = wx.App(False)
    VentanaPrincipal()
    aplicacion.MainLoop()


if __name__ == "__main__":
    main()
