"""Ventana principal accesible del afinador cromático."""

import logging
import statistics
import time
from collections import deque

import numpy as np
import wx

from app.motor_audio import (
    CapturadorYIN,
    CENTS_POR_CUARTO_TONO,
    GeneradorTonos,
    calcular_instruccion,
    frecuencia_a_nota,
    frecuencia_con_desplazamiento,
    listar_dispositivos_entrada,
    nota_a_frecuencia,
)
from app.conector_nvda import AnunciadorNVDA
from app.control_microfono import asegurar_microfono_activo
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

NOMBRE_LIRA = "Lira de 16 cuerdas (Aklot)"
NOMBRE_GUITARRA = "Guitarra"
NOMBRE_UKELELE = "Ukelele"

# Desplazamiento en cuartos de tono (50 cents cada uno) sobre la afinación de fábrica de
# cada instrumento, por escala/afinación. Todos los valores son múltiplos de 2 (semitonos
# completos) salvo los maqam de la lira, que usan cuartos de tono sueltos a propósito.
#
# Lira: patrones verificados contra la teoría estándar de intervalos en cuartos de tono
# (Touma, "The Music of the Arabs"): Rast sobre Sol (4,3,3,4,4,3,3 cuartos de tono desde la
# tónica), Bayati sobre Re (3,3,4,4,2,4,4) e Hijaz sobre Re (2,6,2,4,2,4,4). Al coincidir la
# afinación diatónica de la lira con las notas naturales, solo hace falta retocar las
# cuerdas cuyo grado cambia respecto al maqam.
#
# Guitarra y ukelele: afinaciones alternativas estándar, ampliamente documentadas. En un
# instrumento con trastes el retoque solo desplaza la cuerda al aire entera — los trastes
# siguen fijos en semitonos occidentales, así que estas afinaciones no dan acceso a cuartos
# de tono nuevos en el mástil, solo a otras disposiciones de acordes/resonancias.
ESCALAS_POR_INSTRUMENTO = {
    NOMBRE_LIRA: {
        "Diatónica de fábrica": {},
        "Maqam Rast (sobre Sol)": {
            "Cuerda 3 (Si)": -1, "Cuerda 7 (Fa)": 1, "Cuerda 10 (Si)": -1, "Cuerda 14 (Fa)": 1,
        },
        "Maqam Bayati (sobre Re)": {
            "Cuerda 3 (Si)": -2, "Cuerda 6 (Mi)": -1, "Cuerda 10 (Si)": -2, "Cuerda 13 (Mi)": -1,
        },
        "Maqam Hijaz (sobre Re)": {
            "Cuerda 3 (Si)": -2, "Cuerda 6 (Mi)": -2, "Cuerda 7 (Fa)": 2,
            "Cuerda 10 (Si)": -2, "Cuerda 13 (Mi)": -2, "Cuerda 14 (Fa)": 2,
        },
    },
    NOMBRE_GUITARRA: {
        "Estándar (Mi La Re Sol Si Mi)": {},
        "Drop D (Re La Re Sol Si Mi)": {"Cuerda 6 (Mi)": -4},
        "Open G (Re Sol Re Sol Si Re)": {"Cuerda 6 (Mi)": -4, "Cuerda 5 (La)": -4, "Cuerda 1 (Mi)": -4},
        "Open D (Re La Re Fa# La Re)": {
            "Cuerda 6 (Mi)": -4, "Cuerda 3 (Sol)": -2, "Cuerda 2 (Si)": -4, "Cuerda 1 (Mi)": -4,
        },
        "DADGAD (Re La Re Sol La Re)": {"Cuerda 6 (Mi)": -4, "Cuerda 2 (Si)": -4, "Cuerda 1 (Mi)": -4},
        "Open C (Do Sol Do Sol Do Mi)": {
            "Cuerda 6 (Mi)": -8, "Cuerda 5 (La)": -4, "Cuerda 4 (Re)": -4, "Cuerda 2 (Si)": 2,
        },
        "Open E (Mi Si Mi Sol# Si Mi)": {
            "Cuerda 5 (La)": 4, "Cuerda 4 (Re)": 4, "Cuerda 3 (Sol)": 2,
        },
        "Open A (Mi La Mi La Do# Mi)": {
            "Cuerda 4 (Re)": 4, "Cuerda 3 (Sol)": 4, "Cuerda 2 (Si)": 4,
        },
    },
    NOMBRE_UKELELE: {
        "Estándar (Sol Do Mi La, reentrante)": {},
        "Sol grave (Low G, sin reentrancia)": {"Cuerda 1 (Sol)": -24},
        "Afinación Re tradicional (La Re Fa# Si)": {
            "Cuerda 1 (Sol)": 4, "Cuerda 2 (Do)": 4, "Cuerda 3 (Mi)": 4, "Cuerda 4 (La)": 4,
        },
    },
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
ID_ATAJO_SUBIR_CUARTO_TONO = wx.NewIdRef()
ID_ATAJO_BAJAR_CUARTO_TONO = wx.NewIdRef()
ID_ATAJO_RESTABLECER_AJUSTE_FINO = wx.NewIdRef()

NIVEL_MINIMO_SENAL_DIAGNOSTICO = 0.01
NIVEL_SENAL_BUENA = 0.08
SEGUNDOS_ESPERA_DIAGNOSTICO_SENAL = 4.0
SEGUNDOS_ESTABLE_PARA_AVANZAR = 1.2
SEGUNDOS_MARGEN_SILENCIO_ENTRE_NOTAS = 0.5
TAMANO_HISTORIAL_FRECUENCIAS = 5


# ANCLAJE_INICIO: ventana_principal
class VentanaPrincipal(wx.Frame):
    """Ventana raíz del afinador. Controles nativos wx, accesibles por defecto."""

    def __init__(self):
        super().__init__(None, title="Afinador Accesible", size=(480, 480))

        self.ajustes = cargar_ajustes()
        self.ajustes_finos_cuerdas = dict(self.ajustes.get("ajustes_finos_cuerdas", {}))
        self.anunciador = AnunciadorNVDA()
        self.capturador = None
        self.generador_tonos = GeneradorTonos(tasa_muestreo=44100)
        self._confirmacion_pendiente = True
        self._afinada_desde = None
        self._avance_ya_realizado = False
        self._ultima_categoria_nivel = None
        self._senal_confirmada_una_vez = False
        self._marca_tiempo_ultima_nota = 0.0
        self._historial_frecuencias = deque(maxlen=TAMANO_HISTORIAL_FRECUENCIAS)
        self._reproduciendo_en_bucle = False

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

        etiqueta_escala = wx.StaticText(panel, label="Escala / afinación:")
        self.selector_escala = wx.Choice(panel)
        self.selector_escala.Bind(wx.EVT_CHOICE, self._al_cambiar_escala)

        self.casilla_avance_automatico = wx.CheckBox(panel, label="Avanzar automáticamente a la siguiente cuerda al afinar")
        self.casilla_avance_automatico.SetValue(True)
        self.casilla_avance_automatico.Bind(wx.EVT_CHECKBOX, self._al_cambiar_ajuste_simple)

        self.casilla_exclusivo_wasapi = wx.CheckBox(
            panel, label="Modo exclusivo WASAPI (solo micrófonos dedicados; puede fallar con "
                         "dispositivos compuestos como \"Varios micrófonos\")"
        )
        self.casilla_exclusivo_wasapi.SetValue(False)
        self.casilla_exclusivo_wasapi.Bind(wx.EVT_CHECKBOX, self._al_cambiar_calidad_captura)

        etiqueta_ganancia = wx.StaticText(panel, label="Ganancia de entrada:")
        self.control_ganancia = wx.SpinCtrlDouble(
            panel, min=1.0, max=5.0, initial=1.0, inc=0.5
        )
        self.control_ganancia.SetDigits(1)
        self.control_ganancia.SetLabel("Ganancia de entrada")
        self.control_ganancia.Bind(wx.EVT_SPINCTRLDOUBLE, self._al_cambiar_calidad_captura)
        # SpinCtrlDouble no toma el nombre accesible del StaticText contiguo ni respeta
        # siempre SetLabel() en NVDA: se anuncia el valor con voz propia al recibir el foco,
        # el mismo patrón que ya se usa en el resto de la app para lo que SetLabel() no cubre.
        self.control_ganancia.Bind(wx.EVT_SET_FOCUS, self._al_enfocar_control_ganancia)

        etiqueta_sensibilidad = wx.StaticText(panel, label="Sensibilidad de detección (más alto = más permisivo):")
        self.control_sensibilidad = wx.SpinCtrlDouble(
            panel, min=0.05, max=0.40, initial=0.15, inc=0.05
        )
        self.control_sensibilidad.SetDigits(2)
        self.control_sensibilidad.SetLabel("Sensibilidad de detección")
        self.control_sensibilidad.Bind(wx.EVT_SPINCTRLDOUBLE, self._al_cambiar_calidad_captura)
        self.control_sensibilidad.Bind(wx.EVT_SET_FOCUS, self._al_enfocar_control_sensibilidad)

        self.etiqueta_nota = wx.StaticText(panel, label="Nota detectada: —")
        self.etiqueta_instruccion = wx.StaticText(panel, label="Instrucción: —")
        self.etiqueta_nivel = wx.StaticText(panel, label="Nivel de entrada: —")

        self.boton_escucha = wx.Button(panel, label="Iniciar escucha (Ctrl+E)")
        self.boton_escucha.Bind(wx.EVT_BUTTON, self._al_alternar_escucha)

        self.boton_referencia = wx.Button(panel, label="Reproducir tono de referencia (Ctrl+P)")
        self.boton_referencia.Bind(wx.EVT_BUTTON, self._al_reproducir_referencia)

        self.casilla_bucle_referencia = wx.CheckBox(panel, label="Repetir el tono de referencia en bucle")
        self.casilla_bucle_referencia.SetValue(False)
        self.casilla_bucle_referencia.Bind(wx.EVT_CHECKBOX, self._al_cambiar_ajuste_bucle)

        for widget in (
            etiqueta_dispositivo, self.selector_dispositivo,
            etiqueta_tasa, self.selector_tasa,
            etiqueta_buffer, self.selector_buffer,
            etiqueta_instrumento, self.selector_instrumento,
            etiqueta_cuerda, self.selector_cuerda,
            etiqueta_escala, self.selector_escala,
            self.casilla_avance_automatico,
            self.casilla_exclusivo_wasapi,
            etiqueta_ganancia, self.control_ganancia,
            etiqueta_sensibilidad, self.control_sensibilidad,
            self.etiqueta_nota, self.etiqueta_instruccion, self.etiqueta_nivel,
            self.boton_escucha, self.boton_referencia, self.casilla_bucle_referencia,
        ):
            distribucion.Add(widget, 0, wx.ALL | wx.EXPAND, 8)

        panel.SetSizer(distribucion)

    def _construir_atajos(self):
        """Ctrl+P reproduce el tono de referencia, Ctrl+E alterna la escucha, Ctrl+Mayús+Flecha
        arriba/abajo retoca la cuerda seleccionada en cuartos de tono, y Ctrl+Mayús+R restablece
        ese retoque. Nunca se usa la tecla Espacio."""
        self.Bind(wx.EVT_MENU, self._al_reproducir_referencia, id=ID_ATAJO_REPRODUCIR_REFERENCIA)
        self.Bind(wx.EVT_MENU, self._al_alternar_escucha, id=ID_ATAJO_ALTERNAR_ESCUCHA)
        self.Bind(wx.EVT_MENU, self._al_subir_cuarto_tono, id=ID_ATAJO_SUBIR_CUARTO_TONO)
        self.Bind(wx.EVT_MENU, self._al_bajar_cuarto_tono, id=ID_ATAJO_BAJAR_CUARTO_TONO)
        self.Bind(wx.EVT_MENU, self._al_restablecer_ajuste_fino, id=ID_ATAJO_RESTABLECER_AJUSTE_FINO)
        tabla = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord("P"), ID_ATAJO_REPRODUCIR_REFERENCIA),
            (wx.ACCEL_CTRL, ord("E"), ID_ATAJO_ALTERNAR_ESCUCHA),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, wx.WXK_UP, ID_ATAJO_SUBIR_CUARTO_TONO),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, wx.WXK_DOWN, ID_ATAJO_BAJAR_CUARTO_TONO),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord("R"), ID_ATAJO_RESTABLECER_AJUSTE_FINO),
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

        self.casilla_exclusivo_wasapi.SetValue(bool(self.ajustes.get("preferir_exclusivo_wasapi", False)))
        self.control_ganancia.SetValue(float(self.ajustes.get("ganancia", 1.0)))
        self.control_sensibilidad.SetValue(float(self.ajustes.get("umbral_yin", 0.15)))
        self.casilla_bucle_referencia.SetValue(bool(self.ajustes.get("bucle_referencia", False)))
        self.casilla_avance_automatico.SetValue(bool(self.ajustes.get("avance_automatico", True)))

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
            "preferir_exclusivo_wasapi": self.casilla_exclusivo_wasapi.GetValue(),
            "ganancia": self.control_ganancia.GetValue(),
            "umbral_yin": self.control_sensibilidad.GetValue(),
            "bucle_referencia": self.casilla_bucle_referencia.GetValue(),
            "avance_automatico": self.casilla_avance_automatico.GetValue(),
            "ajustes_finos_cuerdas": self.ajustes_finos_cuerdas,
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

        instrumento = self.selector_instrumento.GetStringSelection()
        escalas_disponibles = ESCALAS_POR_INSTRUMENTO.get(instrumento)
        self.selector_escala.Clear()
        if escalas_disponibles:
            for nombre_escala in escalas_disponibles:
                self.selector_escala.Append(nombre_escala)
            self.selector_escala.SetSelection(0)
            self.selector_escala.Enable()
        else:
            self.selector_escala.Disable()

        self.anunciador.reiniciar_estado()
        self._afinada_desde = None
        self._avance_ya_realizado = False
        if evento is not None:
            self._guardar_ajustes_actuales()
            evento.Skip()

    def _al_cambiar_escala(self, evento):
        instrumento = self.selector_instrumento.GetStringSelection()
        nombre_escala = self.selector_escala.GetStringSelection()
        desplazamientos = ESCALAS_POR_INSTRUMENTO.get(instrumento, {}).get(nombre_escala, {})
        for nombre_cuerda, _, _ in PRESETS_INSTRUMENTO.get(instrumento) or []:
            clave = "{}||{}".format(instrumento, nombre_cuerda)
            if nombre_cuerda in desplazamientos:
                self.ajustes_finos_cuerdas[clave] = desplazamientos[nombre_cuerda]
            else:
                self.ajustes_finos_cuerdas.pop(clave, None)
        self._guardar_ajustes_actuales()
        self.anunciador.reiniciar_estado()
        self._afinada_desde = None
        self._avance_ya_realizado = False
        self._historial_frecuencias.clear()
        self.anunciador.hablar("Escala aplicada: {}.".format(nombre_escala))
        evento.Skip()

    def _al_cambiar_cuerda(self, evento):
        self.anunciador.reiniciar_estado()
        self._afinada_desde = None
        self._avance_ya_realizado = False
        self._guardar_ajustes_actuales()
        cuartos_tono = self._cuartos_tono_actual()
        if cuartos_tono != 0:
            self.anunciador.hablar("Retocada: {:+d} cents.".format(cuartos_tono * CENTS_POR_CUARTO_TONO))
        evento.Skip()

    def _cuerda_objetivo(self):
        preset = self._preset_actual()
        if preset is None:
            return None
        indice = self.selector_cuerda.GetSelection()
        if indice == wx.NOT_FOUND:
            return None
        return preset[indice]

    def _clave_ajuste_fino(self):
        nombre_cuerda = self.selector_cuerda.GetStringSelection()
        if not nombre_cuerda:
            return None
        return "{}||{}".format(self.selector_instrumento.GetStringSelection(), nombre_cuerda)

    def _cuartos_tono_actual(self):
        clave = self._clave_ajuste_fino()
        if clave is None:
            return 0
        return self.ajustes_finos_cuerdas.get(clave, 0)

    def _frecuencia_objetivo_actual(self):
        """Frecuencia real de la cuerda seleccionada, incluyendo el retoque fino en cuartos
        de tono si lo hay. None en modo Cromático (sin cuerda objetivo)."""
        cuerda_objetivo = self._cuerda_objetivo()
        if cuerda_objetivo is None:
            return None
        _, indice_nota, octava = cuerda_objetivo
        return frecuencia_con_desplazamiento(indice_nota, octava, self._cuartos_tono_actual())

    def _desplazar_cuarto_tono(self, delta):
        clave = self._clave_ajuste_fino()
        if clave is None:
            self.anunciador.hablar("No hay ninguna cuerda seleccionada para retocar.")
            return
        cuerda_objetivo = self._cuerda_objetivo()
        cuartos_tono = self.ajustes_finos_cuerdas.get(clave, 0) + delta
        self.ajustes_finos_cuerdas[clave] = cuartos_tono
        self._guardar_ajustes_actuales()
        self.anunciador.reiniciar_estado()
        self._afinada_desde = None
        self._avance_ya_realizado = False
        self._historial_frecuencias.clear()

        _, indice_nota, octava = cuerda_objetivo
        nota_resultante = frecuencia_a_nota(frecuencia_con_desplazamiento(indice_nota, octava, cuartos_tono))
        cents_totales = cuartos_tono * CENTS_POR_CUARTO_TONO
        self.anunciador.hablar(
            "Retoque: {:+d} cents. Nota más cercana: {}{}.".format(
                cents_totales, nota_resultante["nombre"], nota_resultante["octava"]
            )
        )

    def _al_subir_cuarto_tono(self, evento):
        self._desplazar_cuarto_tono(1)

    def _al_bajar_cuarto_tono(self, evento):
        self._desplazar_cuarto_tono(-1)

    def _al_restablecer_ajuste_fino(self, evento):
        clave = self._clave_ajuste_fino()
        if clave is None or clave not in self.ajustes_finos_cuerdas:
            self.anunciador.hablar("Esta cuerda no tiene ningún retoque que restablecer.")
            return
        del self.ajustes_finos_cuerdas[clave]
        self._guardar_ajustes_actuales()
        self.anunciador.reiniciar_estado()
        self._afinada_desde = None
        self._avance_ya_realizado = False
        self._historial_frecuencias.clear()
        self.anunciador.hablar("Retoque restablecido.")

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

    def _al_enfocar_control_ganancia(self, evento):
        self.anunciador.hablar("Ganancia de entrada: {:.1f}".format(self.control_ganancia.GetValue()))
        evento.Skip()

    def _al_enfocar_control_sensibilidad(self, evento):
        self.anunciador.hablar("Sensibilidad de detección: {:.2f}".format(self.control_sensibilidad.GetValue()))
        evento.Skip()

    def _indice_dispositivo_seleccionado(self):
        posicion = self.selector_dispositivo.GetSelection()
        if posicion == wx.NOT_FOUND or not self.dispositivos:
            return None
        return self.dispositivos[posicion]["indice"]

    def _nombre_dispositivo_seleccionado(self):
        posicion = self.selector_dispositivo.GetSelection()
        if posicion == wx.NOT_FOUND or not self.dispositivos:
            return None
        return self.dispositivos[posicion]["nombre"]

    def _al_alternar_escucha(self, evento):
        if self.capturador is None:
            self._iniciar_escucha()
        else:
            self._detener_escucha()

    def _iniciar_escucha(self):
        asegurar_microfono_activo(self._nombre_dispositivo_seleccionado())
        indice_dispositivo = self._indice_dispositivo_seleccionado()
        tasa_muestreo = self._tasa_muestreo_seleccionada()
        duracion_ventana = self._duracion_ventana_seleccionada()
        self.capturador = CapturadorYIN(
            indice_dispositivo=indice_dispositivo,
            tasa_muestreo=tasa_muestreo,
            duracion_ventana=duracion_ventana,
            al_detectar=self._al_detectar_tono,
            preferir_exclusivo_wasapi=self.casilla_exclusivo_wasapi.GetValue(),
            ganancia=self.control_ganancia.GetValue(),
            umbral_yin=self.control_sensibilidad.GetValue(),
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
            "Escucha iniciada: dispositivo=%s (indice=%s) tasa_muestreo=%s duracion_ventana=%s backend=%s",
            self._nombre_dispositivo_seleccionado(), indice_dispositivo, tasa_muestreo, duracion_ventana,
            self.capturador.backend,
        )
        self.generador_tonos.capturador = self.capturador
        self.boton_escucha.SetLabel("Detener escucha (Ctrl+E)")
        # El botón cambia de etiqueta con SetLabel(), que no dispara ningún evento de
        # accesibilidad sin foco (el atajo Ctrl+E no se lo da) — hay que anunciarlo aparte.
        self.anunciador.hablar("Escucha iniciada.")
        self.anunciador.reiniciar_estado()
        self._nivel_maximo_observado = 0.0
        self._ultima_categoria_nivel = None
        self._senal_confirmada_una_vez = False
        self._marca_tiempo_ultima_nota = 0.0
        self._historial_frecuencias.clear()
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
            self.anunciador.hablar("Escucha detenida.")
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

    @staticmethod
    def _categoria_nivel(rms):
        if rms < NIVEL_MINIMO_SENAL_DIAGNOSTICO:
            return "sin_senal"
        if rms < NIVEL_SENAL_BUENA:
            return "senal_debil"
        return "senal_buena"

    def _actualizar_deteccion(self, resultado, rms):
        self._nivel_maximo_observado = max(getattr(self, "_nivel_maximo_observado", 0.0), rms)
        self.etiqueta_nivel.SetLabel("Nivel de entrada: {:.3f}".format(rms))

        ahora = time.monotonic()
        registrar_log = ahora - getattr(self, "_marca_tiempo_ultimo_log_nivel", 0.0) >= 1.0
        if registrar_log:
            self._marca_tiempo_ultimo_log_nivel = ahora

        # Los avisos de nivel comparten canal de voz con las instrucciones de afinación, y la
        # mayoría de lectores de pantalla cortan lo que se está diciendo en cuanto llega un
        # texto nuevo. Anunciar la categoría de nivel en cada fluctuación (algo constante en
        # una cuerda pulsada) cortaba las instrucciones de afinación a medias. Ahora solo se
        # confirma una vez, la primera vez que se detecta señal real tras el silencio inicial;
        # el resto del tiempo el canal de voz queda libre para "sube/baja/afinada".
        categoria_nivel = self._categoria_nivel(rms)
        if (self._ultima_categoria_nivel in (None, "sin_senal") and categoria_nivel != "sin_senal"
                and not self._senal_confirmada_una_vez):
            self._senal_confirmada_una_vez = True
            self.anunciador.hablar("Señal detectada.")
        self._ultima_categoria_nivel = categoria_nivel

        if resultado is None:
            self.etiqueta_nota.SetLabel("Nota detectada: —")
            self.etiqueta_instruccion.SetLabel("Instrucción: —")
            # Una cuerda pulsada decae: el nivel sube y baja constantemente entre "hay nota"
            # y "no hay nada" en fracciones de segundo, aunque la nota siga sonando. Reiniciar
            # el estado del anunciador en cada hueco así de breve nunca deja acumular los 350 ms
            # de estabilidad que exige el throttling, y la instrucción no llega a decirse nunca.
            # Solo se reinicia si el silencio real se sostiene más de ese margen.
            if ahora - getattr(self, "_marca_tiempo_ultima_nota", 0.0) > SEGUNDOS_MARGEN_SILENCIO_ENTRE_NOTAS:
                self.anunciador.reiniciar_estado()
                self._historial_frecuencias.clear()
            if registrar_log:
                logger.info(
                    "Nivel actual: rms=%.4f nota=ninguna instrumento=%s cuerda=%s",
                    rms, self.selector_instrumento.GetStringSelection(), self.selector_cuerda.GetStringSelection(),
                )
            return

        self._marca_tiempo_ultima_nota = ahora

        # Filtro de mediana: en el instante del ataque de una cuerda pulsada, antes de que
        # el sonido se asiente en su frecuencia real, YIN puede devolver lecturas puntuales
        # erráticas (saltos de octava o notas vecinas). Quedarse con la mediana de las
        # últimas lecturas descarta esos valores sueltos sin perder capacidad de respuesta.
        self._historial_frecuencias.append(resultado["frecuencia"])
        frecuencia_filtrada = statistics.median(self._historial_frecuencias)
        resultado = frecuencia_a_nota(frecuencia_filtrada)

        cuerda_objetivo = self._cuerda_objetivo()
        frecuencia_objetivo = self._frecuencia_objetivo_actual()
        if frecuencia_objetivo is not None:
            cents = 1200 * np.log2(frecuencia_filtrada / frecuencia_objetivo)
        else:
            cents = resultado["cents"]

        instruccion = calcular_instruccion(cents)
        texto_instruccion = TEXTOS_INSTRUCCION.get(instruccion, "—")

        self.etiqueta_nota.SetLabel(
            "Nota detectada: {}{} ({:+.0f} cents)".format(resultado["nombre"], resultado["octava"], cents)
        )
        self.etiqueta_instruccion.SetLabel("Instrucción: {}".format(texto_instruccion))

        if registrar_log:
            logger.info(
                "Nivel actual: rms=%.4f nota=%s%s cents=%+.1f instruccion=%s instrumento=%s cuerda=%s",
                rms, resultado["nombre"], resultado["octava"], cents, instruccion,
                self.selector_instrumento.GetStringSelection(), self.selector_cuerda.GetStringSelection(),
            )

        if instruccion != "AFINADA":
            self._confirmacion_pendiente = True
            self._afinada_desde = None
            self._avance_ya_realizado = False
        self.anunciador.procesar_instruccion(texto_instruccion)
        if instruccion == "AFINADA" and self._confirmacion_pendiente:
            self._confirmacion_pendiente = False
            self.generador_tonos.reproducir_confirmacion()

        if (instruccion == "AFINADA" and cuerda_objetivo is not None and not self._avance_ya_realizado
                and self.casilla_avance_automatico.GetValue()):
            if self._afinada_desde is None:
                self._afinada_desde = time.monotonic()
            elif time.monotonic() - self._afinada_desde >= SEGUNDOS_ESTABLE_PARA_AVANZAR:
                self._avance_ya_realizado = True
                self._avanzar_a_siguiente_cuerda()

    def _avanzar_a_siguiente_cuerda(self):
        total_cuerdas = self.selector_cuerda.GetCount()
        posicion_actual = self.selector_cuerda.GetSelection()
        if posicion_actual == wx.NOT_FOUND or total_cuerdas == 0:
            return
        siguiente_posicion = posicion_actual + 1
        if siguiente_posicion >= total_cuerdas:
            self.anunciador.hablar("Última cuerda afinada.")
            return
        self.selector_cuerda.SetSelection(siguiente_posicion)
        self.anunciador.reiniciar_estado()
        self._afinada_desde = None
        self._confirmacion_pendiente = True
        self._guardar_ajustes_actuales()
        self.anunciador.hablar("Siguiente: {}".format(self.selector_cuerda.GetStringSelection()))

    def _al_reproducir_referencia(self, evento):
        if self._reproduciendo_en_bucle:
            self.generador_tonos.detener_bucle()
            self._reproduciendo_en_bucle = False
            self.boton_referencia.SetLabel("Reproducir tono de referencia (Ctrl+P)")
            return

        frecuencia = self._frecuencia_objetivo_actual()
        if frecuencia is None:
            frecuencia = nota_a_frecuencia(9, 4)  # La4, referencia estándar en modo cromático

        if self.casilla_bucle_referencia.GetValue():
            self._reproduciendo_en_bucle = True
            self.boton_referencia.SetLabel("Detener tono de referencia (Ctrl+P)")
            self.generador_tonos.reproducir_en_bucle(frecuencia)
        else:
            self.generador_tonos.reproducir(frecuencia, duracion=2.0)

    def _al_cambiar_ajuste_bucle(self, evento):
        if not self.casilla_bucle_referencia.GetValue() and self._reproduciendo_en_bucle:
            self.generador_tonos.detener_bucle()
            self._reproduciendo_en_bucle = False
            self.boton_referencia.SetLabel("Reproducir tono de referencia (Ctrl+P)")
        self._guardar_ajustes_actuales()
        evento.Skip()

    def _al_cambiar_ajuste_simple(self, evento):
        self._guardar_ajustes_actuales()
        evento.Skip()

    def _al_cerrar(self, evento):
        self.generador_tonos.detener_bucle()
        self._guardar_ajustes_actuales()
        self._detener_escucha()
        evento.Skip()
# ANCLAJE_FIN: ventana_principal
