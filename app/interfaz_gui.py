"""Ventana principal accesible del afinador cromático."""

import logging

import numpy as np
import wx

from app.motor_audio import (
    CapturadorYIN,
    GeneradorTonos,
    calcular_instruccion,
    listar_dispositivos_entrada,
    nota_a_frecuencia,
)
from app.conector_nvda import AnunciadorNVDA
from app.gestor_ajustes import cargar_ajustes, guardar_ajustes

logger = logging.getLogger(__name__)

TEXTOS_INSTRUCCION = {
    "AFINADA": "Afinada",
    "SUBE_POCO": "Sube un poco",
    "SUBE_BASTANTE": "Sube bastante",
    "BAJA_POCO": "Baja un poco",
    "BAJA_BASTANTE": "Baja bastante",
}

# índice de nota cromática: 0=Do, 1=Do#, 2=Re, 3=Re#, 4=Mi, 5=Fa, 6=Fa#, 7=Sol, 8=Sol#, 9=La, 10=La#, 11=Si
CROMATICO = "Cromático (cualquier nota)"

PRESETS_INSTRUMENTO = {
    CROMATICO: None,
    "Lira de 16 cuerdas (Aklot)": [
        ("Cuerda 1 (Sol)", 7, 3), ("Cuerda 2 (La)", 9, 3), ("Cuerda 3 (Si)", 11, 3), ("Cuerda 4 (Do)", 0, 4),
        ("Cuerda 5 (Re)", 2, 4), ("Cuerda 6 (Mi)", 4, 4), ("Cuerda 7 (Fa)", 5, 4), ("Cuerda 8 (Sol)", 7, 4),
        ("Cuerda 9 (La)", 9, 4), ("Cuerda 10 (Si)", 11, 4), ("Cuerda 11 (Do)", 0, 5), ("Cuerda 12 (Re)", 2, 5),
        ("Cuerda 13 (Mi)", 4, 5), ("Cuerda 14 (Fa)", 5, 5), ("Cuerda 15 (Sol)", 7, 5), ("Cuerda 16 (La)", 9, 5),
    ],
    "Ukelele": [
        ("Cuerda 1 (Sol)", 7, 4), ("Cuerda 2 (Do)", 0, 4),
        ("Cuerda 3 (Mi)", 4, 4), ("Cuerda 4 (La)", 9, 4),
    ],
    "Guitarra": [
        ("Cuerda 6 (Mi)", 4, 2), ("Cuerda 5 (La)", 9, 2), ("Cuerda 4 (Re)", 2, 3),
        ("Cuerda 3 (Sol)", 7, 3), ("Cuerda 2 (Si)", 11, 3), ("Cuerda 1 (Mi)", 4, 4),
    ],
}

OPCIONES_TASA_MUESTREO = [
    ("Automática (recomendada)", None),
    ("44100 Hz", 44100),
    ("48000 Hz", 48000),
    ("96000 Hz", 96000),
    ("192000 Hz", 192000),
]

OPCIONES_DURACION_VENTANA = [
    ("Baja latencia (50 ms)", 0.05),
    ("Equilibrada (100 ms)", 0.1),
    ("Alta precisión, notas graves (200 ms)", 0.2),
]

ID_ATAJO_REPRODUCIR_REFERENCIA = wx.NewIdRef()
ID_ATAJO_ALTERNAR_ESCUCHA = wx.NewIdRef()

NIVEL_MINIMO_SENAL_DIAGNOSTICO = 0.01
SEGUNDOS_ESPERA_DIAGNOSTICO_SENAL = 4.0


# ANCLAJE_INICIO: ventana_principal
class VentanaPrincipal(wx.Frame):
    """Ventana raíz del afinador. Controles nativos wx, accesibles por defecto."""

    def __init__(self):
        super().__init__(None, title="Afinador Accesible", size=(480, 480))

        self.ajustes = cargar_ajustes()
        self.anunciador = AnunciadorNVDA()
        self.capturador = None
        self.generador_tonos = GeneradorTonos(tasa_muestreo=44100)
        self._confirmacion_pendiente = True

        self._construir_controles()
        self._construir_atajos()
        self._cargar_dispositivos()
        self._aplicar_ajustes_guardados()

        self.Bind(wx.EVT_CLOSE, self._al_cerrar)
        self.Centre()
        self.Show()

    def _construir_controles(self):
        panel = wx.Panel(self)
        distribucion = wx.BoxSizer(wx.VERTICAL)

        etiqueta_dispositivo = wx.StaticText(panel, label="Dispositivo de entrada de audio:")
        self.selector_dispositivo = wx.Choice(panel)
        self.selector_dispositivo.Bind(wx.EVT_CHOICE, self._al_cambiar_dispositivo)

        etiqueta_tasa = wx.StaticText(panel, label="Tasa de muestreo:")
        self.selector_tasa = wx.Choice(panel, choices=[etiqueta for etiqueta, _ in OPCIONES_TASA_MUESTREO])
        self.selector_tasa.SetSelection(0)
        self.selector_tasa.Bind(wx.EVT_CHOICE, self._al_cambiar_calidad_captura)

        etiqueta_buffer = wx.StaticText(panel, label="Tamaño de búfer:")
        self.selector_buffer = wx.Choice(panel, choices=[etiqueta for etiqueta, _ in OPCIONES_DURACION_VENTANA])
        self.selector_buffer.SetSelection(1)
        self.selector_buffer.Bind(wx.EVT_CHOICE, self._al_cambiar_calidad_captura)

        etiqueta_instrumento = wx.StaticText(panel, label="Instrumento:")
        self.selector_instrumento = wx.Choice(panel, choices=list(PRESETS_INSTRUMENTO.keys()))
        self.selector_instrumento.SetSelection(0)
        self.selector_instrumento.Bind(wx.EVT_CHOICE, self._al_cambiar_instrumento)

        etiqueta_cuerda = wx.StaticText(panel, label="Cuerda objetivo:")
        self.selector_cuerda = wx.Choice(panel)
        self.selector_cuerda.Bind(wx.EVT_CHOICE, self._al_cambiar_cuerda)

        self.etiqueta_nota = wx.StaticText(panel, label="Nota detectada: —")
        self.etiqueta_instruccion = wx.StaticText(panel, label="Instrucción: —")
        self.etiqueta_nivel = wx.StaticText(panel, label="Nivel de entrada: —")

        self.boton_escucha = wx.Button(panel, label="Iniciar escucha (Ctrl+E)")
        self.boton_escucha.Bind(wx.EVT_BUTTON, self._al_alternar_escucha)

        self.boton_referencia = wx.Button(panel, label="Reproducir tono de referencia (Ctrl+P)")
        self.boton_referencia.Bind(wx.EVT_BUTTON, self._al_reproducir_referencia)

        for widget in (
            etiqueta_dispositivo, self.selector_dispositivo,
            etiqueta_tasa, self.selector_tasa,
            etiqueta_buffer, self.selector_buffer,
            etiqueta_instrumento, self.selector_instrumento,
            etiqueta_cuerda, self.selector_cuerda,
            self.etiqueta_nota, self.etiqueta_instruccion, self.etiqueta_nivel,
            self.boton_escucha, self.boton_referencia,
        ):
            distribucion.Add(widget, 0, wx.ALL | wx.EXPAND, 8)

        panel.SetSizer(distribucion)

    def _construir_atajos(self):
        """Ctrl+P reproduce el tono de referencia y Ctrl+E alterna la escucha, nunca Espacio."""
        self.Bind(wx.EVT_MENU, self._al_reproducir_referencia, id=ID_ATAJO_REPRODUCIR_REFERENCIA)
        self.Bind(wx.EVT_MENU, self._al_alternar_escucha, id=ID_ATAJO_ALTERNAR_ESCUCHA)
        tabla = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord("P"), ID_ATAJO_REPRODUCIR_REFERENCIA),
            (wx.ACCEL_CTRL, ord("E"), ID_ATAJO_ALTERNAR_ESCUCHA),
        ])
        self.SetAcceleratorTable(tabla)

    def _cargar_dispositivos(self):
        self.dispositivos = listar_dispositivos_entrada()
        self.selector_dispositivo.Clear()
        for dispositivo in self.dispositivos:
            self.selector_dispositivo.Append(dispositivo["nombre"])
        if self.dispositivos:
            self.selector_dispositivo.SetSelection(0)

    def _aplicar_ajustes_guardados(self):
        nombre_dispositivo = self.ajustes.get("nombre_dispositivo")
        if nombre_dispositivo:
            for posicion, dispositivo in enumerate(self.dispositivos):
                if dispositivo["nombre"] == nombre_dispositivo:
                    self.selector_dispositivo.SetSelection(posicion)
                    break

        tasa_guardada = self.ajustes.get("tasa_muestreo")
        for posicion, (_, valor) in enumerate(OPCIONES_TASA_MUESTREO):
            if valor == tasa_guardada:
                self.selector_tasa.SetSelection(posicion)
                break

        duracion_guardada = self.ajustes.get("duracion_ventana", 0.1)
        for posicion, (_, valor) in enumerate(OPCIONES_DURACION_VENTANA):
            if valor == duracion_guardada:
                self.selector_buffer.SetSelection(posicion)
                break

        nombre_instrumento = self.ajustes.get("instrumento")
        if nombre_instrumento and nombre_instrumento in PRESETS_INSTRUMENTO:
            self.selector_instrumento.SetStringSelection(nombre_instrumento)

        self._al_cambiar_instrumento(None)

        nombre_cuerda = self.ajustes.get("cuerda")
        if nombre_cuerda:
            posicion_cuerda = self.selector_cuerda.FindString(nombre_cuerda)
            if posicion_cuerda != wx.NOT_FOUND:
                self.selector_cuerda.SetSelection(posicion_cuerda)

    def _guardar_ajustes_actuales(self):
        posicion_dispositivo = self.selector_dispositivo.GetSelection()
        nombre_dispositivo = (
            self.dispositivos[posicion_dispositivo]["nombre"]
            if posicion_dispositivo != wx.NOT_FOUND and self.dispositivos
            else None
        )
        self.ajustes.update({
            "nombre_dispositivo": nombre_dispositivo,
            "instrumento": self.selector_instrumento.GetStringSelection(),
            "cuerda": self.selector_cuerda.GetStringSelection() or None,
            "tasa_muestreo": self._tasa_muestreo_seleccionada(),
            "duracion_ventana": self._duracion_ventana_seleccionada(),
        })
        guardar_ajustes(self.ajustes)

    def _tasa_muestreo_seleccionada(self):
        posicion = self.selector_tasa.GetSelection()
        if posicion == wx.NOT_FOUND:
            return None
        return OPCIONES_TASA_MUESTREO[posicion][1]

    def _duracion_ventana_seleccionada(self):
        posicion = self.selector_buffer.GetSelection()
        if posicion == wx.NOT_FOUND:
            return 0.1
        return OPCIONES_DURACION_VENTANA[posicion][1]

    def _preset_actual(self):
        nombre_instrumento = self.selector_instrumento.GetStringSelection()
        return PRESETS_INSTRUMENTO.get(nombre_instrumento)

    def _al_cambiar_instrumento(self, evento):
        preset = self._preset_actual()
        self.selector_cuerda.Clear()
        if preset is None:
            self.selector_cuerda.Disable()
        else:
            for nombre_cuerda, indice_nota, octava in preset:
                self.selector_cuerda.Append(nombre_cuerda)
            self.selector_cuerda.SetSelection(0)
            self.selector_cuerda.Enable()
        self.anunciador.reiniciar_estado()
        if evento is not None:
            self._guardar_ajustes_actuales()
            evento.Skip()

    def _al_cambiar_cuerda(self, evento):
        self.anunciador.reiniciar_estado()
        self._guardar_ajustes_actuales()
        evento.Skip()

    def _cuerda_objetivo(self):
        preset = self._preset_actual()
        if preset is None:
            return None
        indice = self.selector_cuerda.GetSelection()
        if indice == wx.NOT_FOUND:
            return None
        return preset[indice]

    def _al_cambiar_dispositivo(self, evento):
        self._guardar_ajustes_actuales()
        estaba_escuchando = self.capturador is not None
        if estaba_escuchando:
            self._detener_escucha()
            self._iniciar_escucha()
        evento.Skip()

    def _al_cambiar_calidad_captura(self, evento):
        self._guardar_ajustes_actuales()
        estaba_escuchando = self.capturador is not None
        if estaba_escuchando:
            self._detener_escucha()
            self._iniciar_escucha()
        evento.Skip()

    def _indice_dispositivo_seleccionado(self):
        posicion = self.selector_dispositivo.GetSelection()
        if posicion == wx.NOT_FOUND or not self.dispositivos:
            return None
        return self.dispositivos[posicion]["indice"]

    def _al_alternar_escucha(self, evento):
        if self.capturador is None:
            self._iniciar_escucha()
        else:
            self._detener_escucha()

    def _iniciar_escucha(self):
        indice_dispositivo = self._indice_dispositivo_seleccionado()
        tasa_muestreo = self._tasa_muestreo_seleccionada()
        duracion_ventana = self._duracion_ventana_seleccionada()
        self.capturador = CapturadorYIN(
            indice_dispositivo=indice_dispositivo,
            tasa_muestreo=tasa_muestreo,
            duracion_ventana=duracion_ventana,
            al_detectar=self._al_detectar_tono,
        )
        try:
            self.capturador.iniciar()
        except Exception:
            logger.exception("fallo al iniciar la captura de audio")
            self.capturador = None
            wx.MessageBox("No se pudo iniciar el dispositivo de entrada seleccionado.",
                           "Error de audio", wx.OK | wx.ICON_ERROR)
            return
        logger.info(
            "Escucha iniciada: dispositivo=%s tasa_muestreo=%s duracion_ventana=%s backend=%s",
            indice_dispositivo, tasa_muestreo, duracion_ventana, self.capturador.backend,
        )
        self.generador_tonos.capturador = self.capturador
        self.boton_escucha.SetLabel("Detener escucha (Ctrl+E)")
        self.anunciador.reiniciar_estado()
        self._nivel_maximo_observado = 0.0
        self._temporizador_diagnostico = wx.CallLater(
            int(SEGUNDOS_ESPERA_DIAGNOSTICO_SENAL * 1000), self._comprobar_senal_de_audio
        )

    def _detener_escucha(self):
        if getattr(self, "_temporizador_diagnostico", None) is not None:
            self._temporizador_diagnostico.Stop()
            self._temporizador_diagnostico = None
        if self.capturador is not None:
            self.capturador.detener()
            logger.info("Escucha detenida")
            self.capturador = None
            self.generador_tonos.capturador = None
        self.boton_escucha.SetLabel("Iniciar escucha (Ctrl+E)")
        self.etiqueta_nota.SetLabel("Nota detectada: —")
        self.etiqueta_instruccion.SetLabel("Instrucción: —")
        self.etiqueta_nivel.SetLabel("Nivel de entrada: —")

    def _comprobar_senal_de_audio(self):
        if self.capturador is None:
            return
        if self._nivel_maximo_observado < NIVEL_MINIMO_SENAL_DIAGNOSTICO:
            logger.warning(
                "No se detectó señal de audio por encima de %.4f tras %.0f segundos",
                NIVEL_MINIMO_SENAL_DIAGNOSTICO, SEGUNDOS_ESPERA_DIAGNOSTICO_SENAL,
            )
            self.anunciador.hablar(
                "No se detecta señal del micrófono. Comprueba que el dispositivo "
                "seleccionado sea el correcto y que no esté silenciado en Windows."
            )

    def _al_detectar_tono(self, resultado, rms):
        wx.CallAfter(self._actualizar_deteccion, resultado, rms)

    def _actualizar_deteccion(self, resultado, rms):
        self._nivel_maximo_observado = max(getattr(self, "_nivel_maximo_observado", 0.0), rms)
        self.etiqueta_nivel.SetLabel("Nivel de entrada: {:.3f}".format(rms))

        if resultado is None:
            self.etiqueta_nota.SetLabel("Nota detectada: —")
            self.etiqueta_instruccion.SetLabel("Instrucción: —")
            self.anunciador.reiniciar_estado()
            return

        cuerda_objetivo = self._cuerda_objetivo()
        if cuerda_objetivo is not None:
            _, indice_nota_objetivo, octava_objetivo = cuerda_objetivo
            frecuencia_objetivo = nota_a_frecuencia(indice_nota_objetivo, octava_objetivo)
            cents = 1200 * np.log2(resultado["frecuencia"] / frecuencia_objetivo)
        else:
            cents = resultado["cents"]

        instruccion = calcular_instruccion(cents)
        texto_instruccion = TEXTOS_INSTRUCCION.get(instruccion, "—")

        self.etiqueta_nota.SetLabel(
            "Nota detectada: {}{} ({:+.0f} cents)".format(resultado["nombre"], resultado["octava"], cents)
        )
        self.etiqueta_instruccion.SetLabel("Instrucción: {}".format(texto_instruccion))

        if instruccion != "AFINADA":
            self._confirmacion_pendiente = True
        self.anunciador.procesar_instruccion(texto_instruccion)
        if instruccion == "AFINADA" and self._confirmacion_pendiente:
            self._confirmacion_pendiente = False
            self.generador_tonos.reproducir_confirmacion()

    def _al_reproducir_referencia(self, evento):
        cuerda_objetivo = self._cuerda_objetivo()
        if cuerda_objetivo is not None:
            _, indice_nota, octava = cuerda_objetivo
            frecuencia = nota_a_frecuencia(indice_nota, octava)
        else:
            frecuencia = nota_a_frecuencia(9, 4)  # La4, referencia estándar en modo cromático
        self.generador_tonos.reproducir(frecuencia, duracion=2.0)

    def _al_cerrar(self, evento):
        self._guardar_ajustes_actuales()
        self._detener_escucha()
        evento.Skip()
# ANCLAJE_FIN: ventana_principal
