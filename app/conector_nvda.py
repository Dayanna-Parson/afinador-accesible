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
SALIDA_LECTOR = "lector"
SALIDA_VOZ_PROPIA = "voz_propia"

# Con el lector de pantalla no hay forma de saber cuándo termina de hablar, así que se
# estima por la longitud del texto. Es deliberadamente generosa: ignorar el micrófono un
# poco de más solo retrasa la siguiente indicación; ignorarlo de menos hace que la propia
# voz, saliendo por los altavoces, se detecte como si fuera la cuerda.
SEGUNDOS_BASE_ESTIMACION_HABLA = 0.3
SEGUNDOS_POR_CARACTER_ESTIMACION_HABLA = 0.06
# Tras terminar de hablar, la reverberación de la habitación sigue llegando al micrófono
# unas décimas de segundo.
SEGUNDOS_MARGEN_TRAS_HABLAR = 0.3
# Valor de SpVoice.Status.RunningState mientras SAPI5 está hablando (SRSEIsSpeaking).
_SAPI5_HABLANDO = 2


def _crear_voz_propia():
    """Crea la salida SAPI5 de accessible_output3, independiente del lector de pantalla."""
    try:
        from accessible_output3.outputs.sapi5 import SAPI5
        return SAPI5()
    except Exception:
        logger.exception("no se pudo inicializar la voz propia SAPI5")
        return None


class AnunciadorNVDA:
    """Habla al lector de pantalla activo (NVDA, JAWS o Narrador) vía accessible_output3,
    o a una voz SAPI5 propia del afinador, también vía accessible_output3.

    Aplica un throttling estricto: una instrucción solo se pronuncia cuando lleva
    estable el tiempo mínimo configurado y difiere de la última ya pronunciada,
    para no saturar la cola de voz del lector con lecturas de audio en tiempo real.

    La voz propia no pasa por el lector de pantalla: el lector queda libre para
    leer la interfaz sin cortar ni ser cortado por las indicaciones de afinación,
    tiene su propio volumen y velocidad (útil para afinar lejos del ordenador) y
    permite saber con exactitud cuándo está hablando, para no confundir la voz que
    sale por los altavoces con el sonido de la cuerda.
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
        self._voz_propia = None
        self._tipo_salida = SALIDA_LECTOR
        self._fin_estimado_habla = 0.0
        self._marca_ultimo_envio = 0.0
        self._ultima_vez_hablando = 0.0
        self._mensaje_actual = None
        self._marca_tiempo_cambio = None
        self._ultimo_mensaje_hablado = None

    @property
    def tipo_salida(self):
        return self._tipo_salida

    def configurar_salida(self, tipo_salida, nombre_voz=None, velocidad=0, volumen=100):
        """Elige entre el lector de pantalla y la voz propia SAPI5.

        Devuelve el tipo de salida realmente activo: si la voz propia no se puede
        iniciar (por ejemplo, sin voces SAPI5 instaladas), se sigue usando el lector.
        """
        if tipo_salida != SALIDA_VOZ_PROPIA:
            self._tipo_salida = SALIDA_LECTOR
            return self._tipo_salida
        if self._voz_propia is None:
            self._voz_propia = _crear_voz_propia()
        if self._voz_propia is None:
            self._tipo_salida = SALIDA_LECTOR
            return self._tipo_salida
        try:
            if nombre_voz and nombre_voz in self._voz_propia.list_voices():
                self._voz_propia.set_voice(nombre_voz)
            self._voz_propia.set_rate(int(velocidad))
            self._voz_propia.set_volume(int(volumen))
        except Exception:
            logger.exception("no se pudo configurar la voz propia SAPI5")
        self._tipo_salida = SALIDA_VOZ_PROPIA
        return self._tipo_salida

    def listar_voces_propias(self):
        """Nombres de las voces SAPI5 instaladas, o lista vacía si no hay ninguna disponible."""
        if self._voz_propia is None:
            self._voz_propia = _crear_voz_propia()
        if self._voz_propia is None:
            return []
        try:
            return list(self._voz_propia.list_voices())
        except Exception:
            logger.exception("no se pudieron listar las voces SAPI5")
            return []

    def voz_propia_actual(self):
        if self._voz_propia is None:
            return None
        try:
            return self._voz_propia.get_voice()
        except Exception:
            logger.exception("no se pudo consultar la voz SAPI5 activa")
            return None

    def hablar(self, texto, interrumpir=False):
        """Envía texto directo a la salida activa, sin pasar por el throttling."""
        if not texto:
            return
        ahora = time.monotonic()
        self._marca_ultimo_envio = ahora
        duracion_estimada = SEGUNDOS_BASE_ESTIMACION_HABLA + len(texto) * SEGUNDOS_POR_CARACTER_ESTIMACION_HABLA
        if interrumpir:
            self._fin_estimado_habla = ahora + duracion_estimada
        else:
            self._fin_estimado_habla = max(self._fin_estimado_habla, ahora) + duracion_estimada
        if self._tipo_salida == SALIDA_VOZ_PROPIA and self._voz_propia is not None:
            try:
                self._voz_propia.speak(texto, interrupt=interrumpir)
                return
            except Exception:
                logger.exception("fallo al hablar con la voz propia; se usa el lector de pantalla")
        if self._salida is None:
            return
        try:
            self._salida.speak(texto)
        except Exception:
            logger.exception("fallo al enviar texto al lector de pantalla")

    def _voz_propia_hablando(self):
        try:
            return self._voz_propia.object.Status.RunningState == _SAPI5_HABLANDO
        except Exception:
            logger.exception("no se pudo consultar si la voz propia está hablando")
            return None

    def esta_hablando(self):
        """Indica si la voz del afinador puede estar sonando todavía por los altavoces.

        Con la voz propia se consulta el estado real de SAPI5; con el lector de
        pantalla solo cabe estimarlo por la longitud de lo último que se envió.
        """
        ahora = time.monotonic()
        if self._tipo_salida == SALIDA_VOZ_PROPIA and self._voz_propia is not None:
            hablando = self._voz_propia_hablando()
            if hablando is not None:
                if hablando:
                    self._ultima_vez_hablando = ahora
                    return True
                # SAPI5 tarda unas centésimas en arrancar tras recibir el texto: el margen
                # cuenta también desde el último envío, no solo desde que dejó de hablar.
                ultima_actividad = max(self._ultima_vez_hablando, self._marca_ultimo_envio)
                return ahora - ultima_actividad < SEGUNDOS_MARGEN_TRAS_HABLAR
        return ahora < self._fin_estimado_habla + SEGUNDOS_MARGEN_TRAS_HABLAR

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
        # Con la voz propia, una indicación nueva sustituye a la anterior si aún no ha
        # terminado: oír "sube" cuando la cuerda ya pasó de largo confunde más que ayuda.
        self.hablar(mensaje, interrumpir=self._tipo_salida == SALIDA_VOZ_PROPIA)
        self._ultimo_mensaje_hablado = mensaje
# ANCLAJE_FIN: api_nvda
