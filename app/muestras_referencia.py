"""Sonidos grabados para el tono de referencia, en lugar de la onda sintética.

Cada archivo WAV de ``recursos/sonidos/referencias/`` lleva en su nombre la frecuencia
exacta de la nota que suena (por ejemplo ``09_cuerda_9_La4_440,00Hz.wav``). Para
reproducir cualquier frecuencia se elige el sonido más cercano y se reproduce más
rápido o más despacio hasta que suena exactamente en la frecuencia pedida, así que
sirven igual para cuerdas con retoque, para otra referencia de La4 o para otro
instrumento. Si un instrumento tiene su propia subcarpeta (``referencias/guitarra/``,
``referencias/ukelele/``, ``referencias/lira/``), sus sonidos tienen prioridad sobre los
generales. Sin sonidos utilizables, el llamador recae en la onda sintética.

Sin wx: se puede probar sin pantalla ni tarjeta de sonido.
"""

import logging
import os
import re
import wave

import numpy as np

from app.config_rutas import RAIZ

logger = logging.getLogger(__name__)

RUTA_SONIDOS_REFERENCIA = os.path.join(RAIZ, "recursos", "sonidos", "referencias")

# Acepta coma o punto decimal: "196,00Hz", "196.00 Hz", "196Hz".
_PATRON_FRECUENCIA = re.compile(r"(\d+(?:[.,]\d+)?)\s*Hz", re.IGNORECASE)
SEGUNDOS_FUNDIDO_FINAL = 0.08


# ANCLAJE_INICIO: BANCO_MUESTRAS_REFERENCIA
def frecuencia_desde_nombre(nombre_archivo):
    """Frecuencia en hercios escrita en el nombre del archivo, o None si no la lleva."""
    coincidencia = _PATRON_FRECUENCIA.search(os.path.basename(nombre_archivo))
    if not coincidencia:
        return None
    try:
        frecuencia = float(coincidencia.group(1).replace(",", "."))
    except ValueError:
        return None
    return frecuencia if frecuencia > 0 else None


def _leer_wav_mono(ruta):
    """Devuelve (muestras float32 en [-1, 1], tasa de muestreo) de un WAV PCM."""
    with wave.open(ruta, "rb") as archivo:
        canales = archivo.getnchannels()
        ancho = archivo.getsampwidth()
        tasa = archivo.getframerate()
        datos = archivo.readframes(archivo.getnframes())
    if ancho == 1:
        muestras = (np.frombuffer(datos, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    elif ancho == 2:
        muestras = np.frombuffer(datos, dtype="<i2").astype(np.float32) / 32768.0
    elif ancho == 3:
        bytes_crudos = np.frombuffer(datos, dtype=np.uint8).reshape(-1, 3)
        enteros = (bytes_crudos[:, 0].astype(np.int32)
                   | (bytes_crudos[:, 1].astype(np.int32) << 8)
                   | (bytes_crudos[:, 2].astype(np.int32) << 16))
        enteros = np.where(enteros & 0x800000, enteros - 0x1000000, enteros)
        muestras = enteros.astype(np.float32) / 8388608.0
    elif ancho == 4:
        muestras = np.frombuffer(datos, dtype="<i4").astype(np.float32) / 2147483648.0
    else:
        raise ValueError("ancho de muestra no admitido: {} bytes".format(ancho))
    if canales > 1:
        muestras = muestras.reshape(-1, canales).mean(axis=1)
    return muestras, tasa


class BancoMuestrasReferencia:
    """Carga perezosa de los sonidos de referencia y su reproducción a cualquier frecuencia."""

    def __init__(self, ruta_base=RUTA_SONIDOS_REFERENCIA):
        self._ruta_base = ruta_base
        self._indices = {}
        self._cache_muestras = {}

    def _indice_carpeta(self, carpeta):
        """Lista de (frecuencia, ruta) de los WAV con frecuencia en el nombre de una carpeta."""
        if carpeta in self._indices:
            return self._indices[carpeta]
        indice = []
        if os.path.isdir(carpeta):
            for nombre in sorted(os.listdir(carpeta)):
                if not nombre.lower().endswith(".wav"):
                    continue
                frecuencia = frecuencia_desde_nombre(nombre)
                if frecuencia is None:
                    logger.warning("sonido de referencia sin frecuencia en el nombre, se ignora: %s", nombre)
                    continue
                indice.append((frecuencia, os.path.join(carpeta, nombre)))
        self._indices[carpeta] = indice
        return indice

    def _candidatos(self, carpeta_instrumento):
        if carpeta_instrumento:
            propios = self._indice_carpeta(os.path.join(self._ruta_base, carpeta_instrumento))
            if propios:
                return propios
        return self._indice_carpeta(self._ruta_base)

    def hay_muestras(self, carpeta_instrumento=None):
        return bool(self._candidatos(carpeta_instrumento))

    def _muestra(self, ruta):
        if ruta not in self._cache_muestras:
            self._cache_muestras[ruta] = _leer_wav_mono(ruta)
        return self._cache_muestras[ruta]

    def generar_onda(self, frecuencia, duracion, tasa_salida, amplitud, carpeta_instrumento=None):
        """Onda float32 de la duración pedida sonando en `frecuencia`, o None si no hay sonidos."""
        candidatos = self._candidatos(carpeta_instrumento)
        if not candidatos or frecuencia <= 0 or duracion <= 0:
            return None
        frecuencia_origen, ruta = min(candidatos, key=lambda par: abs(np.log2(frecuencia / par[0])))
        try:
            muestras, tasa_origen = self._muestra(ruta)
        except Exception:
            logger.exception("no se pudo leer el sonido de referencia %s", ruta)
            return None
        if muestras.size == 0:
            return None

        # Reproducir el sonido a otra velocidad cambia su altura en la misma proporción:
        # cada muestra de salida avanza `paso` muestras del original.
        paso = (frecuencia / frecuencia_origen) * (tasa_origen / tasa_salida)
        muestras_salida = int(tasa_salida * duracion)
        posiciones = np.arange(muestras_salida, dtype=np.float64) * paso
        posiciones = posiciones[posiciones <= muestras.size - 1]
        if posiciones.size == 0:
            return None
        onda = np.interp(posiciones, np.arange(muestras.size), muestras).astype(np.float32)

        pico = float(np.max(np.abs(onda)))
        if pico > 0:
            onda *= amplitud / pico
        fundido = min(int(tasa_salida * SEGUNDOS_FUNDIDO_FINAL), onda.size // 2)
        if fundido > 0:
            onda[-fundido:] *= np.linspace(1.0, 0.0, fundido, dtype=np.float32)
        return onda
# ANCLAJE_FIN: BANCO_MUESTRAS_REFERENCIA
