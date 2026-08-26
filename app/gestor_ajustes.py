"""Persistencia separada de configuración técnica y ajustes de afinación.

La primera versión guardaba todo en ``configuraciones/ajustes.json``. Se migra
automáticamente al nuevo esquema sin borrar ese archivo heredado, por si hiciera
falta recuperar datos de una versión anterior.
"""

import json
import logging
import os
import shutil
from datetime import datetime

from app.config_rutas import RUTA_CONFIGURACIONES

logger = logging.getLogger(__name__)

RUTA_AJUSTES_LEGADOS = os.path.join(RUTA_CONFIGURACIONES, "ajustes.json")
RUTA_CONFIGURACION_AUDIO = os.path.join(RUTA_CONFIGURACIONES, "configuracion_audio.json")
RUTA_AJUSTES_AFINACION = os.path.join(RUTA_CONFIGURACIONES, "ajustes_afinacion.json")
RUTA_COPIAS_CONFIGURACION_AUDIO = os.path.join(RUTA_CONFIGURACIONES, "copias_configuracion_audio")
RUTA_COPIAS_AJUSTES_AFINACION = os.path.join(RUTA_CONFIGURACIONES, "copias_ajustes_afinacion")

CONFIGURACION_AUDIO_POR_DEFECTO = {
    "nombre_dispositivo": None,
    "frecuencia_la4": 440.0,
    "canal_entrada": None,
    "pitido_confirmacion": True,
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
    "nomenclatura_notas": "solfeo",
}

AJUSTES_AFINACION_POR_DEFECTO = {
    "instrumento": None,
    "cuerda": None,
    "escala": None,
    "familia_maqam": "Todas las familias",
    "ajustes_finos_cuerdas": {},
    "afinaciones_guardadas_lira": {},
    "perfiles_afinacion": {},
    "escala_base_personalizada": {},
}

AJUSTES_POR_DEFECTO = {**CONFIGURACION_AUDIO_POR_DEFECTO, **AJUSTES_AFINACION_POR_DEFECTO}
MAXIMO_COPIAS_POR_TIPO = 10


def _contenido_json(datos):
    return json.dumps(datos, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _leer_json(ruta, valores_por_defecto):
    datos = dict(valores_por_defecto)
    if not os.path.isfile(ruta):
        return datos
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            guardados = json.load(archivo)
        if not isinstance(guardados, dict):
            raise ValueError("el contenido no es un objeto JSON")
        datos.update(guardados)
    except Exception:
        logger.exception("no se pudo leer %s; se usan sus valores por defecto", ruta)
    return datos


def _crear_copia_anterior(ruta_origen, carpeta_copias, prefijo):
    if not os.path.isfile(ruta_origen):
        return
    os.makedirs(carpeta_copias, exist_ok=True)
    marca = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss_%f")
    destino = os.path.join(carpeta_copias, "{}_{}.json".format(prefijo, marca))
    shutil.copy2(ruta_origen, destino)
    copias = sorted(
        nombre for nombre in os.listdir(carpeta_copias)
        if nombre.startswith(prefijo + "_") and nombre.endswith(".json")
    )
    for nombre in copias[:-MAXIMO_COPIAS_POR_TIPO]:
        os.remove(os.path.join(carpeta_copias, nombre))


def _guardar_json_recuperable(ruta, datos, carpeta_copias, prefijo):
    """Escribe de forma atómica y conserva la versión anterior solo si cambió."""
    contenido_nuevo = _contenido_json(datos)
    if os.path.isfile(ruta):
        with open(ruta, "r", encoding="utf-8") as archivo:
            if archivo.read() == contenido_nuevo:
                return False
        _crear_copia_anterior(ruta, carpeta_copias, prefijo)
    ruta_temporal = ruta + ".tmp"
    with open(ruta_temporal, "w", encoding="utf-8") as archivo:
        archivo.write(contenido_nuevo)
    os.replace(ruta_temporal, ruta)
    return True


def _separar(ajustes):
    configuracion_audio = {
        clave: ajustes.get(clave, valor)
        for clave, valor in CONFIGURACION_AUDIO_POR_DEFECTO.items()
    }
    ajustes_afinacion = {
        clave: ajustes.get(clave, valor)
        for clave, valor in AJUSTES_AFINACION_POR_DEFECTO.items()
    }
    return configuracion_audio, ajustes_afinacion


def _migrar_ajustes_legados_si_hace_falta():
    """Crea los dos JSON nuevos a partir del antiguo sin eliminarlo ni modificarlo."""
    if os.path.exists(RUTA_CONFIGURACION_AUDIO) or os.path.exists(RUTA_AJUSTES_AFINACION):
        return
    if not os.path.isfile(RUTA_AJUSTES_LEGADOS):
        return
    try:
        with open(RUTA_AJUSTES_LEGADOS, "r", encoding="utf-8") as archivo:
            legados = json.load(archivo)
        if not isinstance(legados, dict):
            raise ValueError("ajustes.json no contiene un objeto JSON")
        audio, afinacion = _separar(legados)
        os.makedirs(RUTA_CONFIGURACIONES, exist_ok=True)
        _guardar_json_recuperable(
            RUTA_CONFIGURACION_AUDIO, audio, RUTA_COPIAS_CONFIGURACION_AUDIO, "configuracion_audio"
        )
        _guardar_json_recuperable(
            RUTA_AJUSTES_AFINACION, afinacion, RUTA_COPIAS_AJUSTES_AFINACION, "ajustes_afinacion"
        )
        logger.info("migrados ajustes.json a configuracion_audio.json y ajustes_afinacion.json")
    except Exception:
        logger.exception("no se pudo migrar configuraciones/ajustes.json al esquema separado")


def cargar_ajustes():
    """Carga y combina los dos archivos. La interfaz aún recibe un diccionario único."""
    _migrar_ajustes_legados_si_hace_falta()
    configuracion_audio = _leer_json(RUTA_CONFIGURACION_AUDIO, CONFIGURACION_AUDIO_POR_DEFECTO)
    ajustes_afinacion = _leer_json(RUTA_AJUSTES_AFINACION, AJUSTES_AFINACION_POR_DEFECTO)
    return {**AJUSTES_POR_DEFECTO, **configuracion_audio, **ajustes_afinacion}


def guardar_ajustes(ajustes):
    """Guarda cada grupo en su archivo y sus copias de seguridad independientes."""
    try:
        os.makedirs(RUTA_CONFIGURACIONES, exist_ok=True)
        configuracion_audio, ajustes_afinacion = _separar(ajustes)
        cambio_audio = _guardar_json_recuperable(
            RUTA_CONFIGURACION_AUDIO,
            configuracion_audio,
            RUTA_COPIAS_CONFIGURACION_AUDIO,
            "configuracion_audio",
        )
        cambio_afinacion = _guardar_json_recuperable(
            RUTA_AJUSTES_AFINACION,
            ajustes_afinacion,
            RUTA_COPIAS_AJUSTES_AFINACION,
            "ajustes_afinacion",
        )
        if cambio_audio or cambio_afinacion:
            logger.info("configuración y ajustes de afinación guardados correctamente")
    except Exception:
        logger.exception("no se pudieron guardar configuración y ajustes de afinación")
