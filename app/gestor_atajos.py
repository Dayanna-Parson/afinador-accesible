"""Atajos de teclado configurables.

Mismo patrón que Epub TTS Accesible (dos JSON, convención de VS Code):
  - teclas_predeterminadas.json → valores de fábrica, nunca se tocan a mano.
  - teclas_usuario.json          → solo los overrides que se hayan asignado.

Al cargar se fusionan ambos: se puede sobrescribir cualquier valor de fábrica,
y restaurar todo vaciando teclas_usuario.json (restablecer_todos()).

Los atajos fijos (F1, Ctrl+1/2/3, la tecla Menú y Mayús+F10 del menú
contextual) no viven aquí: no compiten por la misma tecla que estos, y
reasignarlos rompería convenciones ya fijadas en toda la app.
"""

import json
import logging
import os

from app.config_rutas import RUTA_CONFIGURACIONES

logger = logging.getLogger(__name__)

_RUTA_DEFAULTS = os.path.join(RUTA_CONFIGURACIONES, "teclas_predeterminadas.json")
_RUTA_USUARIO = os.path.join(RUTA_CONFIGURACIONES, "teclas_usuario.json")

# Atajos de fábrica embebidos en el código. Se escriben a
# teclas_predeterminadas.json si el archivo no existe o le faltan claves,
# para que una versión posterior que añada un atajo nuevo no deje sin
# activar ese atajo en instalaciones que ya tenían el archivo creado.
_DEFAULTS_EMBEBIDOS = {
    "reproducir_referencia": {
        "descripcion": "Reproducir el tono de referencia de la cuerda seleccionada",
        "modificador": "Ctrl",
        "tecla": "P",
    },
    "alternar_escucha": {
        "descripcion": "Iniciar o detener la escucha del micrófono",
        "modificador": "Ctrl",
        "tecla": "E",
    },
    "subir_cuarto_tono": {
        "descripcion": "Subir la cuerda seleccionada según el ajuste manual elegido",
        "modificador": "Ctrl+Shift",
        "tecla": "Arriba",
    },
    "bajar_cuarto_tono": {
        "descripcion": "Bajar la cuerda seleccionada según el ajuste manual elegido",
        "modificador": "Ctrl+Shift",
        "tecla": "Abajo",
    },
    "restablecer_ajuste_fino": {
        "descripcion": "Restablecer el ajuste manual de la cuerda seleccionada",
        "modificador": "Ctrl+Shift",
        "tecla": "R",
    },
    "escucha_previa_escala": {
        "descripcion": "Reproducir la afinación completa (todas las cuerdas seguidas)",
        "modificador": "Ctrl+Shift",
        "tecla": "P",
    },
    "deshacer_retoque": {
        "descripcion": "Deshacer el último retoque en cuartos de tono",
        "modificador": "Ctrl+Shift",
        "tecla": "Z",
    },
    "repetir_instruccion": {
        "descripcion": "Repetir la última instrucción de afinación anunciada",
        "modificador": "Ctrl+Shift",
        "tecla": "V",
    },
}


def _asegurar_defaults():
    if os.path.exists(_RUTA_DEFAULTS):
        try:
            with open(_RUTA_DEFAULTS, "r", encoding="utf-8") as archivo:
                contenido = archivo.read().strip()
            datos = json.loads(contenido) if contenido else {}
            faltantes = {clave: valor for clave, valor in _DEFAULTS_EMBEBIDOS.items() if clave not in datos}
            if not faltantes:
                return
            datos.update(faltantes)
            with open(_RUTA_DEFAULTS, "w", encoding="utf-8") as archivo:
                json.dump(datos, archivo, ensure_ascii=False, indent=2)
            return
        except Exception:
            logger.exception(
                "no se pudo leer/actualizar teclas_predeterminadas.json, se reescribirá desde cero"
            )
    os.makedirs(RUTA_CONFIGURACIONES, exist_ok=True)
    with open(_RUTA_DEFAULTS, "w", encoding="utf-8") as archivo:
        json.dump(_DEFAULTS_EMBEBIDOS, archivo, ensure_ascii=False, indent=2)


def cargar_atajos():
    """Devuelve el diccionario fusionado: defaults + overrides guardados."""
    _asegurar_defaults()
    try:
        with open(_RUTA_DEFAULTS, "r", encoding="utf-8") as archivo:
            defaults = json.load(archivo)
    except Exception:
        logger.exception("no se pudo leer teclas_predeterminadas.json, se usan los defaults embebidos")
        defaults = dict(_DEFAULTS_EMBEBIDOS)

    usuario = {}
    if os.path.exists(_RUTA_USUARIO):
        try:
            with open(_RUTA_USUARIO, "r", encoding="utf-8") as archivo:
                usuario = json.load(archivo)
        except Exception:
            logger.exception("no se pudo leer teclas_usuario.json, se ignoran los overrides")
            usuario = {}

    resultado = {}
    for clave, entrada_defecto in defaults.items():
        entrada = dict(entrada_defecto)
        if clave in usuario:
            override = usuario[clave]
            entrada["modificador"] = override.get("modificador", entrada["modificador"])
            entrada["tecla"] = override.get("tecla", entrada["tecla"])
        resultado[clave] = entrada
    return resultado


def cargar_defaults():
    """Devuelve solo los atajos predeterminados de fábrica."""
    _asegurar_defaults()
    try:
        with open(_RUTA_DEFAULTS, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except Exception:
        logger.exception("no se pudo leer teclas_predeterminadas.json, se devuelven los defaults embebidos")
        return dict(_DEFAULTS_EMBEBIDOS)


def guardar_atajo_usuario(clave, modificador, tecla):
    """Guarda o actualiza un override de usuario en teclas_usuario.json."""
    usuario = {}
    if os.path.exists(_RUTA_USUARIO):
        try:
            with open(_RUTA_USUARIO, "r", encoding="utf-8") as archivo:
                usuario = json.load(archivo)
        except Exception:
            logger.exception("no se pudo leer teclas_usuario.json, se sobrescribirá con este override")
            usuario = {}
    usuario[clave] = {"modificador": modificador, "tecla": tecla}
    os.makedirs(RUTA_CONFIGURACIONES, exist_ok=True)
    with open(_RUTA_USUARIO, "w", encoding="utf-8") as archivo:
        json.dump(usuario, archivo, ensure_ascii=False, indent=2)


def eliminar_atajo_usuario(clave):
    """Elimina el override de usuario para un atajo, restaurando su valor de fábrica."""
    if not os.path.exists(_RUTA_USUARIO):
        return
    try:
        with open(_RUTA_USUARIO, "r", encoding="utf-8") as archivo:
            usuario = json.load(archivo)
        if clave in usuario:
            del usuario[clave]
            with open(_RUTA_USUARIO, "w", encoding="utf-8") as archivo:
                json.dump(usuario, archivo, ensure_ascii=False, indent=2)
    except Exception:
        logger.exception("no se pudo eliminar el override de usuario para '%s'", clave)


def restablecer_todos():
    """Borra teclas_usuario.json: todos los atajos vuelven a sus valores de fábrica."""
    if os.path.exists(_RUTA_USUARIO):
        os.remove(_RUTA_USUARIO)


def texto_atajo(entrada):
    """Convierte {'modificador': 'Ctrl', 'tecla': 'P'} en 'Ctrl+P'."""
    modificador = entrada.get("modificador", "").strip()
    tecla = entrada.get("tecla", "").strip()
    if modificador and tecla:
        return "{}+{}".format(modificador, tecla)
    return tecla or modificador or "(sin asignar)"
