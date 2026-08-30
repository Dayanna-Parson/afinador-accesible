"""Captura de audio, detección de tono mediante YIN y generación de tonos de referencia."""

import logging
import queue
import threading
import time

import numpy as np
import sounddevice as sd

try:
    import motor_rust as _motor_rust
    if not hasattr(_motor_rust, "CapturadorYinRust"):
        # Si el proyecto se ejecuta desde la raíz del repositorio y la extensión no está
        # compilada, Python puede confundir la carpeta fuente motor_rust/ con un paquete
        # real (paquete de espacio de nombres, sin contenido). No es la extensión válida.
        raise ImportError("el módulo motor_rust encontrado no es la extensión compilada")
    _RUST_DISPONIBLE = True
except ImportError:
    _motor_rust = None
    _RUST_DISPONIBLE = False

logger = logging.getLogger(__name__)

FRECUENCIA_LA4 = 440.0
NOMBRES_NOTAS = ["Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]
INDICE_LA = 9


def establecer_frecuencia_la4(frecuencia):
    """Establece la referencia de concierto global usada por notas y tonos."""
    global FRECUENCIA_LA4
    FRECUENCIA_LA4 = float(frecuencia)


def obtener_frecuencia_la4():
    """Devuelve la referencia de concierto activa en hercios."""
    return FRECUENCIA_LA4


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
    indice_api_wasapi = _indice_hostapi_wasapi()
    dispositivos = []
    for indice, info in enumerate(sd.query_devices()):
        if info.get("max_input_channels", 0) <= 0:
            continue
        if indice_api_wasapi is not None and info.get("hostapi") != indice_api_wasapi:
            # PortAudio suele listar el mismo micrófono varias veces, una por cada API de
            # sonido (MME, DirectSound, WASAPI, WDM-KS), con nombres casi idénticos. Se
            # muestra solo la entrada WASAPI cuando existe: es la API moderna que usa el
            # propio Windows y la mayoría de aplicaciones, y evita duplicados confusos que
            # pueden capturar audio de forma distinta al resto del sistema.
            continue
        dispositivos.append({
            "indice": indice,
            "nombre": info["name"],
            "tasa_muestreo_defecto": int(info["default_samplerate"]),
        })
    return dispositivos


def _indice_hostapi_wasapi():
    try:
        apis = sd.query_hostapis()
    except Exception:
        logger.exception("no se pudieron consultar las APIs de audio del sistema")
        return None
    for indice, api in enumerate(apis):
        if "wasapi" in api.get("name", "").lower():
            return indice
    return None


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
        "indice_nota": indice_nota,
        "octava": octava,
        "frecuencia": frecuencia,
        "frecuencia_objetivo": frecuencia_objetivo,
        "cents": cents,
    }


def nota_a_frecuencia(indice_nota, octava):
    """Calcula la frecuencia exacta de una nota cromática a partir de su índice (0=Do) y octava."""
    semitonos_desde_la4 = (indice_nota - INDICE_LA) + (octava - 4) * 12
    return FRECUENCIA_LA4 * (2 ** (semitonos_desde_la4 / 12))


CENTS_POR_CUARTO_TONO = 50


def frecuencia_con_desplazamiento(indice_nota, octava, cuartos_tono=0):
    """Frecuencia de una nota cromática desplazada en cuartos de tono (50 cents cada uno).

    Permite afinar cuerdas a sostenidos/bemoles fuera de la escala diatónica de fábrica
    (con desplazamientos de 2 cuartos de tono = 1 semitono) o a los cuartos de tono
    intermedios que usa la música árabe (maqam), con un solo cuarto de tono.
    """
    frecuencia_base = nota_a_frecuencia(indice_nota, octava)
    return frecuencia_base * (2 ** (cuartos_tono * CENTS_POR_CUARTO_TONO / 1200))


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

    def __init__(self, indice_dispositivo=None, tasa_muestreo=None, duracion_ventana=0.1,
                 umbral_yin=0.15, umbral_rms=0.02, al_detectar=None, preferir_exclusivo_wasapi=False,
                 ganancia=1.0, canal_entrada=None):
        self.indice_dispositivo = indice_dispositivo
        self.tasa_muestreo = tasa_muestreo or self._tasa_muestreo_defecto(indice_dispositivo)
        self.canales = self._canales_defecto(indice_dispositivo)
        self.duracion_ventana = duracion_ventana
        self.tamano_ventana = max(int(self.tasa_muestreo * duracion_ventana), 1024)
        self.umbral_yin = umbral_yin
        self.umbral_rms = umbral_rms
        self.al_detectar = al_detectar
        self.preferir_exclusivo_wasapi = preferir_exclusivo_wasapi
        self.ganancia = ganancia
        self.canal_entrada = canal_entrada

        self._flujo = None
        self._ultimo_log_canales = 0.0
        self._ultimo_log_sin_nota = 0.0
        self._cola = queue.Queue(maxsize=2)
        self._hilo_analisis = None
        self._detener = threading.Event()
        self._pausado = threading.Event()

    @staticmethod
    def _tasa_muestreo_defecto(indice_dispositivo):
        try:
            info = sd.query_devices(indice_dispositivo, "input")
            return int(info["default_samplerate"])
        except Exception:
            logger.exception("no se pudo consultar la tasa de muestreo por defecto del dispositivo")
            return 44100

    @staticmethod
    def _canales_defecto(indice_dispositivo):
        """Algunos dispositivos compuestos (p. ej. "Varios micrófonos" de Windows, que
        combina varios elementos de un array con su propio procesamiento) solo entregan
        la señal real si se abren con todos sus canales; forzar un único canal puede dejar
        la captura casi muda aunque el dispositivo funcione bien en otras aplicaciones."""
        try:
            info = sd.query_devices(indice_dispositivo, "input")
            return max(int(info["max_input_channels"]), 1)
        except Exception:
            logger.exception("no se pudo consultar el número de canales del dispositivo")
            return 1

    def _callback_audio(self, indata, marcos, tiempo_info, estado):
        if estado:
            logger.warning("estado del flujo de entrada de audio: %s", estado)
        if self._pausado.is_set():
            return
        mono_alterno = None
        if self.canal_entrada is not None:
            mono = indata[:, self.canal_entrada]
        elif indata.shape[1] > 1:
            # "Varios micrófonos" y otros dispositivos compuestos de Windows combinan
            # elementos de array independientes en canales separados, no un estéreo real
            # de la misma fuente. Promediarlos a ciegas mezcla la señal periódica de la
            # cuerda con el ruido no correlacionado del resto de canales y destruye la
            # periodicidad que el YIN necesita para encontrar el tono, aunque el nivel
            # general (rms) del canal mezclado siga moviéndose con cada pulsación. Por eso
            # cada bloque se queda primero con el canal de mayor energía: normalmente es el
            # único que lleva señal útil, y los demás aportan solo ruido de fondo. Pero en
            # modo exclusivo WASAPI, un dispositivo de array real (varios micrófonos físicos
            # muy próximos) puede repartir la señal en dos canales de energía parecida, cada
            # uno con demasiado poco nivel por separado para que el YIN encuentre el tono;
            # ahí sí conviene promediarlos, porque las dos capturan la misma cuerda casi en
            # fase y sumar mejora la relación señal/ruido en vez de destruirla. Se guarda
            # también ese promedio como alternativa, por si el canal elegido no basta.
            energia_por_canal = np.sqrt(np.mean(indata.astype(np.float64) ** 2, axis=0))
            canal_elegido = int(np.argmax(energia_por_canal))
            mono = indata[:, canal_elegido]
            mono_alterno = indata.mean(axis=1)
            ahora = time.monotonic()
            if ahora - self._ultimo_log_canales >= 2.0:
                self._ultimo_log_canales = ahora
                logger.info(
                    "canal elegido=%s energia_por_canal=%s",
                    canal_elegido, np.round(energia_por_canal, 5).tolist(),
                )
        else:
            mono = indata[:, 0]
        if self.ganancia != 1.0:
            mono = np.clip(mono * self.ganancia, -1.0, 1.0)
            if mono_alterno is not None:
                mono_alterno = np.clip(mono_alterno * self.ganancia, -1.0, 1.0)
        bloque = (mono.copy(), mono_alterno.copy() if mono_alterno is not None else None)
        try:
            self._cola.put_nowait(bloque)
        except queue.Full:
            try:
                self._cola.get_nowait()
            except queue.Empty:
                pass
            try:
                self._cola.put_nowait(bloque)
            except queue.Full:
                pass

    def _bucle_analisis(self):
        while not self._detener.is_set():
            try:
                bloque, bloque_alterno = self._cola.get(timeout=0.2)
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
            if frecuencia is None and bloque_alterno is not None and self.preferir_exclusivo_wasapi:
                # El canal de mayor energía no bastó: puede ser un dispositivo de array
                # real cuya señal se reparte entre canales (ver _callback_audio). Se
                # reintenta con el promedio de todos los canales antes de dar el bloque
                # por silencioso. Solo tiene sentido en modo exclusivo WASAPI, donde el
                # nivel general es tan bajo que ningún canal por separado basta: en modo
                # compartido el canal elegido ya tiene energía de sobra, y promediarlo con
                # un canal débil (ruido, resonancia de otras cuerdas) puede colar una
                # frecuencia distinta a la real. Esa fue la causa de instrucciones de
                # afinación erráticas en modo compartido: el promedio recuperaba un tono
                # espurio en vez de devolver "sin nota" con más frecuencia de la deseada.
                try:
                    frecuencia = estimar_frecuencia_yin(bloque_alterno, self.tasa_muestreo, umbral=self.umbral_yin)
                except Exception:
                    logger.exception("fallo al estimar la frecuencia con YIN (canal promediado)")
                    frecuencia = None
                if frecuencia is not None:
                    logger.info("nota recuperada promediando canales tras fallar el canal elegido")
            resultado = frecuencia_a_nota(frecuencia) if frecuencia else None
            if resultado is None:
                ahora = time.monotonic()
                if ahora - self._ultimo_log_sin_nota >= 2.0:
                    self._ultimo_log_sin_nota = ahora
                    logger.info(
                        "señal presente (rms=%.4f) pero YIN no encontró candidato "
                        "por debajo del umbral_yin=%.2f",
                        rms, self.umbral_yin,
                    )
            if self.al_detectar:
                self.al_detectar(resultado, rms)

    def iniciar(self):
        if self._flujo is not None:
            return
        self._detener.clear()
        self._pausado.clear()
        self._hilo_analisis = threading.Thread(target=self._bucle_analisis, daemon=True)
        self._hilo_analisis.start()
        if self.canal_entrada is not None and self.canal_entrada >= self.canales:
            self._detener.set()
            self._hilo_analisis.join(timeout=1.0)
            self._hilo_analisis = None
            raise ValueError("el canal de entrada seleccionado no existe en este dispositivo")
        argumentos_flujo = dict(
            device=self.indice_dispositivo,
            channels=self.canales,
            samplerate=self.tasa_muestreo,
            blocksize=self.tamano_ventana,
            callback=self._callback_audio,
        )

        ajustes_exclusivos_wasapi = self._ajustes_exclusivos_wasapi() if self.preferir_exclusivo_wasapi else None
        if ajustes_exclusivos_wasapi is not None:
            try:
                self._flujo = sd.InputStream(extra_settings=ajustes_exclusivos_wasapi, **argumentos_flujo)
                self._flujo.start()
                logger.info("Captura abierta en modo exclusivo WASAPI (sin procesamiento de Windows)")
                self._ajustar_tasa_muestreo_real()
                return
            except Exception:
                logger.warning(
                    "no se pudo abrir el dispositivo en modo exclusivo WASAPI; se usa el modo "
                    "compartido habitual, con el procesamiento de audio de Windows activo",
                    exc_info=True,
                )
                self._flujo = None

        self._flujo = sd.InputStream(**argumentos_flujo)
        self._flujo.start()
        self._ajustar_tasa_muestreo_real()

    def _ajustar_tasa_muestreo_real(self):
        """En modo exclusivo WASAPI el dispositivo puede aceptar la apertura sin lanzar
        ningún error y aun así entregar el audio a una tasa de muestreo distinta de la
        pedida (el hardware solo admite su formato nativo fijo). Si el YIN sigue
        calculando con la tasa que se pidió en vez de la que realmente está llegando,
        cada bloque de audio real acaba comparado contra una ventana de tiempo
        equivocada y la periodicidad de la cuerda nunca coincide con ningún candidato,
        aunque la señal (rms) se vea perfectamente viva. Se corrige leyendo la tasa que
        el propio flujo confirma tras abrirse."""
        tasa_real = getattr(self._flujo, "samplerate", None)
        if tasa_real and abs(tasa_real - self.tasa_muestreo) > 1:
            logger.warning(
                "la tasa de muestreo real del flujo (%s Hz) no coincide con la pedida (%s Hz); "
                "se usa la real para la detección de tono",
                tasa_real, self.tasa_muestreo,
            )
            self.tasa_muestreo = float(tasa_real)

    @staticmethod
    def _ajustes_exclusivos_wasapi():
        """El modo compartido de WASAPI pasa el audio por la cadena de mejoras de Windows
        (reducción de ruido, cancelación de eco, optimizaciones de voz), pensada para
        llamadas y dictado por voz, que puede atenuar o filtrar el sonido de un
        instrumento acústico. El modo exclusivo entrega el audio crudo del hardware,
        sin ese procesamiento — pero solo tiene sentido con un micrófono físico real:
        en un dispositivo compuesto o virtual (p. ej. "Varios micrófonos" de Windows,
        que combina varios elementos de un array mediante su propio procesamiento por
        software) el modo exclusivo puede saltarse precisamente esa combinación y dejar
        la captura casi muda, aunque el modo compartido funcione bien. Por eso está
        desactivado por defecto (preferir_exclusivo_wasapi=False) y es opt-in. Solo se
        intenta si el sistema tiene realmente WASAPI (Windows); en cualquier otro caso
        se devuelve None y se usa el modo habitual."""
        if _indice_hostapi_wasapi() is None:
            return None
        try:
            return sd.WasapiSettings(exclusive=True)
        except Exception:
            logger.exception("no se pudo construir la configuración exclusiva de WASAPI")
            return None

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

    def __init__(self, indice_dispositivo=None, tasa_muestreo=None, duracion_ventana=0.1,
                 umbral_yin=0.15, umbral_rms=0.02, al_detectar=None, preferir_exclusivo_wasapi=False,
                 ganancia=1.0, canal_entrada=None):
        self.al_detectar = al_detectar
        if _RUST_DISPONIBLE:
            self._backend = "rust"
            self._nucleo = _motor_rust.CapturadorYinRust(
                self._al_detectar_rust, indice_dispositivo, umbral_yin, umbral_rms,
                tasa_muestreo, duracion_ventana, ganancia, canal_entrada,
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
                preferir_exclusivo_wasapi=preferir_exclusivo_wasapi,
                ganancia=ganancia,
                canal_entrada=canal_entrada,
            )

    @property
    def backend(self):
        """Devuelve "rust" o "python" según el backend de captura realmente en uso."""
        return self._backend

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
        self._detener_bucle = threading.Event()
        self._bloqueo_reproduccion = threading.Lock()
        self._identificador_reproduccion = 0

    def _iniciar_reproduccion(self):
        """Invalida cualquier reproducción anterior y devuelve su nuevo identificador.

        sounddevice reproduce un único flujo global: serializarlo evita que una escucha
        previa, una referencia y un pitido de confirmación se corten o reanuden la captura
        fuera de orden.
        """
        with self._bloqueo_reproduccion:
            self._identificador_reproduccion += 1
            self._detener_bucle.set()
            return self._identificador_reproduccion

    def _es_reproduccion_actual(self, identificador):
        with self._bloqueo_reproduccion:
            return identificador == self._identificador_reproduccion

    def _finalizar_reproduccion(self, identificador, al_finalizar=None):
        """Reanuda la captura solo si esta reproducción sigue siendo la activa."""
        with self._bloqueo_reproduccion:
            if identificador != self._identificador_reproduccion:
                return
            if self.capturador is not None:
                self.capturador.reanudar()
        if al_finalizar:
            al_finalizar()

    @staticmethod
    def _compensar_percepcion_grave(frecuencia, amplitud):
        """Las frecuencias graves se perciben más flojas a igual amplitud (curvas isofónicas)
        y además los altavoces pequeños las reproducen peor; se compensa subiendo el nivel
        de las notas por debajo de 200 Hz, sin llegar a saturar la onda."""
        if frecuencia >= 200.0:
            return amplitud
        factor = 1.0 + (200.0 - frecuencia) / 200.0
        return min(amplitud * factor, 0.95)

    # Amplitud relativa de cada armónico sobre la fundamental, para que el tono de
    # referencia suene a cuerda pulsada en vez de a pitido electrónico plano.
    AMPLITUDES_ARMONICOS = (1.0, 0.35, 0.18, 0.09)

    def _generar_onda(self, frecuencia, duracion, amplitud=0.3):
        muestras = int(self.tasa_muestreo * duracion)
        tiempo = np.linspace(0, duracion, muestras, endpoint=False)
        amplitud_efectiva = self._compensar_percepcion_grave(frecuencia, amplitud)

        onda = np.zeros(muestras)
        for indice_armonico, amplitud_relativa in enumerate(self.AMPLITUDES_ARMONICOS, start=1):
            onda += amplitud_relativa * np.sin(2 * np.pi * frecuencia * indice_armonico * tiempo)
        onda *= amplitud_efectiva / sum(self.AMPLITUDES_ARMONICOS)

        rampa = min(int(self.tasa_muestreo * 0.01), muestras // 2)
        if rampa > 0:
            envolvente = np.ones(muestras)
            envolvente[:rampa] = np.linspace(0, 1, rampa)
            envolvente[-rampa:] = np.linspace(1, 0, rampa)
            onda *= envolvente
        return onda.astype(np.float32)

    def _reproducir_bloqueante(self, frecuencia, duracion, amplitud, al_finalizar, identificador):
        if self.capturador is not None:
            self.capturador.pausar()
        try:
            if not self._es_reproduccion_actual(identificador):
                return
            onda = self._generar_onda(frecuencia, duracion, amplitud)
            sd.play(onda, samplerate=self.tasa_muestreo, blocking=True)
        except Exception:
            logger.exception("fallo al reproducir el tono de referencia")
        finally:
            self._finalizar_reproduccion(identificador, al_finalizar)

    def reproducir(self, frecuencia, duracion=2.0, amplitud=0.45, al_finalizar=None):
        """Reproduce el tono en un hilo secundario, pausando la captura mientras suena."""
        identificador = self._iniciar_reproduccion()
        sd.stop()
        self._hilo_reproduccion = threading.Thread(
            target=self._reproducir_bloqueante,
            args=(frecuencia, duracion, amplitud, al_finalizar, identificador),
            daemon=True,
        )
        self._hilo_reproduccion.start()

    def _reproducir_en_bucle(self, frecuencia, duracion, pausa, amplitud, identificador):
        if self.capturador is not None:
            self.capturador.pausar()
        try:
            onda = self._generar_onda(frecuencia, duracion, amplitud)
            while self._es_reproduccion_actual(identificador) and not self._detener_bucle.is_set():
                sd.play(onda, samplerate=self.tasa_muestreo, blocking=True)
                if self._detener_bucle.wait(timeout=pausa):
                    break
        except Exception:
            logger.exception("fallo al reproducir el tono de referencia en bucle")
        finally:
            sd.stop()
            self._finalizar_reproduccion(identificador)

    def reproducir_en_bucle(self, frecuencia, duracion=1.2, pausa=0.4, amplitud=0.45):
        """Repite el tono de referencia indefinidamente hasta llamar a detener_bucle()."""
        identificador = self._iniciar_reproduccion()
        self._detener_bucle.clear()
        sd.stop()
        self._hilo_reproduccion = threading.Thread(
            target=self._reproducir_en_bucle,
            args=(frecuencia, duracion, pausa, amplitud, identificador),
            daemon=True,
        )
        self._hilo_reproduccion.start()

    def detener_bucle(self):
        identificador = self._iniciar_reproduccion()
        sd.stop()
        self._finalizar_reproduccion(identificador)

    def _reproducir_secuencia(self, frecuencias, duracion, pausa, amplitud, al_finalizar, identificador):
        if self.capturador is not None:
            self.capturador.pausar()
        try:
            for frecuencia in frecuencias:
                if not self._es_reproduccion_actual(identificador) or self._detener_bucle.is_set():
                    break
                onda = self._generar_onda(frecuencia, duracion, amplitud)
                sd.play(onda, samplerate=self.tasa_muestreo, blocking=True)
                if self._detener_bucle.wait(timeout=pausa):
                    break
        except Exception:
            logger.exception("fallo al reproducir la afinación completa")
        finally:
            sd.stop()
            self._finalizar_reproduccion(identificador, al_finalizar)

    def reproducir_secuencia(self, frecuencias, duracion=0.6, pausa=0.15, amplitud=0.45, al_finalizar=None):
        """Reproduce una lista de frecuencias en orden, una sola vez (reproducir la afinación completa).

        Se puede interrumpir a mitad con detener_bucle(), igual que reproducir_en_bucle().
        """
        identificador = self._iniciar_reproduccion()
        self._detener_bucle.clear()
        sd.stop()
        self._hilo_reproduccion = threading.Thread(
            target=self._reproducir_secuencia,
            args=(frecuencias, duracion, pausa, amplitud, al_finalizar, identificador),
            daemon=True,
        )
        self._hilo_reproduccion.start()

    def reproducir_confirmacion(self, frecuencia=880.0, duracion=0.15, amplitud=0.25):
        """Pitido corto de confirmación al alcanzar la afinación correcta."""
        self.reproducir(frecuencia, duracion=duracion, amplitud=amplitud)
# ANCLAJE_FIN: generador_tonos
