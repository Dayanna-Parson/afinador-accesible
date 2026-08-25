"""Iconos de botones seguros: apoyo visual, nunca sustituto del texto o de NVDA."""

import os

import wx

from app.config_rutas import RAIZ


_RUTA_ICONOS = os.path.join(RAIZ, "recursos", "iconos")
_ART_FALLBACK = {
    "afinar": wx.ART_TICK_MARK,
    "afinaciones": wx.ART_LIST_VIEW,
    "audio": wx.ART_TIP,
    "reproducir": wx.ART_GO_FORWARD,
    "detener": wx.ART_CROSS_MARK,
    "ajustes": wx.ART_EXECUTABLE_FILE,
    "subir": wx.ART_GO_UP,
    "bajar": wx.ART_GO_DOWN,
    "restablecer": wx.ART_UNDO,
    "guardar": wx.ART_FILE_SAVE,
    "cargar": wx.ART_FILE_OPEN,
    "ayuda": wx.ART_HELP,
}


def bitmap_icono(nombre, tamano=(16, 16)):
    """Busca un PNG opcional y, si falta, un icono nativo de wx."""
    ruta = os.path.join(_RUTA_ICONOS, "{}.png".format(nombre))
    try:
        if os.path.isfile(ruta):
            imagen = wx.Image(ruta, wx.BITMAP_TYPE_PNG)
            if imagen.IsOk():
                return wx.Bitmap(imagen.Scale(*tamano, wx.IMAGE_QUALITY_HIGH))
        return wx.ArtProvider.GetBitmap(
            _ART_FALLBACK.get(nombre, wx.ART_INFORMATION), wx.ART_BUTTON, tamano
        )
    except Exception:
        return wx.NullBitmap


def aplicar_icono_boton(boton, nombre_icono, nombre_accesible="", fijar_nombre=True):
    """Añade icono sin ocultar etiqueta; el nombre accesible queda siempre explícito."""
    if fijar_nombre:
        boton.SetName(nombre_accesible or boton.GetLabel())
    bitmap = bitmap_icono(nombre_icono)
    if bitmap.IsOk():
        boton.SetBitmap(bitmap)
        boton.SetBitmapMargins(4, 2)
