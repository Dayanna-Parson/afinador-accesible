"""Recursos visuales con fallback nativo y sin iconos exclusivamente visuales."""

import wx


ICONOS = {
    "afinar": wx.ART_TICK_MARK,
    "afinaciones": wx.ART_LIST_VIEW,
    "audio": wx.ART_TIP,
    "reproducir": wx.ART_GO_FORWARD,
    "detener": wx.ART_CROSS_MARK,
    "ajustes": wx.ART_EXECUTABLE_FILE,
}


def bitmap_icono(nombre, tamano=(16, 16)):
    """Obtiene un icono nativo; la interfaz siempre conserva una etiqueta textual."""
    return wx.ArtProvider.GetBitmap(ICONOS.get(nombre, wx.ART_INFORMATION), wx.ART_BUTTON, tamano)
