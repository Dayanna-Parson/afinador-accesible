"""Ventana principal accesible del afinador cromático."""

import json
import logging
import statistics
import time
import webbrowser
from collections import deque
from pathlib import Path

import numpy as np
import wx

from app.motor_audio import (
    CapturadorYIN,
    CENTS_POR_CUARTO_TONO,
    establecer_frecuencia_la4,
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
from app.perfiles_afinacion import guardar_perfil, migrar_perfiles, nombres_perfiles
from app.config_rutas import RUTA_AYUDA
from app.afinaciones_maqam_lira import (
    AFINACIONES_LIRA_MAQAM_24EDO,
    FAMILIAS_MAQAM_LIRA,
    NOMBRE_AFINACION_FABRICA_LIRA,
    NOMBRE_AFINACION_PERSONALIZADA_LIRA,
    REFERENCIAS_GRADOS_MAQAM_24EDO,
)
from app.interfaz.ui_recursos import aplicar_icono_boton

logger = logging.getLogger(__name__)

TEXTOS_INSTRUCCION = {
    "AFINADA": "Afinada",
    "SUBE_POCO": "Sube un poco. Ya te estás acercando",
    "SUBE_BASTANTE": "Sube bastante",
    "BAJA_POCO": "Baja un poco. Ya te estás acercando",
    "BAJA_BASTANTE": "Baja bastante",
}

NOMBRES_NOTAS_BEMOLES = ["Do", "Re bemol", "Re", "Mi bemol", "Mi", "Fa", "Sol bemol", "Sol", "La bemol", "La", "Si bemol", "Si"]
NOMBRES_NOTAS_SOSTENIDOS = ["Do", "Do sostenido", "Re", "Re sostenido", "Mi", "Fa", "Fa sostenido", "Sol", "Sol sostenido", "La", "La sostenido", "Si"]
NOMBRES_NOTAS_AMERICANOS = ["C", "C sostenido", "D", "D sostenido", "E", "F", "F sostenido", "G", "G sostenido", "A", "A sostenido", "B"]

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
NOMBRE_AFINACION_PERSONALIZADA = "Personalizada (retoques manuales)"

# Guitarra y ukelele: afinaciones alternativas estándar, ampliamente documentadas. En un
# instrumento con trastes el retoque solo desplaza la cuerda al aire entera — los trastes
# siguen fijos en semitonos occidentales, así que estas afinaciones no dan acceso a cuartos
# de tono nuevos en el mástil, solo a otras disposiciones de acordes/resonancias.
ESCALAS_POR_INSTRUMENTO = {
    NOMBRE_LIRA: dict(AFINACIONES_LIRA_MAQAM_24EDO),
    NOMBRE_GUITARRA: {
        "Estándar (Mi La Re Sol Si Mi)": {},
        "Drop D (Re La Re Sol Si Mi)": {"Cuerda 6 (Mi)": -4},
        "Open G (Re Sol Re Sol Si Re)": {"Cuerda 6 (Mi)": -4, "Cuerda 5 (La)": -4, "Cuerda 1 (Mi)": -4},
        "Open D (Re La Re Fa# La Re)": {
            "Cuerda 6 (Mi)": -4, "Cuerda 3 (Sol)": -2, "Cuerda 2 (Si)": -4, "Cuerda 1 (Mi)": -4,
        },
        "DADGAD (Re La Re Sol La Re)": {"Cuerda 6 (Mi)": -4, "Cuerda 2 (Si)": -4, "Cuerda 1 (Mi)": -4},
    },
    NOMBRE_UKELELE: {
        "Estándar (Sol Do Mi La, reentrante)": {},
    },
}

OPCIONES_TASA_MUESTREO = [
    ("Automática (recomendada)", None),
    ("44100 Hz", 44100),
    ("48000 Hz", 48000),
]

OPCIONES_DURACION_VENTANA = [
    ("Baja latencia (50 ms)", 0.05),
    ("Equilibrada (100 ms)", 0.1),
    ("Alta precisión, notas graves (200 ms)", 0.2),
]
OPCIONES_CANAL_ENTRADA = [("Automático (todos los canales)", None), ("Entrada 1", 0), ("Entrada 2", 1)]
OPCIONES_PASO_RETOQUE = [
    ("Cuarto de tono", 1),
    ("Semitono", 2),
    ("Tono", 4),
]

ID_ATAJO_REPRODUCIR_REFERENCIA = wx.NewIdRef()
ID_ATAJO_ALTERNAR_ESCUCHA = wx.NewIdRef()
ID_ATAJO_SUBIR_CUARTO_TONO = wx.NewIdRef()
ID_ATAJO_BAJAR_CUARTO_TONO = wx.NewIdRef()
ID_ATAJO_RESTABLECER_AJUSTE_FINO = wx.NewIdRef()
ID_ATAJO_ESCUCHA_PREVIA_ESCALA = wx.NewIdRef()
ID_ATAJO_DESHACER_RETOQUE = wx.NewIdRef()
ID_ATAJO_REPETIR_INSTRUCCION = wx.NewIdRef()

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
        super().__init__(None, title="Afinador Accesible", size=(760, 780))
        self.SetMinSize((520, 520))

        self.ajustes = cargar_ajustes()
        establecer_frecuencia_la4(float(self.ajustes.get("frecuencia_la4", 440.0)))
        self.ajustes_finos_cuerdas = dict(self.ajustes.get("ajustes_finos_cuerdas", {}))
        self.perfiles_afinacion = migrar_perfiles(self.ajustes, NOMBRE_LIRA)
        self.escala_base_personalizada = dict(self.ajustes.get("escala_base_personalizada", {}))
        self._perfil_cargado = None
        self._retoques_sin_guardar = False
        self._retoques_antes_de_editar = None
        self.retoques_escala_activa = {}
        self._historial_retoques = []
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
        self._ultima_instruccion_afinacion = None
        self._marca_tiempo_ultima_actualizacion = time.monotonic()
        self._aviso_captura_interrumpida = False

        self._construir_controles()
        self._construir_atajos()
        self._cargar_dispositivos()
        self._aplicar_ajustes_guardados()

        self.Bind(wx.EVT_CLOSE, self._al_cerrar)
        self.Centre()
        self.Show()

    def _construir_controles(self):
        self._construir_controles_con_pestanas()

    def _construir_controles_con_pestanas(self):
        """Crea cada control dentro de su página; wx no permite reparentar con fiabilidad."""
        principal = wx.BoxSizer(wx.VERTICAL)
        self.cuaderno = wx.Notebook(self)
        self.pagina_afinar = self._crear_pagina_desplazable()
        self.pagina_afinaciones = self._crear_pagina_desplazable()
        self.pagina_audio = self._crear_pagina_desplazable()
        self.cuaderno.AddPage(self.pagina_afinar, "Afinar", select=True)
        self.cuaderno.AddPage(self.pagina_afinaciones, "Afinaciones especiales")
        self.cuaderno.AddPage(self.pagina_audio, "Audio y ajustes")

        # Afinar: lo necesario para una sesión corriente.
        self.selector_instrumento = wx.RadioBox(
            self.pagina_afinar, label="Instrumento que quieres afinar", choices=[NOMBRE_LIRA, NOMBRE_GUITARRA, NOMBRE_UKELELE],
            majorDimension=1, style=wx.RA_SPECIFY_ROWS,
        )
        self.selector_instrumento.SetSelection(0)
        self.selector_instrumento.SetHelpText("Tus tres instrumentos. Al abrir cada uno parte de su afinación estándar.")
        # RadioBox emite EVT_RADIOBOX, no EVT_CHOICE. Usar el evento correcto es
        # esencial: de lo contrario puede quedarse visible la lista de cuerdas
        # del instrumento anterior.
        self.selector_instrumento.Bind(wx.EVT_RADIOBOX, self._al_cambiar_instrumento)
        etiqueta_cuerda = wx.StaticText(self.pagina_afinar, label="Cuerda objetivo:")
        self.selector_cuerda = wx.Choice(self.pagina_afinar)
        self.selector_cuerda.SetHelpText("Elige la cuerda que vas a afinar.")
        self.selector_cuerda.Bind(wx.EVT_CHOICE, self._al_cambiar_cuerda)
        etiqueta_escala_rapida = wx.StaticText(self.pagina_afinar, label="Afinación de este instrumento:")
        self.selector_escala_rapida = wx.Choice(self.pagina_afinar)
        self.selector_escala_rapida.SetHelpText(
            "Muestra solamente las afinaciones compatibles con el instrumento elegido. "
            "Para la lira incluye la afinación de fábrica y los maqamat."
        )
        self.selector_escala_rapida.Bind(wx.EVT_CHOICE, self._al_cambiar_escala_rapida)
        self.boton_abrir_perfiles = wx.Button(self.pagina_afinar, label="Perfiles personales...")
        aplicar_icono_boton(self.boton_abrir_perfiles, "guardar")
        self.boton_abrir_perfiles.SetHelpText(
            "Abre una ventana para cargar o guardar las afinaciones personales del instrumento elegido."
        )
        self.boton_abrir_perfiles.Bind(wx.EVT_BUTTON, self._al_abrir_perfiles)
        self.casilla_deteccion_automatica_cuerda = wx.CheckBox(
            self.pagina_afinar, label="Detectar automáticamente qué cuerda suena"
        )
        self.casilla_deteccion_automatica_cuerda.SetHelpText(
            "Evita elegir una cuerda, pero es menos fiable si hay ruido o varias cuerdas vibrando."
        )
        self.casilla_deteccion_automatica_cuerda.SetValue(False)
        self.casilla_deteccion_automatica_cuerda.Bind(wx.EVT_CHECKBOX, self._al_cambiar_ajuste_simple)
        self.etiqueta_nota = wx.StaticText(self.pagina_afinar, label="Nota detectada: —")
        self.etiqueta_instruccion = wx.StaticText(self.pagina_afinar, label="Instrucción: —")
        self.etiqueta_nivel = wx.StaticText(self.pagina_afinar, label="Nivel de entrada: —")
        self.indicador_desviacion = wx.Gauge(self.pagina_afinar, range=100, style=wx.GA_HORIZONTAL)
        self.indicador_desviacion.SetValue(50)
        self.indicador_desviacion.SetHelpText("Indicador visual de desviación: izquierda baja, centro afinada, derecha sube.")
        self.etiqueta_visual_afinacion = wx.StaticText(
            self.pagina_afinar, label="Indicador visual: esperando una nota"
        )
        fuente_indicador = self.etiqueta_visual_afinacion.GetFont()
        fuente_indicador.SetPointSize(fuente_indicador.GetPointSize() + 2)
        fuente_indicador.SetWeight(wx.FONTWEIGHT_BOLD)
        self.etiqueta_visual_afinacion.SetFont(fuente_indicador)
        etiqueta_escala_visual = wx.StaticText(
            self.pagina_afinar, label="Baja la tensión   ←   AFINADA   →   Sube la tensión"
        )
        self.boton_escucha = wx.Button(self.pagina_afinar, label="Iniciar escucha (Ctrl+E)")
        aplicar_icono_boton(self.boton_escucha, "afinar", fijar_nombre=False)
        self.boton_escucha.SetHelpText("Inicia o detiene la escucha del micrófono.")
        self.boton_escucha.Bind(wx.EVT_BUTTON, self._al_alternar_escucha)
        self.boton_referencia = wx.Button(self.pagina_afinar, label="Reproducir tono de referencia (Ctrl+P)")
        aplicar_icono_boton(self.boton_referencia, "reproducir")
        self.boton_referencia.SetHelpText("Reproduce el tono de la cuerda objetivo.")
        self.boton_referencia.Bind(wx.EVT_BUTTON, self._al_reproducir_referencia)
        self.casilla_bucle_referencia = wx.CheckBox(self.pagina_afinar, label="Repetir el tono de referencia en bucle")
        self.casilla_bucle_referencia.SetValue(False)
        self.casilla_bucle_referencia.Bind(wx.EVT_CHECKBOX, self._al_cambiar_ajuste_bucle)
        self.casilla_avance_automatico = wx.CheckBox(
            self.pagina_afinar, label="Avanzar automáticamente a la siguiente cuerda al afinar"
        )
        self.casilla_avance_automatico.SetValue(True)
        self.casilla_avance_automatico.Bind(wx.EVT_CHECKBOX, self._al_cambiar_ajuste_simple)
        self.casilla_pitido_confirmacion = wx.CheckBox(
            self.pagina_afinar, label="Reproducir pitido al afinar correctamente"
        )
        self.casilla_pitido_confirmacion.SetValue(True)
        self.casilla_pitido_confirmacion.Bind(wx.EVT_CHECKBOX, self._al_cambiar_ajuste_simple)
        self.casilla_modo_solo_escucha = wx.CheckBox(
            self.pagina_afinar, label="Modo solo escucha (dice la nota detectada, sin instrucciones de sube/baja)"
        )
        self.casilla_modo_solo_escucha.SetValue(False)
        self.casilla_modo_solo_escucha.Bind(wx.EVT_CHECKBOX, self._al_cambiar_ajuste_simple)
        self._organizar_pagina(
            self.pagina_afinar,
            ("Instrumento, afinación y cuerda", (self.selector_instrumento, etiqueta_escala_rapida,
                                                    self.selector_escala_rapida, etiqueta_cuerda,
                                                    self.selector_cuerda, self.casilla_deteccion_automatica_cuerda)),
            ("Afinaciones personales", (self.boton_abrir_perfiles,)),
            ("Durante la afinación", (self.etiqueta_nota, self.etiqueta_instruccion, self.etiqueta_nivel,
                                         self.etiqueta_visual_afinacion, self.indicador_desviacion, etiqueta_escala_visual,
                                         self.boton_escucha, self.boton_referencia, self.casilla_bucle_referencia)),
            ("Comportamiento", (self.casilla_avance_automatico, self.casilla_pitido_confirmacion,
                                 self.casilla_modo_solo_escucha)),
        )

        # Afinaciones especiales: no distrae de la afinación estándar.
        etiqueta_familia_maqam = wx.StaticText(self.pagina_afinaciones, label="Familia de maqam:")
        self.selector_familia_maqam = wx.Choice(
            self.pagina_afinaciones, choices=["Todas las familias"] + list(FAMILIAS_MAQAM_LIRA)
        )
        self.selector_familia_maqam.SetSelection(0)
        self.selector_familia_maqam.SetHelpText(
            "Filtra los maqamat de la lira por familia. La afinación de fábrica siempre permanece disponible."
        )
        self.selector_familia_maqam.Bind(wx.EVT_CHOICE, self._al_cambiar_familia_maqam)
        etiqueta_escala = wx.StaticText(self.pagina_afinaciones, label="Escala o afinación:")
        self.selector_escala = wx.Choice(self.pagina_afinaciones)
        self.selector_escala.SetHelpText("Las opciones dependen del instrumento elegido en la pestaña Afinar.")
        self.selector_escala.Bind(wx.EVT_CHOICE, self._al_cambiar_escala)
        self.boton_escucha_previa = wx.Button(
            self.pagina_afinaciones, label="Escuchar la afinación completa actual (Ctrl+Mayús+P)"
        )
        aplicar_icono_boton(self.boton_escucha_previa, "reproducir")
        self.boton_escucha_previa.SetHelpText(
            "Reproduce todas las notas objetivo, incluidos el maqam y los retoques manuales que hayas hecho."
        )
        self.boton_escucha_previa.Bind(wx.EVT_BUTTON, self._al_escucha_previa_escala)
        aviso_escala = wx.StaticText(
            self.pagina_afinaciones,
            label="Para afinar normalmente, elige la primera opción de la lista."
        )
        self.etiqueta_contexto_afinacion = wx.StaticText(self.pagina_afinaciones, label="")
        self.etiqueta_contexto_afinacion.Wrap(560)
        etiqueta_paso_retoque = wx.StaticText(self.pagina_afinaciones, label="Tamaño del ajuste manual:")
        self.selector_paso_retoque = wx.Choice(
            self.pagina_afinaciones, choices=[nombre for nombre, _ in OPCIONES_PASO_RETOQUE]
        )
        self.selector_paso_retoque.SetSelection(0)
        self.selector_paso_retoque.SetHelpText(
            "Elige si las flechas y botones ajustan un cuarto de tono, un semitono o un tono."
        )
        self.boton_subir_retoque = wx.Button(self.pagina_afinaciones, label="Subir la cuerda seleccionada (Ctrl+Mayús+Flecha arriba)")
        aplicar_icono_boton(self.boton_subir_retoque, "subir")
        self.boton_subir_retoque.Bind(wx.EVT_BUTTON, self._al_subir_cuarto_tono)
        self.boton_bajar_retoque = wx.Button(self.pagina_afinaciones, label="Bajar la cuerda seleccionada (Ctrl+Mayús+Flecha abajo)")
        aplicar_icono_boton(self.boton_bajar_retoque, "bajar")
        self.boton_bajar_retoque.Bind(wx.EVT_BUTTON, self._al_bajar_cuarto_tono)
        self.boton_restablecer_retoque = wx.Button(self.pagina_afinaciones, label="Restablecer ajuste manual de esta cuerda (Ctrl+Mayús+R)")
        aplicar_icono_boton(self.boton_restablecer_retoque, "restablecer")
        self.boton_restablecer_retoque.Bind(wx.EVT_BUTTON, self._al_restablecer_ajuste_fino)
        etiqueta_guardadas = wx.StaticText(self.pagina_afinaciones, label="Perfiles personales de este instrumento:")
        self.selector_afinacion_guardada = wx.Choice(self.pagina_afinaciones)
        self.boton_guardar_afinacion = wx.Button(self.pagina_afinaciones, label="Guardar perfil de afinación actual como...")
        aplicar_icono_boton(self.boton_guardar_afinacion, "guardar")
        self.boton_guardar_afinacion.SetHelpText(
            "Guarda una copia con nombre de la afinación actual, incluida cada cuerda retocada."
        )
        self.boton_guardar_afinacion.Bind(wx.EVT_BUTTON, self._al_guardar_afinacion_personal)
        self.boton_cargar_afinacion = wx.Button(self.pagina_afinaciones, label="Cargar perfil seleccionado")
        aplicar_icono_boton(self.boton_cargar_afinacion, "cargar")
        self.boton_cargar_afinacion.SetHelpText(
            "Recupera el perfil seleccionado para el instrumento actual."
        )
        self.boton_cargar_afinacion.Bind(wx.EVT_BUTTON, self._al_cargar_afinacion_personal)
        self.boton_renombrar_afinacion = wx.Button(self.pagina_afinaciones, label="Renombrar perfil seleccionado")
        aplicar_icono_boton(self.boton_renombrar_afinacion, "editar")
        self.boton_renombrar_afinacion.SetHelpText("Cambia solamente el nombre del perfil seleccionado.")
        self.boton_renombrar_afinacion.Bind(wx.EVT_BUTTON, self._al_renombrar_afinacion_personal)
        self.boton_eliminar_afinacion = wx.Button(self.pagina_afinaciones, label="Eliminar perfil seleccionado")
        aplicar_icono_boton(self.boton_eliminar_afinacion, "eliminar")
        self.boton_eliminar_afinacion.SetHelpText("Elimina el perfil seleccionado después de pedir confirmación.")
        self.boton_eliminar_afinacion.Bind(wx.EVT_BUTTON, self._al_eliminar_afinacion_personal)
        self.boton_exportar_perfiles = wx.Button(self.pagina_afinaciones, label="Exportar todos los perfiles...")
        aplicar_icono_boton(self.boton_exportar_perfiles, "guardar")
        self.boton_exportar_perfiles.SetHelpText("Guarda una copia de seguridad de todos los perfiles en un archivo JSON.")
        self.boton_exportar_perfiles.Bind(wx.EVT_BUTTON, self._al_exportar_perfiles)
        self.boton_importar_perfiles = wx.Button(self.pagina_afinaciones, label="Importar perfiles desde copia...")
        aplicar_icono_boton(self.boton_importar_perfiles, "cargar")
        self.boton_importar_perfiles.SetHelpText("Añade perfiles de una copia sin reemplazar perfiles con el mismo nombre.")
        self.boton_importar_perfiles.Bind(wx.EVT_BUTTON, self._al_importar_perfiles)
        self._organizar_pagina(
            self.pagina_afinaciones,
            ("Afinación seleccionada", (etiqueta_familia_maqam, self.selector_familia_maqam,
                                          etiqueta_escala, self.selector_escala,
                                          self.boton_escucha_previa, aviso_escala,
                                          self.etiqueta_contexto_afinacion)),
            ("Ajuste manual de una cuerda", (etiqueta_paso_retoque, self.selector_paso_retoque,
                                              self.boton_subir_retoque, self.boton_bajar_retoque,
                                              self.boton_restablecer_retoque)),
            ("Perfiles personales", (etiqueta_guardadas, self.selector_afinacion_guardada,
                                         self.boton_guardar_afinacion, self.boton_cargar_afinacion,
                                         self.boton_renombrar_afinacion, self.boton_eliminar_afinacion,
                                         self.boton_exportar_perfiles, self.boton_importar_perfiles)),
        )

        # Audio y ajustes: opciones que rara vez hay que tocar durante una sesión.
        etiqueta_dispositivo = wx.StaticText(self.pagina_audio, label="Dispositivo de entrada de audio:")
        self.selector_dispositivo = wx.Choice(self.pagina_audio)
        self.selector_dispositivo.Bind(wx.EVT_CHOICE, self._al_cambiar_dispositivo)
        etiqueta_canal = wx.StaticText(self.pagina_audio, label="Canal de entrada:")
        self.selector_canal = wx.Choice(self.pagina_audio, choices=[texto for texto, _ in OPCIONES_CANAL_ENTRADA])
        self.selector_canal.SetSelection(0)
        self.selector_canal.Bind(wx.EVT_CHOICE, self._al_cambiar_calidad_captura)
        self.casilla_exclusivo_wasapi = wx.CheckBox(
            self.pagina_audio, label="Modo exclusivo WASAPI (puede fallar con dispositivos compuestos)"
        )
        self.casilla_exclusivo_wasapi.SetHelpText("Útil si la entrada normal no detecta bien el instrumento.")
        self.casilla_exclusivo_wasapi.SetValue(False)
        self.casilla_exclusivo_wasapi.Bind(wx.EVT_CHECKBOX, self._al_cambiar_calidad_captura)
        self.casilla_desmutear_microfono = wx.CheckBox(
            self.pagina_audio, label="Desmutear el micrófono si Windows lo tiene silenciado"
        )
        self.casilla_desmutear_microfono.SetValue(False)
        self.casilla_desmutear_microfono.Bind(wx.EVT_CHECKBOX, self._al_cambiar_ajuste_simple)
        etiqueta_tasa = wx.StaticText(self.pagina_audio, label="Tasa de muestreo:")
        self.selector_tasa = wx.Choice(self.pagina_audio, choices=[texto for texto, _ in OPCIONES_TASA_MUESTREO])
        self.selector_tasa.SetSelection(0)
        self.selector_tasa.Bind(wx.EVT_CHOICE, self._al_cambiar_calidad_captura)
        etiqueta_buffer = wx.StaticText(self.pagina_audio, label="Tamaño de búfer:")
        self.selector_buffer = wx.Choice(self.pagina_audio, choices=[texto for texto, _ in OPCIONES_DURACION_VENTANA])
        self.selector_buffer.SetSelection(1)
        self.selector_buffer.Bind(wx.EVT_CHOICE, self._al_cambiar_calidad_captura)
        etiqueta_ganancia = wx.StaticText(self.pagina_audio, label="Ganancia de entrada:")
        self.control_ganancia = wx.SpinCtrlDouble(self.pagina_audio, min=1.0, max=5.0, initial=1.0, inc=0.5)
        self.control_ganancia.SetDigits(1)
        self.control_ganancia.SetLabel("Ganancia de entrada")
        self.control_ganancia.Bind(wx.EVT_SPINCTRLDOUBLE, self._al_cambiar_calidad_captura)
        self.control_ganancia.Bind(wx.EVT_SET_FOCUS, self._al_enfocar_control_ganancia)
        etiqueta_sensibilidad = wx.StaticText(self.pagina_audio, label="Sensibilidad de detección (más alto = más permisivo):")
        self.control_sensibilidad = wx.SpinCtrlDouble(self.pagina_audio, min=0.05, max=0.40, initial=0.15, inc=0.05)
        self.control_sensibilidad.SetDigits(2)
        self.control_sensibilidad.SetLabel("Sensibilidad de detección")
        self.control_sensibilidad.Bind(wx.EVT_SPINCTRLDOUBLE, self._al_cambiar_calidad_captura)
        self.control_sensibilidad.Bind(wx.EVT_SET_FOCUS, self._al_enfocar_control_sensibilidad)
        etiqueta_la4 = wx.StaticText(self.pagina_audio, label="Referencia La4 (Hz):")
        self.control_la4 = wx.SpinCtrlDouble(self.pagina_audio, min=400.0, max=480.0, initial=440.0, inc=1.0)
        self.control_la4.SetDigits(1)
        self.control_la4.SetLabel("Referencia La4 en hercios")
        self.control_la4.Bind(wx.EVT_SPINCTRLDOUBLE, self._al_cambiar_la4)
        etiqueta_verbosidad = wx.StaticText(self.pagina_audio, label="Nivel de detalle de las instrucciones:")
        self.selector_verbosidad = wx.Choice(self.pagina_audio, choices=["Conciso", "Detallado (con cents exactos)"])
        self.selector_verbosidad.SetSelection(0)
        self.selector_verbosidad.Bind(wx.EVT_CHOICE, self._al_cambiar_ajuste_simple)
        self.selector_nomenclatura = wx.RadioBox(
            self.pagina_audio, label="Nombres de las notas", choices=["Do, Re, Mi", "C, D, E (cifrado americano)"],
            majorDimension=1, style=wx.RA_SPECIFY_ROWS,
        )
        self.selector_nomenclatura.SetHelpText(
            "Cambia cómo se muestran y se verbalizan las notas detectadas y objetivo. No altera frecuencias ni afinaciones."
        )
        self.selector_nomenclatura.Bind(wx.EVT_RADIOBOX, self._al_cambiar_nomenclatura)
        self._organizar_pagina(
            self.pagina_audio,
            ("Entrada de audio", (etiqueta_dispositivo, self.selector_dispositivo, etiqueta_canal,
                                   self.selector_canal, self.casilla_exclusivo_wasapi,
                                   self.casilla_desmutear_microfono)),
            ("Calidad de detección", (etiqueta_tasa, self.selector_tasa, etiqueta_buffer,
                                      self.selector_buffer, etiqueta_ganancia, self.control_ganancia,
                                      etiqueta_sensibilidad, self.control_sensibilidad)),
            ("Referencia e indicaciones", (etiqueta_la4, self.control_la4, etiqueta_verbosidad,
                                            self.selector_verbosidad, self.selector_nomenclatura)),
        )
        principal.Add(self.cuaderno, 1, wx.EXPAND | wx.ALL, 8)
        self.SetSizer(principal)
        self._controles_pestana = {
            self.pagina_afinar: (
                self.selector_instrumento, self.selector_escala_rapida, self.selector_cuerda,
                self.casilla_deteccion_automatica_cuerda, self.boton_abrir_perfiles,
                self.boton_escucha, self.boton_referencia, self.casilla_bucle_referencia,
                self.casilla_avance_automatico, self.casilla_pitido_confirmacion, self.casilla_modo_solo_escucha,
            ),
            self.pagina_afinaciones: (self.selector_familia_maqam, self.selector_escala,
                                       self.boton_escucha_previa, self.selector_paso_retoque,
                                       self.boton_subir_retoque, self.boton_bajar_retoque,
                                       self.boton_restablecer_retoque, self.selector_afinacion_guardada,
                                       self.boton_guardar_afinacion, self.boton_cargar_afinacion,
                                       self.boton_renombrar_afinacion, self.boton_eliminar_afinacion,
                                       self.boton_exportar_perfiles, self.boton_importar_perfiles),
            self.pagina_audio: (
                self.selector_dispositivo, self.selector_canal, self.casilla_exclusivo_wasapi,
                self.casilla_desmutear_microfono, self.selector_tasa, self.selector_buffer,
                self.control_ganancia, self.control_sensibilidad, self.control_la4, self.selector_verbosidad,
                self.selector_nomenclatura,
            ),
        }
        self.Bind(wx.EVT_CHAR_HOOK, self._al_navegacion_con_tab)

    def _crear_pagina_desplazable(self):
        pagina = wx.ScrolledWindow(self.cuaderno, style=wx.VSCROLL)
        pagina.SetScrollRate(0, 20)
        return pagina

    @staticmethod
    def _titulo_seccion(pagina, texto):
        titulo = wx.StaticText(pagina, label=texto)
        fuente = titulo.GetFont()
        fuente.SetWeight(wx.FONTWEIGHT_BOLD)
        titulo.SetFont(fuente)
        return titulo

    def _organizar_pagina(self, pagina, *secciones):
        distribucion = wx.BoxSizer(wx.VERTICAL)
        for titulo, controles in secciones:
            distribucion.Add(self._titulo_seccion(pagina, titulo), 0, wx.LEFT | wx.RIGHT | wx.TOP, 12)
            for control in controles:
                distribucion.Add(control, 0, wx.ALL | wx.EXPAND, 8)
        pagina.SetSizer(distribucion)
        distribucion.Fit(pagina)

    def _al_navegacion_con_tab(self, evento):
        """Atajos globales y recorrido circular entre pestañas y controles."""
        tecla = evento.GetKeyCode()
        if tecla == wx.WXK_F1:
            self._abrir_ayuda()
            return
        if (
            evento.ControlDown() and not evento.ShiftDown() and not evento.AltDown()
            and tecla in (ord("1"), ord("2"), ord("3"))
        ):
            self.cuaderno.SetSelection(tecla - ord("1"))
            wx.CallAfter(self.cuaderno.SetFocus)
            return
        foco = wx.Window.FindFocus()
        # wx.Notebook no cierra siempre el recorrido con las flechas: al llegar
        # a un extremo puede mandar el foco al primer control de la página. Lo
        # interceptamos para conservar el foco en las pestañas y volver de la
        # última a la primera (y al revés).
        if foco == self.cuaderno and tecla in (wx.WXK_LEFT, wx.WXK_RIGHT):
            total_pestanas = self.cuaderno.GetPageCount()
            if total_pestanas:
                delta = -1 if tecla == wx.WXK_LEFT else 1
                self.cuaderno.SetSelection((self.cuaderno.GetSelection() + delta) % total_pestanas)
                wx.CallAfter(self.cuaderno.SetFocus)
            return
        if tecla != wx.WXK_TAB or evento.ControlDown() or evento.AltDown():
            evento.Skip()
            return
        controles = tuple(
            control for control in self._controles_pestana.get(self.cuaderno.GetCurrentPage(), ())
            if control.IsShown() and control.IsEnabled()
        )
        # El cuaderno forma parte del recorrido. Antes se cerraba el círculo solo
        # entre controles de la página, con lo que Tab no podía llegar nunca a
        # las pestañas; Ctrl+1/2/3 quedaba como única vía de acceso.
        if foco == self.cuaderno:
            if controles:
                controles[-1 if evento.ShiftDown() else 0].SetFocus()
                return
            evento.Skip()
            return
        indice = next(
            (posicion for posicion, control in enumerate(controles)
             if foco == control or (foco is not None and control.IsDescendant(foco))),
            None,
        )
        if indice is None:
            evento.Skip()
            return
        if evento.ShiftDown() and indice == 0:
            self.cuaderno.SetFocus()
            return
        if not evento.ShiftDown() and indice == len(controles) - 1:
            self.cuaderno.SetFocus()
            return
        controles[indice - 1 if evento.ShiftDown() else indice + 1].SetFocus()

    def _abrir_ayuda(self):
        """Abre la ayuda local con el navegador predeterminado, sin bloquear el afinador."""
        try:
            webbrowser.open(Path(RUTA_AYUDA).resolve().as_uri())
            self.anunciador.hablar("Ayuda abierta en el navegador.")
        except Exception:
            logger.exception("no se pudo abrir la ayuda local")
            self.anunciador.hablar("No se pudo abrir la ayuda local.")

    def _construir_atajos(self):
        """Ctrl+P reproduce el tono de referencia, Ctrl+E alterna la escucha, Ctrl+Mayús+Flecha
        arriba/abajo retoca la cuerda seleccionada en cuartos de tono, Ctrl+Mayús+R restablece
        ese retoque, Ctrl+Mayús+Z deshace el último retoque, y Ctrl+Mayús+P reproduce una
        escucha previa de toda la escala/afinación activa, y Ctrl+Mayús+V repite la última
        instrucción de afinación. Nunca se usa la tecla Espacio."""
        self.Bind(wx.EVT_MENU, self._al_reproducir_referencia, id=ID_ATAJO_REPRODUCIR_REFERENCIA)
        self.Bind(wx.EVT_MENU, self._al_alternar_escucha, id=ID_ATAJO_ALTERNAR_ESCUCHA)
        self.Bind(wx.EVT_MENU, self._al_subir_cuarto_tono, id=ID_ATAJO_SUBIR_CUARTO_TONO)
        self.Bind(wx.EVT_MENU, self._al_bajar_cuarto_tono, id=ID_ATAJO_BAJAR_CUARTO_TONO)
        self.Bind(wx.EVT_MENU, self._al_restablecer_ajuste_fino, id=ID_ATAJO_RESTABLECER_AJUSTE_FINO)
        self.Bind(wx.EVT_MENU, self._al_escucha_previa_escala, id=ID_ATAJO_ESCUCHA_PREVIA_ESCALA)
        self.Bind(wx.EVT_MENU, self._al_deshacer_retoque, id=ID_ATAJO_DESHACER_RETOQUE)
        self.Bind(wx.EVT_MENU, self._al_repetir_instruccion, id=ID_ATAJO_REPETIR_INSTRUCCION)
        tabla = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord("P"), ID_ATAJO_REPRODUCIR_REFERENCIA),
            (wx.ACCEL_CTRL, ord("E"), ID_ATAJO_ALTERNAR_ESCUCHA),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, wx.WXK_UP, ID_ATAJO_SUBIR_CUARTO_TONO),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, wx.WXK_DOWN, ID_ATAJO_BAJAR_CUARTO_TONO),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord("R"), ID_ATAJO_RESTABLECER_AJUSTE_FINO),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord("P"), ID_ATAJO_ESCUCHA_PREVIA_ESCALA),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord("Z"), ID_ATAJO_DESHACER_RETOQUE),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord("V"), ID_ATAJO_REPETIR_INSTRUCCION),
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
        for posicion, (_, valor) in enumerate(OPCIONES_CANAL_ENTRADA):
            if valor == self.ajustes.get("canal_entrada"):
                self.selector_canal.SetSelection(posicion)
                break
        self.control_la4.SetValue(float(self.ajustes.get("frecuencia_la4", 440.0)))
        self.casilla_pitido_confirmacion.SetValue(bool(self.ajustes.get("pitido_confirmacion", True)))
        self.casilla_desmutear_microfono.SetValue(
            bool(self.ajustes.get("desmutear_microfono_si_es_necesario", False))
        )
        self.control_ganancia.SetValue(float(self.ajustes.get("ganancia", 1.0)))
        self.control_sensibilidad.SetValue(float(self.ajustes.get("umbral_yin", 0.15)))
        self.casilla_bucle_referencia.SetValue(bool(self.ajustes.get("bucle_referencia", False)))
        self.casilla_avance_automatico.SetValue(bool(self.ajustes.get("avance_automatico", True)))
        self.casilla_modo_solo_escucha.SetValue(bool(self.ajustes.get("modo_solo_escucha", False)))
        self.casilla_deteccion_automatica_cuerda.SetValue(
            bool(self.ajustes.get("deteccion_automatica_cuerda", False))
        )
        self.selector_verbosidad.SetSelection(1 if self.ajustes.get("instrucciones_detalladas", False) else 0)
        self.selector_nomenclatura.SetSelection(
            1 if self.ajustes.get("nomenclatura_notas") == "americano" else 0
        )

        familia_maqam = self.ajustes.get("familia_maqam")
        if familia_maqam and self.selector_familia_maqam.FindString(familia_maqam) != wx.NOT_FOUND:
            self.selector_familia_maqam.SetStringSelection(familia_maqam)

        self._al_cambiar_instrumento(None)

        nombre_cuerda = self.ajustes.get("cuerda")
        if nombre_cuerda:
            posicion_cuerda = self.selector_cuerda.FindString(nombre_cuerda)
            if posicion_cuerda != wx.NOT_FOUND:
                self.selector_cuerda.SetSelection(posicion_cuerda)

        # La sesión cotidiana siempre arranca limpia: lira, afinación de fábrica.
        # Las demás afinaciones se recuperan conscientemente desde un perfil.
        self._aplicar_retoques_escala_activa()

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
            "canal_entrada": self._canal_entrada_seleccionado(),
            "frecuencia_la4": self.control_la4.GetValue(),
            "pitido_confirmacion": self.casilla_pitido_confirmacion.GetValue(),
            "duracion_ventana": self._duracion_ventana_seleccionada(),
            "preferir_exclusivo_wasapi": self.casilla_exclusivo_wasapi.GetValue(),
            "desmutear_microfono_si_es_necesario": self.casilla_desmutear_microfono.GetValue(),
            "ganancia": self.control_ganancia.GetValue(),
            "umbral_yin": self.control_sensibilidad.GetValue(),
            "bucle_referencia": self.casilla_bucle_referencia.GetValue(),
            "avance_automatico": self.casilla_avance_automatico.GetValue(),
            "modo_solo_escucha": self.casilla_modo_solo_escucha.GetValue(),
            "deteccion_automatica_cuerda": self.casilla_deteccion_automatica_cuerda.GetValue(),
            "instrucciones_detalladas": self.selector_verbosidad.GetSelection() == 1,
            "nomenclatura_notas": "americano" if self.selector_nomenclatura.GetSelection() == 1 else "solfeo",
            "escala": self.selector_escala.GetStringSelection() or None,
            "familia_maqam": self.selector_familia_maqam.GetStringSelection() or "Todas las familias",
            "perfiles_afinacion": self.perfiles_afinacion,
            "escala_base_personalizada": self.escala_base_personalizada,
        })
        # Un retoque manual es un borrador hasta que se guarde explícitamente
        # como perfil. Así "salir sin guardar" realmente lo descarta.
        if not self._retoques_sin_guardar:
            self.ajustes["ajustes_finos_cuerdas"] = self.ajustes_finos_cuerdas
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

    def _canal_entrada_seleccionado(self):
        posicion = self.selector_canal.GetSelection()
        return OPCIONES_CANAL_ENTRADA[posicion][1] if posicion != wx.NOT_FOUND else None

    def _preset_actual(self):
        nombre_instrumento = self.selector_instrumento.GetStringSelection()
        return PRESETS_INSTRUMENTO.get(nombre_instrumento)

    def _nombres_notas_actuales(self):
        return NOMBRES_NOTAS_AMERICANOS if self.selector_nomenclatura.GetSelection() == 1 else NOMBRES_NOTAS_SOSTENIDOS

    def _formatear_nota(self, indice_nota, octava):
        """Nombre visible y verbalizable; el cálculo musical sigue siendo numérico."""
        return "{} {}".format(self._nombres_notas_actuales()[indice_nota % 12], octava)

    def _al_cambiar_nomenclatura(self, evento):
        self._guardar_ajustes_actuales()
        self._actualizar_contexto_afinacion()
        self.anunciador.hablar(
            "Nombres de las notas: {}.".format(
                "cifrado americano" if self.selector_nomenclatura.GetSelection() == 1 else "Do Re Mi"
            )
        )
        evento.Skip()

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
        es_lira = instrumento == NOMBRE_LIRA
        self.selector_familia_maqam.Enable(es_lira)
        for control in (
            self.selector_afinacion_guardada, self.boton_guardar_afinacion,
            self.boton_cargar_afinacion, self.selector_paso_retoque,
            self.boton_subir_retoque, self.boton_bajar_retoque,
            self.boton_restablecer_retoque, self.boton_renombrar_afinacion,
            self.boton_eliminar_afinacion, self.boton_exportar_perfiles,
            self.boton_importar_perfiles,
        ):
            control.Enable(instrumento != CROMATICO)
        self.boton_abrir_perfiles.Enable(instrumento != CROMATICO)
        self._actualizar_lista_afinaciones_guardadas()
        self._actualizar_opciones_escala()
        # La lista ha cambiado: hay que cargar la afinación objetivo del nuevo
        # instrumento, no conservar los retoques de la lira anterior.
        self._aplicar_retoques_escala_activa()

        self.anunciador.reiniciar_estado()
        self._afinada_desde = None
        self._avance_ya_realizado = False
        self._actualizar_contexto_afinacion()
        if not es_lira:
            # En instrumentos con trastes nunca se ofrece un cuarto de tono como
            # edición manual: los trastes siguen siendo semitonos occidentales.
            self.selector_paso_retoque.SetSelection(max(1, self.selector_paso_retoque.GetSelection()))
        if evento is not None:
            self._guardar_ajustes_actuales()
            evento.Skip()

    def _al_cambiar_familia_maqam(self, evento):
        """Filtra los maqamat sin ocultar la afinación de fábrica de la lira."""
        self._actualizar_opciones_escala()
        self._aplicar_retoques_escala_activa()
        self._actualizar_contexto_afinacion()
        self._guardar_ajustes_actuales()
        self.anunciador.reiniciar_estado()
        self.anunciador.hablar(
            "Familia seleccionada: {}.".format(self.selector_familia_maqam.GetStringSelection())
        )
        evento.Skip()

    def _actualizar_opciones_escala(self, preferida=None):
        """Rellena el selector según instrumento y familia, manteniendo un orden predecible."""
        instrumento = self.selector_instrumento.GetStringSelection()
        seleccion_anterior = (
            preferida
            or self.selector_escala_rapida.GetStringSelection()
            or self.selector_escala.GetStringSelection()
        )
        if instrumento == NOMBRE_LIRA:
            familia = self.selector_familia_maqam.GetStringSelection()
            maqamat = (
                tuple(AFINACIONES_LIRA_MAQAM_24EDO)
                if familia == "Todas las familias"
                else FAMILIAS_MAQAM_LIRA.get(familia, ())
            )
            nombres = [NOMBRE_AFINACION_FABRICA_LIRA, NOMBRE_AFINACION_PERSONALIZADA_LIRA]
            nombres.extend(nombre for nombre in maqamat if nombre not in nombres)
        else:
            nombres = list(ESCALAS_POR_INSTRUMENTO.get(instrumento, {}))
            if nombres:
                nombres.insert(1, NOMBRE_AFINACION_PERSONALIZADA)

        for selector in (self.selector_escala_rapida, self.selector_escala):
            selector.Clear()
            for nombre in nombres:
                selector.Append(nombre)
            if nombres:
                posicion = selector.FindString(seleccion_anterior)
                selector.SetSelection(posicion if posicion != wx.NOT_FOUND else 0)
                selector.Enable()
            else:
                selector.Disable()

    def _actualizar_lista_afinaciones_guardadas(self):
        seleccion = self.selector_afinacion_guardada.GetStringSelection()
        instrumento = self.selector_instrumento.GetStringSelection()
        nombres = nombres_perfiles(self.perfiles_afinacion, instrumento)
        self.selector_afinacion_guardada.Clear()
        self.selector_afinacion_guardada.Append("Selecciona una afinación guardada")
        for nombre in nombres:
            self.selector_afinacion_guardada.Append(nombre)
        posicion = self.selector_afinacion_guardada.FindString(seleccion)
        self.selector_afinacion_guardada.SetSelection(posicion if posicion != wx.NOT_FOUND else 0)

    def _al_cambiar_escala(self, evento):
        self._cambiar_escala(evento.GetEventObject().GetStringSelection(), evento)

    def _al_cambiar_escala_rapida(self, evento):
        self._cambiar_escala(evento.GetEventObject().GetStringSelection(), evento)

    def _cambiar_escala(self, nombre_escala, evento=None):
        """Aplica una escala desde cualquiera de los dos selectores sincronizados."""
        if not nombre_escala:
            return
        self._actualizar_opciones_escala(preferida=nombre_escala)
        self._perfil_cargado = None
        self._aplicar_retoques_escala_activa(borrar_retoques=True)
        self._actualizar_contexto_afinacion()
        self._guardar_ajustes_actuales()
        self.anunciador.reiniciar_estado()
        self._afinada_desde = None
        self._avance_ya_realizado = False
        self._historial_frecuencias.clear()
        self.anunciador.hablar("Afinación aplicada: {}.".format(nombre_escala))
        if evento is not None:
            evento.Skip()

    def _actualizar_contexto_afinacion(self):
        """Explica la tónica real sin confundirla con la cuerda más grave de la lira."""
        if self.selector_instrumento.GetStringSelection() != NOMBRE_LIRA:
            self.etiqueta_contexto_afinacion.SetLabel("")
            return
        nombre = self.selector_escala.GetStringSelection()
        if nombre == NOMBRE_AFINACION_FABRICA_LIRA:
            texto = "Afinación de fábrica: notas de Do mayor. La cuerda más grave es Sol, pero no hay una tónica obligatoria hasta que toques una melodía o escala."
        elif nombre == NOMBRE_AFINACION_PERSONALIZADA_LIRA:
            texto = "Afinación personalizada: conserva tus retoques manuales. Comprueba cada nota objetivo antes de tocar."
        elif nombre in REFERENCIAS_GRADOS_MAQAM_24EDO:
            tonica = nombre.split("(sobre ", 1)[1].rstrip(")")
            texto = (
                "Tónica del maqam: {}. La escucha empieza por Sol grave porque es la primera cuerda física de la lira; "
                "no significa que Sol sea la tónica. Esta adaptación conserva los siete grados en una afinación fija de lira."
            ).format(tonica)
        else:
            texto = "Afinación seleccionada."
        self.etiqueta_contexto_afinacion.SetLabel(texto)
        self.etiqueta_contexto_afinacion.Wrap(560)

    def _aplicar_retoques_escala_activa(self, borrar_retoques=False):
        """Carga los retoques de la escala; la afinación de fábrica siempre es pura."""
        instrumento = self.selector_instrumento.GetStringSelection()
        nombre_escala = self.selector_escala.GetStringSelection()
        if borrar_retoques or (instrumento == NOMBRE_LIRA and nombre_escala == NOMBRE_AFINACION_FABRICA_LIRA):
            prefijo = instrumento + "||"
            self.ajustes_finos_cuerdas = {
                clave: valor for clave, valor in self.ajustes_finos_cuerdas.items()
                if not clave.startswith(prefijo)
            }
        escala_base = nombre_escala
        if nombre_escala in (NOMBRE_AFINACION_PERSONALIZADA_LIRA, NOMBRE_AFINACION_PERSONALIZADA):
            escala_base = self.escala_base_personalizada.get(instrumento, next(iter(ESCALAS_POR_INSTRUMENTO[instrumento]), ""))
        desplazamientos = ESCALAS_POR_INSTRUMENTO.get(instrumento, {}).get(escala_base, {})
        self.retoques_escala_activa = {
            "{}||{}".format(instrumento, nombre_cuerda): cuartos_tono
            for nombre_cuerda, cuartos_tono in desplazamientos.items()
        }

    def _al_cambiar_cuerda(self, evento):
        self.anunciador.reiniciar_estado()
        self._afinada_desde = None
        self._avance_ya_realizado = False
        self._guardar_ajustes_actuales()
        cuartos_tono = self._cuartos_tono_actual()
        if cuartos_tono != 0:
            self.anunciador.hablar(self._descripcion_objetivo_cuerda())
        evento.Skip()

    @staticmethod
    def _descripcion_retoque(cuartos_tono):
        direccion = "más alta" if cuartos_tono > 0 else "más baja"
        cantidad = abs(cuartos_tono)
        if cantidad == 1:
            distancia = "un cuarto de tono"
        elif cantidad == 2:
            distancia = "un semitono"
        else:
            distancia = "{} cents".format(cantidad * CENTS_POR_CUARTO_TONO)
        return "Objetivo de esta cuerda: {} {} que su afinación de fábrica.".format(distancia, direccion)

    def _descripcion_objetivo_cuerda(self):
        """Nombra el objetivo sin exigir que la persona interprete cents."""
        cuerda_objetivo = self._cuerda_objetivo()
        if cuerda_objetivo is None:
            return "No hay una cuerda objetivo seleccionada."
        _, indice_nota, octava = cuerda_objetivo
        cuartos_tono = self._cuartos_tono_actual()
        indice_en_cuartos = indice_nota * 2 + cuartos_tono
        octava_objetivo = octava + indice_en_cuartos // 24
        posicion_en_octava = indice_en_cuartos % 24
        if posicion_en_octava % 2 == 0:
            nombre = self._nombres_notas_actuales()[posicion_en_octava // 2]
        elif cuartos_tono < 0:
            nombre = self._nombres_notas_actuales()[((posicion_en_octava + 1) // 2) % 12] + " medio bemol"
        else:
            nombre = self._nombres_notas_actuales()[((posicion_en_octava - 1) // 2) % 12] + " medio sostenido"
        return "Objetivo de esta cuerda: {} {}.".format(nombre, octava_objetivo)

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
        retoque_manual = self.ajustes_finos_cuerdas.get(clave, 0)
        return self.retoques_escala_activa.get(clave, 0) + retoque_manual

    def _frecuencia_objetivo_actual(self):
        """Frecuencia real de la cuerda seleccionada, incluyendo el retoque fino en cuartos
        de tono si lo hay. None en modo Cromático (sin cuerda objetivo)."""
        cuerda_objetivo = self._cuerda_objetivo()
        if cuerda_objetivo is None:
            return None
        _, indice_nota, octava = cuerda_objetivo
        return frecuencia_con_desplazamiento(indice_nota, octava, self._cuartos_tono_actual())

    def _desplazar_cuarto_tono(self, delta):
        instrumento = self.selector_instrumento.GetStringSelection()
        if instrumento == CROMATICO:
            self.anunciador.hablar("El modo cromático no tiene cuerdas objetivo que retocar.")
            return
        if instrumento != NOMBRE_LIRA and abs(delta) % 2:
            self.anunciador.hablar("En guitarra y ukelele usa semitonos o tonos; sus trastes no se adaptan a cuartos de tono.")
            return
        clave = self._clave_ajuste_fino()
        if clave is None:
            self.anunciador.hablar("No hay ninguna cuerda seleccionada para retocar.")
            return
        retoque_manual_previo = self.ajustes_finos_cuerdas.get(clave, 0)
        desplazamiento_previo = self.retoques_escala_activa.get(clave, 0) + retoque_manual_previo
        desplazamiento_nuevo = desplazamiento_previo + delta
        # Dos semitonos por encima de la tensión estándar ya es una subida notable.
        # No bloqueamos: la cuerda y el calibre pueden permitirlo, pero la decisión
        # debe ser consciente, especialmente en instrumentos pequeños.
        if desplazamiento_previo < 4 <= desplazamiento_nuevo:
            respuesta = wx.MessageBox(
                "Vas a subir esta cuerda dos semitonos o más respecto a su afinación estándar. "
                "Puede aumentar mucho la tensión y romper la cuerda. ¿Quieres continuar?",
                "Aviso de tensión de cuerda",
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
                self,
            )
            if respuesta != wx.YES:
                self.anunciador.hablar("Ajuste cancelado para proteger la cuerda.")
                return
        escala_actual = self.selector_escala.GetStringSelection()
        personalizada = NOMBRE_AFINACION_PERSONALIZADA_LIRA if instrumento == NOMBRE_LIRA else NOMBRE_AFINACION_PERSONALIZADA
        if escala_actual != personalizada:
            self.escala_base_personalizada[instrumento] = escala_actual
            self._actualizar_opciones_escala(preferida=personalizada)
            self._aplicar_retoques_escala_activa()
        if not self._retoques_sin_guardar:
            self._retoques_antes_de_editar = dict(self.ajustes_finos_cuerdas)
            self._retoques_sin_guardar = True
        self._historial_retoques.append((clave, retoque_manual_previo))
        retoque_manual = retoque_manual_previo + delta
        self.ajustes_finos_cuerdas[clave] = retoque_manual
        self.anunciador.reiniciar_estado()
        self._afinada_desde = None
        self._avance_ya_realizado = False
        self._historial_frecuencias.clear()

        self.anunciador.hablar(
            "Ajuste manual aplicado. {}".format(self._descripcion_objetivo_cuerda())
        )

    def _paso_retoque_seleccionado(self):
        posicion = self.selector_paso_retoque.GetSelection()
        if posicion == wx.NOT_FOUND:
            return 1
        return OPCIONES_PASO_RETOQUE[posicion][1]

    def _al_subir_cuarto_tono(self, evento):
        self._desplazar_cuarto_tono(self._paso_retoque_seleccionado())

    def _al_bajar_cuarto_tono(self, evento):
        self._desplazar_cuarto_tono(-self._paso_retoque_seleccionado())

    def _al_restablecer_ajuste_fino(self, evento):
        instrumento = self.selector_instrumento.GetStringSelection()
        if instrumento == CROMATICO:
            self.anunciador.hablar("El modo cromático no tiene cuerdas objetivo que restablecer.")
            return
        clave = self._clave_ajuste_fino()
        if clave is None or clave not in self.ajustes_finos_cuerdas:
            self.anunciador.hablar("Esta cuerda no tiene ningún ajuste manual que restablecer.")
            return
        if not self._retoques_sin_guardar:
            self._retoques_antes_de_editar = dict(self.ajustes_finos_cuerdas)
            self._retoques_sin_guardar = True
        del self.ajustes_finos_cuerdas[clave]
        self.anunciador.reiniciar_estado()
        self._afinada_desde = None
        self._avance_ya_realizado = False
        self._historial_frecuencias.clear()
        volvimos_a_fabrica = False
        if (
            self.selector_escala.GetStringSelection() == (NOMBRE_AFINACION_PERSONALIZADA_LIRA if instrumento == NOMBRE_LIRA else NOMBRE_AFINACION_PERSONALIZADA)
            and not any(clave.startswith(instrumento + "||") for clave in self.ajustes_finos_cuerdas)
        ):
            escala_base = self.escala_base_personalizada.get(instrumento, NOMBRE_AFINACION_FABRICA_LIRA if instrumento == NOMBRE_LIRA else next(iter(ESCALAS_POR_INSTRUMENTO[instrumento])))
            self._actualizar_opciones_escala(preferida=escala_base)
            self._aplicar_retoques_escala_activa()
            self._actualizar_contexto_afinacion()
            volvimos_a_fabrica = True
        mensaje = (
            "Ajuste manual restablecido. Vuelves a la afinación de fábrica."
            if volvimos_a_fabrica
            else "Ajuste manual restablecido. La escala seleccionada se mantiene."
        )
        self.anunciador.hablar(mensaje)

    def _al_abrir_perfiles(self, evento):
        """Abre una ventana breve para no llenar la pestaña de afinación."""
        instrumento = self.selector_instrumento.GetStringSelection()
        if instrumento == CROMATICO:
            self.anunciador.hablar("El modo cromático no tiene perfiles de cuerdas.")
            return

        dialogo = wx.Dialog(
            self, title="Perfiles personales: {}".format(instrumento),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        panel = wx.Panel(dialogo)
        etiqueta = wx.StaticText(panel, label="Afinaciones guardadas para {}:".format(instrumento))
        selector = wx.Choice(panel)
        selector.SetHelpText("Selecciona un perfil de este instrumento para cargarlo.")
        explicacion = wx.StaticText(
            panel,
            label=("Guardar crea una copia de la afinación actual. Para renombrar, eliminar, "
                   "importar o exportar perfiles usa la pestaña Afinaciones especiales."),
        )
        explicacion.Wrap(420)
        boton_cargar = wx.Button(panel, label="Cargar perfil seleccionado")
        aplicar_icono_boton(boton_cargar, "cargar")
        boton_guardar = wx.Button(panel, label="Guardar afinación actual como perfil...")
        aplicar_icono_boton(boton_guardar, "guardar")
        boton_cerrar = wx.Button(panel, wx.ID_CLOSE, "Cerrar")

        def rellenar_selector(preferido=None):
            seleccionado = preferido or selector.GetStringSelection()
            selector.Clear()
            selector.Append("Selecciona una afinación guardada")
            for nombre in nombres_perfiles(self.perfiles_afinacion, instrumento):
                selector.Append(nombre)
            posicion = selector.FindString(seleccionado)
            selector.SetSelection(posicion if posicion != wx.NOT_FOUND else 0)

        def cargar(evento_cargar):
            nombre = selector.GetStringSelection()
            if not self.perfiles_afinacion.get(instrumento, {}).get(nombre):
                self.anunciador.hablar("Selecciona primero una afinación guardada.")
                return
            self.selector_afinacion_guardada.SetStringSelection(nombre)
            self._cargar_afinacion_personal_desde_selector(self.selector_afinacion_guardada)
            dialogo.EndModal(wx.ID_OK)

        def guardar(evento_guardar):
            self._al_guardar_afinacion_personal(None)
            rellenar_selector(self.selector_afinacion_guardada.GetStringSelection())

        boton_cargar.Bind(wx.EVT_BUTTON, cargar)
        boton_guardar.Bind(wx.EVT_BUTTON, guardar)
        boton_cerrar.Bind(wx.EVT_BUTTON, lambda _evento: dialogo.EndModal(wx.ID_CLOSE))
        filas = wx.BoxSizer(wx.VERTICAL)
        for control in (etiqueta, selector, boton_cargar, boton_guardar, explicacion, boton_cerrar):
            filas.Add(control, 0, wx.EXPAND | wx.ALL, 6)
        panel.SetSizer(filas)
        marco = wx.BoxSizer(wx.VERTICAL)
        marco.Add(panel, 1, wx.EXPAND | wx.ALL, 8)
        dialogo.SetSizerAndFit(marco)
        dialogo.SetMinSize((460, -1))
        rellenar_selector()
        try:
            dialogo.ShowModal()
        finally:
            dialogo.Destroy()

    def _al_guardar_afinacion_personal(self, evento):
        instrumento = self.selector_instrumento.GetStringSelection()
        if instrumento == CROMATICO:
            self.anunciador.hablar("El modo cromático no tiene una afinación de cuerdas que guardar.")
            return
        dialogo = wx.TextEntryDialog(
            self, "Escribe un nombre claro para esta afinación.", "Guardar afinación personal"
        )
        try:
            if dialogo.ShowModal() != wx.ID_OK:
                return
            nombre = dialogo.GetValue().strip()
        finally:
            dialogo.Destroy()
        if not nombre:
            self.anunciador.hablar("No se guardó la afinación porque no tiene nombre.")
            return
        perfiles_instrumento = self.perfiles_afinacion.setdefault(instrumento, {})
        if nombre in perfiles_instrumento:
            respuesta = wx.MessageBox(
                "Ya existe una afinación con ese nombre. ¿Quieres reemplazarla?",
                "Reemplazar afinación guardada",
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
                self,
            )
            if respuesta != wx.YES:
                return
        prefijo = instrumento + "||"
        manuales = {
            clave[len(prefijo):]: valor for clave, valor in self.ajustes_finos_cuerdas.items()
            if clave.startswith(prefijo) and valor
        }
        escala_base = self.selector_escala.GetStringSelection()
        if escala_base in (NOMBRE_AFINACION_PERSONALIZADA_LIRA, NOMBRE_AFINACION_PERSONALIZADA):
            escala_base = self.escala_base_personalizada.get(instrumento, NOMBRE_AFINACION_FABRICA_LIRA if instrumento == NOMBRE_LIRA else next(iter(ESCALAS_POR_INSTRUMENTO[instrumento])))
        guardar_perfil(self.perfiles_afinacion, instrumento, nombre, escala_base, manuales,
                       self.selector_familia_maqam.GetStringSelection() if instrumento == NOMBRE_LIRA else None)
        self._actualizar_lista_afinaciones_guardadas()
        self.selector_afinacion_guardada.SetStringSelection(nombre)
        self._retoques_sin_guardar = False
        self._retoques_antes_de_editar = None
        self._guardar_ajustes_actuales()
        self.anunciador.hablar("Afinación guardada: {}.".format(nombre))

    def _al_cargar_afinacion_personal(self, evento):
        self._cargar_afinacion_personal_desde_selector(self.selector_afinacion_guardada)

    def _cargar_afinacion_personal_desde_selector(self, selector):
        nombre = selector.GetStringSelection()
        instrumento = self.selector_instrumento.GetStringSelection()
        datos = self.perfiles_afinacion.get(instrumento, {}).get(nombre)
        if not datos:
            self.anunciador.hablar("Selecciona primero una afinación guardada.")
            return
        escala_base = datos.get("escala_base", NOMBRE_AFINACION_FABRICA_LIRA)
        familia = datos.get("familia_maqam", "Todas las familias")
        if instrumento == NOMBRE_LIRA and escala_base in REFERENCIAS_GRADOS_MAQAM_24EDO:
            familia = next(
                (nombre_familia for nombre_familia, maqamat in FAMILIAS_MAQAM_LIRA.items()
                 if escala_base in maqamat),
                "Todas las familias",
            )
        if self.selector_familia_maqam.FindString(familia) == wx.NOT_FOUND:
            familia = "Todas las familias"
        if instrumento == NOMBRE_LIRA:
            self.selector_familia_maqam.SetStringSelection(familia)
        self._actualizar_opciones_escala(preferida=escala_base)
        if self.selector_escala.FindString(escala_base) == wx.NOT_FOUND:
            escala_base = (
                NOMBRE_AFINACION_FABRICA_LIRA if instrumento == NOMBRE_LIRA
                else next(iter(ESCALAS_POR_INSTRUMENTO[instrumento]), "")
            )
            self._actualizar_opciones_escala(preferida=escala_base)
        self._actualizar_opciones_escala(preferida=escala_base)
        self._aplicar_retoques_escala_activa()
        prefijo = instrumento + "||"
        self.ajustes_finos_cuerdas = {
            clave: valor for clave, valor in self.ajustes_finos_cuerdas.items()
            if not clave.startswith(prefijo)
        }
        for nombre_cuerda, valor in datos.get("retoques_manuales", {}).items():
            self.ajustes_finos_cuerdas[prefijo + nombre_cuerda] = int(valor)
        self._perfil_cargado = nombre
        self._retoques_sin_guardar = False
        self._retoques_antes_de_editar = None
        self.selector_afinacion_guardada.SetStringSelection(nombre)
        self._actualizar_contexto_afinacion()
        self._guardar_ajustes_actuales()
        self.anunciador.reiniciar_estado()
        self.anunciador.hablar("Afinación cargada: {}.".format(nombre))

    def _al_renombrar_afinacion_personal(self, evento):
        instrumento = self.selector_instrumento.GetStringSelection()
        nombre_anterior = self.selector_afinacion_guardada.GetStringSelection()
        perfiles = self.perfiles_afinacion.get(instrumento, {})
        if nombre_anterior not in perfiles:
            self.anunciador.hablar("Selecciona primero un perfil que quieras renombrar.")
            return
        dialogo = wx.TextEntryDialog(
            self, "Escribe el nuevo nombre del perfil.", "Renombrar perfil", value=nombre_anterior
        )
        try:
            if dialogo.ShowModal() != wx.ID_OK:
                return
            nombre_nuevo = dialogo.GetValue().strip()
        finally:
            dialogo.Destroy()
        if not nombre_nuevo:
            self.anunciador.hablar("El perfil conserva su nombre porque no escribiste uno nuevo.")
            return
        if nombre_nuevo != nombre_anterior and nombre_nuevo in perfiles:
            self.anunciador.hablar("Ya existe un perfil con ese nombre.")
            return
        if nombre_nuevo == nombre_anterior:
            return
        perfiles[nombre_nuevo] = perfiles.pop(nombre_anterior)
        self._actualizar_lista_afinaciones_guardadas()
        self.selector_afinacion_guardada.SetStringSelection(nombre_nuevo)
        self._guardar_ajustes_actuales()
        self.anunciador.hablar("Perfil renombrado a {}.".format(nombre_nuevo))

    def _al_eliminar_afinacion_personal(self, evento):
        instrumento = self.selector_instrumento.GetStringSelection()
        nombre = self.selector_afinacion_guardada.GetStringSelection()
        perfiles = self.perfiles_afinacion.get(instrumento, {})
        if nombre not in perfiles:
            self.anunciador.hablar("Selecciona primero un perfil que quieras eliminar.")
            return
        respuesta = wx.MessageBox(
            "¿Eliminar definitivamente el perfil '{}'? Los presets incluidos no se borrarán.".format(nombre),
            "Eliminar perfil de afinación",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
            self,
        )
        if respuesta != wx.YES:
            self.anunciador.hablar("Eliminación cancelada.")
            return
        del perfiles[nombre]
        self._actualizar_lista_afinaciones_guardadas()
        self._guardar_ajustes_actuales()
        self.anunciador.hablar("Perfil eliminado: {}.".format(nombre))

    def _al_exportar_perfiles(self, evento):
        dialogo = wx.FileDialog(
            self, "Exportar perfiles de afinación", wildcard="Archivos JSON (*.json)|*.json",
            defaultFile="perfiles_afinador_accesible.json", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
        try:
            if dialogo.ShowModal() != wx.ID_OK:
                return
            ruta = dialogo.GetPath()
        finally:
            dialogo.Destroy()
        try:
            with open(ruta, "w", encoding="utf-8") as archivo:
                json.dump({"formato": 1, "perfiles_afinacion": self.perfiles_afinacion}, archivo,
                          ensure_ascii=False, indent=2)
        except Exception:
            logger.exception("no se pudieron exportar los perfiles")
            self.anunciador.hablar("No se pudo exportar la copia de perfiles.")
            return
        self.anunciador.hablar("Copia de perfiles exportada correctamente.")

    def _al_importar_perfiles(self, evento):
        dialogo = wx.FileDialog(
            self, "Importar perfiles de afinación", wildcard="Archivos JSON (*.json)|*.json",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        try:
            if dialogo.ShowModal() != wx.ID_OK:
                return
            ruta = dialogo.GetPath()
        finally:
            dialogo.Destroy()
        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                contenido = json.load(archivo)
            perfiles_importados = contenido.get("perfiles_afinacion", contenido)
            if not isinstance(perfiles_importados, dict):
                raise ValueError("el archivo no contiene perfiles válidos")
        except Exception:
            logger.exception("no se pudieron importar los perfiles")
            self.anunciador.hablar("No se pudo leer esa copia de perfiles.")
            return
        anadidos = 0
        omitidos = 0
        for instrumento, perfiles in perfiles_importados.items():
            if instrumento not in PRESETS_INSTRUMENTO or not isinstance(perfiles, dict):
                omitidos += len(perfiles) if isinstance(perfiles, dict) else 1
                continue
            destino = self.perfiles_afinacion.setdefault(instrumento, {})
            for nombre, datos in perfiles.items():
                if nombre in destino or not isinstance(datos, dict):
                    omitidos += 1
                    continue
                destino[nombre] = datos
                anadidos += 1
        self._actualizar_lista_afinaciones_guardadas()
        self._guardar_ajustes_actuales()
        self.anunciador.hablar(
            "Importación terminada: {} perfiles añadidos y {} omitidos para no sobrescribir los existentes."
            .format(anadidos, omitidos)
        )

    def _al_deshacer_retoque(self, evento):
        if not self._historial_retoques:
            self.anunciador.hablar("No hay ningún retoque que deshacer.")
            return
        clave, cuartos_tono_previo = self._historial_retoques.pop()
        if cuartos_tono_previo == 0:
            self.ajustes_finos_cuerdas.pop(clave, None)
        else:
            self.ajustes_finos_cuerdas[clave] = cuartos_tono_previo
        self._retoques_sin_guardar = True
        self.anunciador.reiniciar_estado()
        self._afinada_desde = None
        self._avance_ya_realizado = False
        self._historial_frecuencias.clear()
        _, nombre_cuerda = clave.split("||", 1)
        self.anunciador.hablar("Deshecho el último retoque de {}.".format(nombre_cuerda))

    # ANCLAJE_INICIO: REPETIR_INSTRUCCION_AFINACION
    def _al_repetir_instruccion(self, evento):
        if self._ultima_instruccion_afinacion is None:
            self.anunciador.hablar("Todavía no hay ninguna instrucción de afinación que repetir.")
            return
        self.anunciador.hablar(self._ultima_instruccion_afinacion)
    # ANCLAJE_FIN: REPETIR_INSTRUCCION_AFINACION

    def _al_escucha_previa_escala(self, evento):
        try:
            instrumento = self.selector_instrumento.GetStringSelection()
            preset = PRESETS_INSTRUMENTO.get(instrumento)
            if not preset:
                self.anunciador.hablar("No hay ninguna afinación que previsualizar en modo Cromático.")
                return
            frecuencias = []
            for nombre_cuerda, indice_nota, octava in preset:
                clave = "{}||{}".format(instrumento, nombre_cuerda)
                cuartos_tono = self.retoques_escala_activa.get(clave, 0) + self.ajustes_finos_cuerdas.get(clave, 0)
                frecuencia = frecuencia_con_desplazamiento(indice_nota, octava, cuartos_tono)
                if not isinstance(frecuencia, (float, int)) or frecuencia <= 0:
                    raise ValueError("frecuencia no válida para {}: {!r}".format(nombre_cuerda, frecuencia))
                frecuencias.append(frecuencia)
            logger.info(
                "escucha previa solicitada: instrumento=%s escala=%s cuerdas=%s frecuencias=%s",
                instrumento, self.selector_escala.GetStringSelection(), len(preset), frecuencias,
            )
            self.anunciador.hablar(
                "Escucha previa de la afinación objetivo: {} cuerdas, desde la más grave a la más aguda."
                .format(len(preset))
            )
            self.generador_tonos.reproducir_secuencia(
                frecuencias,
                al_finalizar=lambda: wx.CallAfter(self.anunciador.hablar, "Escucha previa terminada.")
            )
        except Exception:
            logger.exception("fallo al preparar la escucha previa de la afinación")
            self.anunciador.hablar(
                "No se pudo iniciar la escucha previa. El detalle se ha guardado en registros, errores."
            )

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

    def _al_cambiar_la4(self, evento):
        establecer_frecuencia_la4(self.control_la4.GetValue())
        self._historial_frecuencias.clear()
        self.anunciador.reiniciar_estado()
        self._guardar_ajustes_actuales()
        self.anunciador.hablar("Referencia La4: {:.1f} hercios.".format(self.control_la4.GetValue()))
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
        if self.casilla_desmutear_microfono.GetValue():
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
            canal_entrada=self._canal_entrada_seleccionado(),
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
        self._marca_tiempo_ultima_actualizacion = time.monotonic()
        self._aviso_captura_interrumpida = False
        self._historial_frecuencias.clear()
        self._temporizador_diagnostico = wx.CallLater(
            int(SEGUNDOS_ESPERA_DIAGNOSTICO_SENAL * 1000), self._comprobar_senal_de_audio
        )
        self._temporizador_vigilancia = wx.CallLater(5000, self._vigilar_captura)

    def _detener_escucha(self):
        if getattr(self, "_temporizador_diagnostico", None) is not None:
            self._temporizador_diagnostico.Stop()
            self._temporizador_diagnostico = None
        if getattr(self, "_temporizador_vigilancia", None) is not None:
            self._temporizador_vigilancia.Stop()
            self._temporizador_vigilancia = None
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
        self._actualizar_indicador_visual(None, "Esperando una nota")
        self._ultima_instruccion_afinacion = None

    def _actualizar_indicador_visual(self, cents, texto_estado):
        """Actualiza una barra con texto; nunca depende solo del color."""
        if cents is None:
            self.indicador_desviacion.SetValue(50)
        else:
            self.indicador_desviacion.SetValue(max(0, min(100, int(round(cents)) + 50)))
        self.etiqueta_visual_afinacion.SetLabel("Indicador visual: {}".format(texto_estado))

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

    def _vigilar_captura(self):
        if self.capturador is None:
            return
        if time.monotonic() - self._marca_tiempo_ultima_actualizacion > 8.0:
            if not self._aviso_captura_interrumpida:
                self._aviso_captura_interrumpida = True
                self.anunciador.hablar("La captura de audio parece haberse interrumpido. Detén e inicia la escucha de nuevo.")
        else:
            self._aviso_captura_interrumpida = False
        self._temporizador_vigilancia = wx.CallLater(5000, self._vigilar_captura)

    def _al_detectar_tono(self, resultado, rms):
        wx.CallAfter(self._actualizar_deteccion, resultado, rms)

    @staticmethod
    def _categoria_nivel(rms):
        if rms < NIVEL_MINIMO_SENAL_DIAGNOSTICO:
            return "sin_senal"
        if rms < NIVEL_SENAL_BUENA:
            return "senal_debil"
        return "senal_buena"

    MARGEN_CENTS_DETECCION_AUTOMATICA = 55

    def _detectar_cuerda_automaticamente(self, frecuencia_filtrada):
        """Compara la frecuencia detectada contra todas las cuerdas del preset activo (con sus
        retoques) y selecciona la más cercana, sin que la usuaria tenga que elegir cuerda antes
        de tocar. Solo cambia de selección si la coincidencia es razonablemente cercana, para no
        saltar de cuerda con ruido o armónicos ambiguos."""
        preset = self._preset_actual()
        if not preset:
            return
        instrumento = self.selector_instrumento.GetStringSelection()
        mejor_indice = None
        mejor_diferencia = None
        for indice, (nombre_cuerda, indice_nota, octava) in enumerate(preset):
            clave = "{}||{}".format(instrumento, nombre_cuerda)
            cuartos_tono = self.retoques_escala_activa.get(clave, 0) + self.ajustes_finos_cuerdas.get(clave, 0)
            frecuencia_cuerda = frecuencia_con_desplazamiento(indice_nota, octava, cuartos_tono)
            diferencia = abs(1200 * np.log2(frecuencia_filtrada / frecuencia_cuerda))
            if mejor_diferencia is None or diferencia < mejor_diferencia:
                mejor_diferencia = diferencia
                mejor_indice = indice

        if (mejor_indice is None or mejor_diferencia > self.MARGEN_CENTS_DETECCION_AUTOMATICA
                or mejor_indice == self.selector_cuerda.GetSelection()):
            return

        self.selector_cuerda.SetSelection(mejor_indice)
        self.anunciador.hablar("Cuerda detectada: {}.".format(preset[mejor_indice][0]))
        self.anunciador.reiniciar_estado()
        self._afinada_desde = None
        self._avance_ya_realizado = False
        self._confirmacion_pendiente = True

    def _actualizar_deteccion(self, resultado, rms):
        self._marca_tiempo_ultima_actualizacion = time.monotonic()
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
            self._actualizar_indicador_visual(None, "sin nota estable")
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

        if self.casilla_deteccion_automatica_cuerda.GetValue():
            self._detectar_cuerda_automaticamente(frecuencia_filtrada)

        cuerda_objetivo = self._cuerda_objetivo()
        frecuencia_objetivo = self._frecuencia_objetivo_actual()
        if frecuencia_objetivo is not None:
            cents = 1200 * np.log2(frecuencia_filtrada / frecuencia_objetivo)
        else:
            cents = resultado["cents"]

        instruccion = calcular_instruccion(cents)
        texto_instruccion = TEXTOS_INSTRUCCION.get(instruccion, "—")
        if self.selector_verbosidad.GetSelection() == 1 and instruccion is not None:
            texto_instruccion = "{} ({:+.0f} cents)".format(texto_instruccion, cents)

        texto_nota = "Nota detectada: {}".format(
            self._formatear_nota(resultado["indice_nota"], resultado["octava"])
        )
        if self.selector_verbosidad.GetSelection() == 1:
            texto_nota += " ({:+.0f} cents)".format(cents)
        self.etiqueta_nota.SetLabel(texto_nota)

        if registrar_log:
            logger.info(
                "Nivel actual: rms=%.4f nota=%s%s cents=%+.1f instruccion=%s instrumento=%s cuerda=%s",
                rms, resultado["nombre"], resultado["octava"], cents, instruccion,
                self.selector_instrumento.GetStringSelection(), self.selector_cuerda.GetStringSelection(),
            )

        if self.casilla_modo_solo_escucha.GetValue():
            # Solo dice la nota que suena, sin instrucciones de sube/baja ni confirmación de
            # afinada: para quien solo quiere identificar por oído lo que está tocando.
            self.etiqueta_instruccion.SetLabel("Instrucción: — (modo solo escucha)")
            self._actualizar_indicador_visual(cents, "nota detectada; modo solo escucha")
            self._ultima_instruccion_afinacion = None
            self.anunciador.procesar_instruccion(
                self._formatear_nota(resultado["indice_nota"], resultado["octava"])
            )
            return

        self.etiqueta_instruccion.SetLabel("Instrucción: {}".format(texto_instruccion))
        self._actualizar_indicador_visual(cents, texto_instruccion)
        self._ultima_instruccion_afinacion = texto_instruccion

        if instruccion != "AFINADA":
            self._confirmacion_pendiente = True
            self._afinada_desde = None
            self._avance_ya_realizado = False
        self.anunciador.procesar_instruccion(texto_instruccion)
        if instruccion == "AFINADA" and self._confirmacion_pendiente:
            self._confirmacion_pendiente = False
            if self.casilla_pitido_confirmacion.GetValue():
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
        cuartos_tono = self._cuartos_tono_actual()
        if frecuencia is None:
            frecuencia = nota_a_frecuencia(9, 4)  # La4, referencia estándar en modo cromático
            self.anunciador.hablar("Referencia: La4 (440 Hz), modo cromático.")
        elif cuartos_tono != 0:
            self.anunciador.hablar("Referencia: {}".format(self._descripcion_objetivo_cuerda()))
        else:
            self.anunciador.hablar("Referencia: nota de fábrica de esta cuerda, sin retoque.")

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
        if self._retoques_sin_guardar:
            respuesta = wx.MessageBox(
                "Has modificado una afinación sin guardarla como perfil. ¿Quieres guardarla ahora?",
                "Guardar afinación antes de salir",
                wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION,
                self,
            )
            if respuesta == wx.CANCEL:
                return
            if respuesta == wx.YES:
                self._al_guardar_afinacion_personal(None)
                if self._retoques_sin_guardar:
                    return
            else:
                self.ajustes_finos_cuerdas = dict(self._retoques_antes_de_editar or {})
                self._retoques_sin_guardar = False
                self._retoques_antes_de_editar = None
        self._guardar_ajustes_actuales()
        self._detener_escucha()
        evento.Skip()
# ANCLAJE_FIN: ventana_principal
