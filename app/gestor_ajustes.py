"""Persistencia de los ajustes de la aplicación en configuraciones/ajustes.json."""

import json
import logging
import os

from app.config_rutas import RUTA_AJUSTES, RUTA_CONFIGURACIONES

logger = logging.getLogger(__name__)

AJUSTES_POR_DEFECTO = {
    "nombre_dispositivo": None,
    "instrumento": None,
    "cuerda": None,
    "tasa_muestreo": None,
    "duracion_ventana": 0.1,
    "umbral_yin": 0.15,
    "umbral_rms": 0.02,
    "preferir_exclusivo_wasapi": False,
    "ganancia": 1.0,
    "bucle_referencia": False,
    "avance_automatico": True,
    "modo_solo_escucha": False,
    "umbral_yin": 0.15,
    "ajustes_finos_cuerdas": {},
}


def cargar_ajustes():
    """Lee ajustes.json y lo completa con los valores por defecto que falten."""
    ajustes = dict(AJUSTES_POR_DEFECTO)
    if not os.path.isfile(RUTA_AJUSTES):
        return ajustes
    try:
        with open(RUTA_AJUSTES, "r", encoding="utf-8") as archivo:
            guardados = json.load(archivo)
        ajustes.update(guardados)
    except Exception:
        logger.exception("no se pudo leer configuraciones/ajustes.json, se usan valores por defecto")
    return ajustes


def guardar_ajustes(ajustes):
    """Escritura atómica: primero a un archivo temporal, luego renombrado sobre el destino."""
    try:
        os.makedirs(RUTA_CONFIGURACIONES, exist_ok=True)
        ruta_temporal = RUTA_AJUSTES + ".tmp"
        with open(ruta_temporal, "w", encoding="utf-8") as archivo:
            json.dump(ajustes, archivo, ensure_ascii=False, indent=2)
        os.replace(ruta_temporal, RUTA_AJUSTES)
    except Exception:
        logger.exception("no se pudieron guardar los ajustes")
