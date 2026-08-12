"""Salida de voz hacia el lector de pantalla activo, con throttling por estabilidad."""

import logging
import time

logger = logging.getLogger(__name__)

try:
    import accessible_output3.outputs.auto
    _SALIDA_DISPONIBLE = True
except ImportError:
    _SALIDA_DISPONIBLE = False

DURACION_ESTABILIDAD_SEGUNDOS = 0.35


# ANCLAJE_INICIO: api_nvda
class AnunciadorNVDA:
    """Habla al lector de pantalla activo (NVDA, JAWS o Narrador) vía accessible_output3.

    Aplica un throttling estricto: una instrucción solo se pronuncia cuando lleva
    estable el tiempo mínimo configurado y difiere de la última ya pronunciada,
    para no saturar la cola de voz del lector con lecturas de audio en tiempo real.
    """

    def __init__(self, duracion_estabilidad=DURACION_ESTABILIDAD_SEGUNDOS):
        self._duracion_estabilidad = duracion_estabilidad
        self._salida = None
        if _SALIDA_DISPONIBLE:
            try:
                self._salida = accessible_output3.outputs.auto.Auto()
            except Exception:
                logger.exception("no se pudo inicializar la salida de accesibilidad")
                self._salida = None
        self._mensaje_actual = None
        self._marca_tiempo_cambio = None
        self._ultimo_mensaje_hablado = None

    def hablar(self, texto):
        """Envía texto directo al lector de pantalla, sin pasar por el throttling."""
        if not texto or self._salida is None:
            return
        try:
            self._salida.speak(texto)
        except Exception:
            logger.exception("fallo al enviar texto al lector de pantalla")

    def reiniciar_estado(self):
        """Limpia el estado de estabilidad, por ejemplo al cambiar de instrumento o cuerda."""
        self._mensaje_actual = None
        self._marca_tiempo_cambio = None
        self._ultimo_mensaje_hablado = None

    def procesar_instruccion(self, mensaje):
        """Evalúa si la instrucción actual debe pronunciarse según el tiempo de estabilidad."""
        if mensaje is None:
            self.reiniciar_estado()
            return
        ahora = time.monotonic()
        if mensaje != self._mensaje_actual:
            self._mensaje_actual = mensaje
            self._marca_tiempo_cambio = ahora
        if self._marca_tiempo_cambio is None:
            return
        if ahora - self._marca_tiempo_cambio < self._duracion_estabilidad:
            return
        if mensaje == self._ultimo_mensaje_hablado:
            return
        self.hablar(mensaje)
        self._ultimo_mensaje_hablado = mensaje
# ANCLAJE_FIN: api_nvda
