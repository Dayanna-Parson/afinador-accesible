"""Perfiles de afinación del usuario, independientes de los presets de fábrica.

Los perfiles guardan desplazamientos en cuartos de tono porque es la unidad interna
del afinador: 1 equivale a 50 cents, 2 a un semitono y 4 a un tono.
"""

from copy import deepcopy


def migrar_perfiles(ajustes, nombre_lira):
    """Devuelve perfiles por instrumento y migra las afinaciones antiguas de lira.

    La migración no elimina los datos antiguos: así una actualización interrumpida
    nunca hace perder afinaciones que ya existían.
    """
    perfiles = deepcopy(ajustes.get("perfiles_afinacion", {}))
    perfiles.setdefault(nombre_lira, {})
    for nombre, datos in ajustes.get("afinaciones_guardadas_lira", {}).items():
        perfiles[nombre_lira].setdefault(nombre, deepcopy(datos))
    return perfiles


def nombres_perfiles(perfiles, instrumento):
    """Nombres ordenados de los perfiles de un único instrumento."""
    return sorted(perfiles.get(instrumento, {}), key=str.casefold)


def guardar_perfil(perfiles, instrumento, nombre, escala_base, retoques, familia_maqam=None):
    """Guarda una instantánea completa sin modificar ningún preset integrado."""
    perfiles.setdefault(instrumento, {})[nombre] = {
        "escala_base": escala_base,
        "retoques_manuales": {clave: int(valor) for clave, valor in retoques.items() if int(valor)},
    }
    if familia_maqam:
        perfiles[instrumento][nombre]["familia_maqam"] = familia_maqam

