"""Persistencia de los ajustes de la aplicación en configuraciones/ajustes.json."""

import json
import logging
import os
import shutil
from datetime import datetime

from app.config_rutas import RUTA_AJUSTES, RUTA_CONFIGURACIONES, RUTA_COPIAS_AJUSTES

logger = logging.getLogger(__name__)

AJUSTES_POR_DEFECTO = {
    "nombre_dispositivo": None,
    "frecuencia_la4": 440.0,
    "canal_entrada": None,
    "pitido_confirmacion": True,
    "instrumento": None,
    "cuerda": None,
    "tasa_muestreo": None,
    "duracion_ventana": 0.1,
    "umbral_yin": 0.15,
    "umbral_rms": 0.02,
    "preferir_exclusivo_wasapi": False,
    "desmutear_microfono_si_es_necesario": False,
    "ganancia": 1.0,
    "bucle_referencia": False,
    "avance_automatico": True,
    "modo_solo_escucha": False,
    "deteccion_automatica_cuerda": False,
    "instrucciones_detalladas": False,
    "umbral_yin": 0.15,
    "escala": None,
    "familia_maqam": "Todas las familias",
    "ajustes_finos_cuerdas": {},
    "afinaciones_guardadas_lira": {},
    "perfiles_afinacion": {},
    "escala_base_personalizada": {},
    "nomenclatura_notas": "solfeo",
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


MAXIMO_COPIAS_AJUSTES = 10


def _contenido_json(ajustes):
    return json.dumps(ajustes, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _crear_copia_ajustes_anterior():
    """Guarda la versión anterior antes de sustituirla y conserva solo las diez últimas."""
    if not os.path.isfile(RUTA_AJUSTES):
        return
    os.makedirs(RUTA_COPIAS_AJUSTES, exist_ok=True)
    marca = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss_%f")
    destino = os.path.join(RUTA_COPIAS_AJUSTES, "ajustes_{}.json".format(marca))
    shutil.copy2(RUTA_AJUSTES, destino)
    copias = sorted(
        nombre for nombre in os.listdir(RUTA_COPIAS_AJUSTES)
        if nombre.startswith("ajustes_") and nombre.endswith(".json")
    )
    for nombre in copias[:-MAXIMO_COPIAS_AJUSTES]:
        os.remove(os.path.join(RUTA_COPIAS_AJUSTES, nombre))


def guardar_ajustes(ajustes):
    """Escritura atómica con historial recuperable de los diez cambios reales más recientes."""
    try:
        os.makedirs(RUTA_CONFIGURACIONES, exist_ok=True)
        contenido_nuevo = _contenido_json(ajustes)
        if os.path.isfile(RUTA_AJUSTES):
            with open(RUTA_AJUSTES, "r", encoding="utf-8") as archivo:
                if archivo.read() == contenido_nuevo:
                    return
            _crear_copia_ajustes_anterior()
        ruta_temporal = RUTA_AJUSTES + ".tmp"
        with open(ruta_temporal, "w", encoding="utf-8") as archivo:
            archivo.write(contenido_nuevo)
        os.replace(ruta_temporal, RUTA_AJUSTES)
        logger.info("ajustes guardados correctamente")
    except Exception:
        logger.exception("no se pudieron guardar los ajustes")
