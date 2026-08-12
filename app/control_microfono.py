"""Comprobación y corrección del silencio de Windows a nivel de sistema para el micrófono."""

import logging

logger = logging.getLogger(__name__)

try:
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from pycaw.constants import DEVICE_STATE
    _PYCAW_DISPONIBLE = True
except ImportError:
    _PYCAW_DISPONIBLE = False


def asegurar_microfono_activo(nombre_dispositivo=None):
    """Si Windows tiene silenciado el micrófono de entrada a nivel de sistema, lo desmutea.

    No hace nada si pycaw no está instalado (solo aplica en Windows) o si no encuentra
    el dispositivo. Cualquier fallo se registra y se ignora: esto es una comodidad para
    evitar el silencio automático conocido en algunos portátiles con varios micrófonos,
    nunca debe impedir que la captura de audio arranque.
    """
    if not _PYCAW_DISPONIBLE:
        return
    try:
        dispositivos = AudioUtilities.GetAllDevices()
        for dispositivo in dispositivos:
            if dispositivo.state != DEVICE_STATE.ACTIVE.value:
                continue
            nombre_amigable = dispositivo.FriendlyName or ""
            if nombre_dispositivo and nombre_dispositivo not in nombre_amigable:
                continue
            interfaz = dispositivo._dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            control_volumen = interfaz.QueryInterface(IAudioEndpointVolume)
            if control_volumen.GetMute():
                control_volumen.SetMute(0, None)
                logger.info("El micrófono '%s' estaba silenciado en Windows; se ha desmuteado", nombre_amigable)
            if nombre_dispositivo:
                return
    except Exception:
        logger.exception("no se pudo comprobar/desmutear el micrófono a nivel de sistema")
