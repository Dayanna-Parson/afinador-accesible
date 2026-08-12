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
    "Lira de 16 cuerdas": [
        ("Cuerda 1", 0, 3), ("Cuerda 2", 2, 3), ("Cuerda 3", 4, 3), ("Cuerda 4", 5, 3),
        ("Cuerda 5", 7, 3), ("Cuerda 6", 9, 3), ("Cuerda 7", 11, 3), ("Cuerda 8", 0, 4),
        ("Cuerda 9", 2, 4), ("Cuerda 10", 4, 4), ("Cuerda 11", 5, 4), ("Cuerda 12", 7, 4),
        ("Cuerda 13", 9, 4), ("Cuerda 14", 11, 4), ("Cuerda 15", 0, 5), ("Cuerda 16", 2, 5),
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


# ANCLAJE_INICIO: ventana_principal
class VentanaPrincipal(wx.Frame):
    """Ventana raíz del afinador. Controles nativos wx, accesibles por defecto."""

    def __init__(self):
        super().__init__(None, title="Afinador Accesible", size=(480, 400))

        self.anunciador = AnunciadorNVDA()
        self.capturador = None
        self.generador_tonos = GeneradorTonos(tasa_muestreo=44100)
        self._confirmacion_pendiente = True

        self._construir_controles()
        self._cargar_dispositivos()
        self._al_cambiar_instrumento(None)

        self.Bind(wx.EVT_CLOSE, self._al_cerrar)
        self.Centre()
        self.Show()

    def _construir_controles(self):
        panel = wx.Panel(self)
        distribucion = wx.BoxSizer(wx.VERTICAL)

        etiqueta_dispositivo = wx.StaticText(panel, label="Dispositivo de entrada de audio:")
        self.selector_dispositivo = wx.Choice(panel)
        self.selector_dispositivo.Bind(wx.EVT_CHOICE, self._al_cambiar_dispositivo)

        etiqueta_instrumento = wx.StaticText(panel, label="Instrumento:")
        self.selector_instrumento = wx.Choice(panel, choices=list(PRESETS_INSTRUMENTO.keys()))
        self.selector_instrumento.SetSelection(0)
        self.selector_instrumento.Bind(wx.EVT_CHOICE, self._al_cambiar_instrumento)

        etiqueta_cuerda = wx.StaticText(panel, label="Cuerda objetivo:")
        self.selector_cuerda = wx.Choice(panel)
        self.selector_cuerda.Bind(wx.EVT_CHOICE, self._al_cambiar_cuerda)

        self.etiqueta_nota = wx.StaticText(panel, label="Nota detectada: —")
        self.etiqueta_instruccion = wx.StaticText(panel, label="Instrucción: —")

        self.boton_escucha = wx.Button(panel, label="Iniciar escucha")
        self.boton_escucha.Bind(wx.EVT_BUTTON, self._al_alternar_escucha)

        self.boton_referencia = wx.Button(panel, label="Reproducir tono de referencia")
        self.boton_referencia.Bind(wx.EVT_BUTTON, self._al_reproducir_referencia)

        for widget in (
            etiqueta_dispositivo, self.selector_dispositivo,
            etiqueta_instrumento, self.selector_instrumento,
            etiqueta_cuerda, self.selector_cuerda,
            self.etiqueta_nota, self.etiqueta_instruccion,
            self.boton_escucha, self.boton_referencia,
        ):
            distribucion.Add(widget, 0, wx.ALL | wx.EXPAND, 8)

        panel.SetSizer(distribucion)

    def _cargar_dispositivos(self):
        self.dispositivos = listar_dispositivos_entrada()
        self.selector_dispositivo.Clear()
        for dispositivo in self.dispositivos:
            self.selector_dispositivo.Append(dispositivo["nombre"])
        if self.dispositivos:
            self.selector_dispositivo.SetSelection(0)

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
            evento.Skip()

    def _al_cambiar_cuerda(self, evento):
        self.anunciador.reiniciar_estado()
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
        self.capturador = CapturadorYIN(
            indice_dispositivo=self._indice_dispositivo_seleccionado(),
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
        self.generador_tonos.capturador = self.capturador
        self.boton_escucha.SetLabel("Detener escucha")
        self.anunciador.reiniciar_estado()

    def _detener_escucha(self):
        if self.capturador is not None:
            self.capturador.detener()
            self.capturador = None
            self.generador_tonos.capturador = None
        self.boton_escucha.SetLabel("Iniciar escucha")
        self.etiqueta_nota.SetLabel("Nota detectada: —")
        self.etiqueta_instruccion.SetLabel("Instrucción: —")

    def _al_detectar_tono(self, resultado, rms):
        wx.CallAfter(self._actualizar_deteccion, resultado)

    def _actualizar_deteccion(self, resultado):
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
        self._detener_escucha()
        evento.Skip()
# ANCLAJE_FIN: ventana_principal
