"""Captura de audio, detección de tono mediante YIN y generación de tonos de referencia."""

import logging
import queue
import threading
import time

import numpy as np
import sounddevice as sd

try:
    import motor_rust as _motor_rust
    _RUST_DISPONIBLE = True
except ImportError:
    _motor_rust = None
    _RUST_DISPONIBLE = False

logger = logging.getLogger(__name__)

FRECUENCIA_LA4 = 440.0
NOMBRES_NOTAS = ["Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]
INDICE_LA = 9


def listar_dispositivos_entrada():
    """Devuelve los dispositivos de audio con al menos un canal de entrada disponible.

    Cuando la extensión nativa (motor_rust, backend cpal) está disponible, los índices
    se enumeran desde ahí, porque son los que después usará CapturadorYIN para abrir el
    dispositivo real; no coinciden necesariamente con los índices de sounddevice/PortAudio.
    """
    if _RUST_DISPONIBLE:
        return [
            {"indice": indice, "nombre": nombre, "tasa_muestreo_defecto": tasa}
            for indice, nombre, tasa in _motor_rust.listar_dispositivos_entrada()
        ]
    dispositivos = []
    for indice, info in enumerate(sd.query_devices()):
        if info.get("max_input_channels", 0) > 0:
            dispositivos.append({
                "indice": indice,
                "nombre": info["name"],
                "tasa_muestreo_defecto": int(info["default_samplerate"]),
            })
    return dispositivos


def frecuencia_a_nota(frecuencia):
    """Traduce una frecuencia en Hz a la nota cromática más cercana y su desviación en cents."""
    if frecuencia is None or frecuencia <= 0:
        return None
    semitonos = 12 * np.log2(frecuencia / FRECUENCIA_LA4)
    semitonos_redondeados = int(round(semitonos))
    frecuencia_objetivo = FRECUENCIA_LA4 * (2 ** (semitonos_redondeados / 12))
    cents = 1200 * np.log2(frecuencia / frecuencia_objetivo)
    indice_nota = (semitonos_redondeados + INDICE_LA) % 12
    octava = 4 + (semitonos_redondeados + INDICE_LA) // 12
    return {
        "nombre": NOMBRES_NOTAS[indice_nota],
        "octava": octava,
        "frecuencia": frecuencia,
        "frecuencia_objetivo": frecuencia_objetivo,
        "cents": cents,
    }


def nota_a_frecuencia(indice_nota, octava):
    """Calcula la frecuencia exacta de una nota cromática a partir de su índice (0=Do) y octava."""
    semitonos_desde_la4 = (indice_nota - INDICE_LA) + (octava - 4) * 12
    return FRECUENCIA_LA4 * (2 ** (semitonos_desde_la4 / 12))


def calcular_instruccion(cents, margen_afinada=5.0, margen_bastante=25.0):
    """Clasifica la desviación en cents en una instrucción de afinación."""
    if cents is None:
        return None
    if abs(cents) <= margen_afinada:
        return "AFINADA"
    if cents < 0:
        return "BAJA_BASTANTE" if cents < -margen_bastante else "BAJA_POCO"
    return "SUBE_BASTANTE" if cents > margen_bastante else "SUBE_POCO"


# ANCLAJE_INICIO: capturador_yin
def estimar_frecuencia_yin(senal, tasa_muestreo, umbral=0.15, f_min=60.0, f_max=1500.0):
    """Estima la frecuencia fundamental de una señal mono mediante el algoritmo YIN.

    Devuelve None si no se encuentra un candidato fiable por debajo del umbral.
    """
    tamano = len(senal)
    retardo_maximo = min(int(tasa_muestreo / f_min), tamano // 2)
    retardo_minimo = max(int(tasa_muestreo / f_max), 1)
    if retardo_maximo <= retardo_minimo:
        return None

    longitud_segmento = tamano - retardo_maximo
    diferencia = np.zeros(retardo_maximo)
    segmento_base = senal[:longitud_segmento]
    for retardo in range(retardo_maximo):
        segmento_desplazado = senal[retardo:retardo + longitud_segmento]
        diferencia[retardo] = np.sum((segmento_base - segmento_desplazado) ** 2)

    diferencia_acumulada = np.ones(retardo_maximo)
    suma_corrida = 0.0
    for retardo in range(1, retardo_maximo):
        suma_corrida += diferencia[retardo]
        if suma_corrida > 0:
            diferencia_acumulada[retardo] = diferencia[retardo] * retardo / suma_corrida
        else:
            diferencia_acumulada[retardo] = 1.0

    retardo_elegido = None
    for retardo in range(retardo_minimo, retardo_maximo):
        if diferencia_acumulada[retardo] < umbral:
            while retardo + 1 < retardo_maximo and diferencia_acumulada[retardo + 1] < diferencia_acumulada[retardo]:
                retardo += 1
            retardo_elegido = retardo
            break

    if retardo_elegido is None:
        return None

    if 0 < retardo_elegido < retardo_maximo - 1:
        anterior = diferencia_acumulada[retardo_elegido - 1]
        actual = diferencia_acumulada[retardo_elegido]
        siguiente = diferencia_acumulada[retardo_elegido + 1]
        denominador = anterior - 2 * actual + siguiente
        ajuste = (anterior - siguiente) / (2 * denominador) if denominador != 0 else 0.0
        retardo_final = retardo_elegido + ajuste
    else:
        retardo_final = retardo_elegido

    if retardo_final <= 0:
        return None
    return tasa_muestreo / retardo_final


class _CapturadorYINPuroPython:
    """Captura audio en un hilo secundario y estima el tono mediante YIN con puerta de ruido.

    Implementación 100% Python con sounddevice, usada como respaldo cuando la extensión
    nativa `motor_rust` (cpal + YIN en Rust) no está compilada para la plataforma actual.
    """

    def __init__(self, indice_dispositivo=None, tasa_muestreo=44100, duracion_ventana=0.1,
                 umbral_yin=0.15, umbral_rms=0.02, al_detectar=None):
        self.indice_dispositivo = indice_dispositivo
        self.tasa_muestreo = tasa_muestreo
        self.tamano_ventana = max(int(tasa_muestreo * duracion_ventana), 1024)
        self.umbral_yin = umbral_yin
        self.umbral_rms = umbral_rms
        self.al_detectar = al_detectar

        self._flujo = None
        self._cola = queue.Queue(maxsize=2)
        self._hilo_analisis = None
        self._detener = threading.Event()
        self._pausado = threading.Event()

    def _callback_audio(self, indata, marcos, tiempo_info, estado):
        if estado:
            logger.warning("estado del flujo de entrada de audio: %s", estado)
        if self._pausado.is_set():
            return
        try:
            self._cola.put_nowait(indata[:, 0].copy())
        except queue.Full:
            try:
                self._cola.get_nowait()
            except queue.Empty:
                pass
            try:
                self._cola.put_nowait(indata[:, 0].copy())
            except queue.Full:
                pass

    def _bucle_analisis(self):
        while not self._detener.is_set():
            try:
                bloque = self._cola.get(timeout=0.2)
            except queue.Empty:
                continue
            rms = float(np.sqrt(np.mean(bloque ** 2)))
            if rms < self.umbral_rms:
                if self.al_detectar:
                    self.al_detectar(None, rms)
                continue
            try:
                frecuencia = estimar_frecuencia_yin(bloque, self.tasa_muestreo, umbral=self.umbral_yin)
            except Exception:
                logger.exception("fallo al estimar la frecuencia con YIN")
                frecuencia = None
            resultado = frecuencia_a_nota(frecuencia) if frecuencia else None
            if self.al_detectar:
                self.al_detectar(resultado, rms)

    def iniciar(self):
        if self._flujo is not None:
            return
        self._detener.clear()
        self._pausado.clear()
        self._hilo_analisis = threading.Thread(target=self._bucle_analisis, daemon=True)
        self._hilo_analisis.start()
        self._flujo = sd.InputStream(
            device=self.indice_dispositivo,
            channels=1,
            samplerate=self.tasa_muestreo,
            blocksize=self.tamano_ventana,
            callback=self._callback_audio,
        )
        self._flujo.start()

    def detener(self):
        if self._flujo is not None:
            self._flujo.stop()
            self._flujo.close()
            self._flujo = None
        self._detener.set()
        if self._hilo_analisis is not None:
            self._hilo_analisis.join(timeout=1.0)
            self._hilo_analisis = None

    def pausar(self):
        """Suspende la captura sin cerrar el flujo, para evitar retroalimentación acústica."""
        self._pausado.set()

    def reanudar(self):
        self._pausado.clear()


class CapturadorYIN:
    """Captura de audio y detección de tono con la misma interfaz pública sin importar el backend.

    Usa la extensión nativa `motor_rust` (cpal + YIN en Rust) cuando está compilada e instalada,
    por su menor latencia y acceso más directo al dispositivo (WASAPI en Windows). Si no está
    disponible, recurre de forma transparente a la implementación en Python puro con sounddevice.
    """

    def __init__(self, indice_dispositivo=None, tasa_muestreo=44100, duracion_ventana=0.1,
                 umbral_yin=0.15, umbral_rms=0.02, al_detectar=None):
        self.al_detectar = al_detectar
        if _RUST_DISPONIBLE:
            self._backend = "rust"
            self._nucleo = _motor_rust.CapturadorYinRust(
                self._al_detectar_rust, indice_dispositivo, umbral_yin, umbral_rms
            )
        else:
            self._backend = "python"
            self._nucleo = _CapturadorYINPuroPython(
                indice_dispositivo=indice_dispositivo,
                tasa_muestreo=tasa_muestreo,
                duracion_ventana=duracion_ventana,
                umbral_yin=umbral_yin,
                umbral_rms=umbral_rms,
                al_detectar=al_detectar,
            )

    def _al_detectar_rust(self, frecuencia, rms):
        resultado = frecuencia_a_nota(frecuencia) if frecuencia else None
        if self.al_detectar:
            self.al_detectar(resultado, rms)

    def iniciar(self):
        self._nucleo.iniciar()

    def detener(self):
        self._nucleo.detener()

    def pausar(self):
        """Suspende la captura sin cerrar el flujo, para evitar retroalimentación acústica."""
        self._nucleo.pausar()

    def reanudar(self):
        self._nucleo.reanudar()
# ANCLAJE_FIN: capturador_yin


# ANCLAJE_INICIO: generador_tonos
class GeneradorTonos:
    """Genera y reproduce tonos senoidales de referencia, coordinando la pausa del capturador."""

    def __init__(self, capturador=None, tasa_muestreo=44100):
        self.capturador = capturador
        self.tasa_muestreo = tasa_muestreo
        self._hilo_reproduccion = None

    def _generar_onda(self, frecuencia, duracion, amplitud=0.3):
        muestras = int(self.tasa_muestreo * duracion)
        tiempo = np.linspace(0, duracion, muestras, endpoint=False)
        onda = amplitud * np.sin(2 * np.pi * frecuencia * tiempo)
        rampa = min(int(self.tasa_muestreo * 0.01), muestras // 2)
        if rampa > 0:
            envolvente = np.ones(muestras)
            envolvente[:rampa] = np.linspace(0, 1, rampa)
            envolvente[-rampa:] = np.linspace(1, 0, rampa)
            onda *= envolvente
        return onda.astype(np.float32)

    def _reproducir_bloqueante(self, frecuencia, duracion, amplitud, al_finalizar):
        if self.capturador is not None:
            self.capturador.pausar()
        try:
            onda = self._generar_onda(frecuencia, duracion, amplitud)
            sd.play(onda, samplerate=self.tasa_muestreo, blocking=True)
        except Exception:
            logger.exception("fallo al reproducir el tono de referencia")
        finally:
            if self.capturador is not None:
                self.capturador.reanudar()
            if al_finalizar:
                al_finalizar()

    def reproducir(self, frecuencia, duracion=2.0, amplitud=0.3, al_finalizar=None):
        """Reproduce el tono en un hilo secundario, pausando la captura mientras suena."""
        self._hilo_reproduccion = threading.Thread(
            target=self._reproducir_bloqueante,
            args=(frecuencia, duracion, amplitud, al_finalizar),
            daemon=True,
        )
        self._hilo_reproduccion.start()

    def reproducir_confirmacion(self, frecuencia=880.0, duracion=0.15, amplitud=0.25):
        """Pitido corto de confirmación al alcanzar la afinación correcta."""
        self.reproducir(frecuencia, duracion=duracion, amplitud=amplitud)
# ANCLAJE_FIN: generador_tonos
