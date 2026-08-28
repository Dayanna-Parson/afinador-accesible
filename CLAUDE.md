# CLAUDE.md — AfinadorAccesible

Léelo entero antes de tocar nada. Estas reglas no son sugerencias.

---

## Identidad del proyecto

**AfinadorAccesible** es una aplicación de escritorio para Windows: un afinador cromático universal y 100% accesible para personas ciegas usuarias de lectores de pantalla (NVDA, JAWS, Narrador). Permite afinar instrumentos de cuerda (lira de 16 cuerdas Aklot, ukelele, guitarra, o cualquier nota en modo cromático) con detección de tono en tiempo real y retroalimentación por voz.

- Desarrolladora: Dayanna Parson (TifloTutos · tiflotutos.com)
- Python 3.12+ · wxPython 4.2+ · extensión nativa opcional en Rust · Windows como plataforma principal

---

## Reglas absolutas de colaboración

### Sin rastro de conversaciones
No incluyas en el código ni en los comentarios ninguna referencia a conversaciones anteriores, sugerencias de IA, sesiones de trabajo, ni nada que no sea parte de la lógica propia de la aplicación. El código debe parecer escrito íntegramente por la desarrolladora.

### Todo en español
Variables, funciones, clases, comentarios, mensajes de log, cadenas de texto de interfaz. Todo en español, tanto en Python como en Rust. Es una decisión consciente de la autora y no se negocia.

### Sistema de ANCLAJES obligatorio
Todo bloque de código que pueda necesitar reemplazarse en el futuro debe delimitarse con comentarios de anclaje:

```python
# ANCLAJE_INICIO: NOMBRE_DEL_BLOQUE
# ... código ...
# ANCLAJE_FIN: NOMBRE_DEL_BLOQUE
```

Cuando entregues código nuevo, indica siempre qué bloque ANCLAJE reemplaza. Nunca entregues un archivo entero sin contexto. Si el bloque es nuevo, ponle nombre descriptivo en mayúsculas con guiones bajos.

Anclajes existentes:

| Anclaje | Archivo |
|---|---|
| `capturador_yin` | `app/motor_audio.py` |
| `generador_tonos` | `app/motor_audio.py` |
| `api_nvda` | `app/conector_nvda.py` |
| `ventana_principal` | `app/interfaz/ventana_principal.py` |

### Cambios quirúrgicos
Nunca reescribas un archivo completo si solo hay que modificar un bloque. Entrega únicamente el bloque ANCLAJE afectado y el contexto mínimo necesario para ubicarlo. Menos tokens, menos riesgo de romper lo que ya funciona.

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Interfaz | wxPython 4.2+ (controles nativos Windows, accesibles por defecto) |
| Lenguaje principal | Python 3.12+ |
| Captura de audio y DSP (opcional, preferente) | Rust + `cpal` + YIN propio, compilado como extensión nativa vía PyO3 (`motor_rust/`) |
| Captura de audio y DSP (respaldo) | `sounddevice` + `numpy`, YIN propio en Python puro |
| Anuncios de interfaz para NVDA/JAWS/Narrador | `accessible_output3` (`app/conector_nvda.py`) — habla directo al lector de pantalla activo |
| Generación de tono de referencia | `numpy` (onda senoidal con envolvente) + `sounddevice.play` |

No añadas dependencias sin justificación explícita. Cada librería nueva es un punto de rotura potencial en la portabilidad.

### Arquitectura híbrida Python/Rust

`app/motor_audio.py` expone una única clase pública, `CapturadorYIN`, que actúa de despachador:

- Si el módulo compilado `motor_rust` está instalado en el entorno, delega en `motor_rust.CapturadorYinRust` (captura con `cpal`, YIN en Rust). Se prefiere por su menor latencia y acceso más directo al dispositivo (WASAPI en Windows), evitando imprecisiones conocidas de `sounddevice`/PortAudio con interfaces externas.
- Si no está instalado, recae de forma transparente en `_CapturadorYINPuroPython` (implementación 100% Python con `sounddevice`), con la misma interfaz pública (`iniciar`, `detener`, `pausar`, `reanudar`).

**Nunca** debe romperse esta compatibilidad de interfaz: cualquier cambio en un backend tiene que reflejarse en el otro, o al menos no cambiar la forma en que `app/interfaz/ventana_principal.py` los consume. La conversión de frecuencia a nota (`frecuencia_a_nota`), el cálculo de instrucción de afinación (`calcular_instruccion`) y toda la lógica de UI/NVDA se quedan siempre en Python — Rust solo se encarga de la captura y el DSP en tiempo real.

La extensión Rust se compila con `maturin` (ver `motor_rust/pyproject.toml` y el README). El binario compilado (`.pyd`/`.so`) nunca se commitea; cada máquina lo compila una vez.

---

## Estructura de archivos

```
app/
├── motor_audio.py     # CapturadorYIN (despachador Rust/Python), _CapturadorYINPuroPython
│                       # (respaldo), YIN en Python puro, GeneradorTonos, conversión nota↔frecuencia
├── conector_nvda.py    # AnunciadorNVDA: accessible_output3 + throttling por estabilidad (350 ms)
├── interfaz_gui.py     # Compatibilidad temporal: reexporta VentanaPrincipal desde interfaz/
├── interfaz/
│   └── ventana_principal.py  # VentanaPrincipal: wx.Frame raíz, pestañas, flujo de captura
├── presets_instrumento.py  # PRESETS_INSTRUMENTO, ESCALAS_POR_INSTRUMENTO (sin wx, para pruebas)
├── afinaciones_maqam_lira.py  # Catálogo de maqamat de la lira, sin wx
├── perfiles_afinacion.py  # Perfiles de afinación guardados por instrumento
├── gestor_atajos.py     # Atajos de teclado configurables: defaults + overrides de usuario
├── gestor_ajustes.py    # cargar_ajustes()/guardar_ajustes(): persistencia atómica en
│                        # configuraciones/ajustes.json
├── control_microfono.py # asegurar_microfono_activo(): desmute opcional a nivel de
│                        # Windows con pycaw, solo con consentimiento de la usuaria
└── config_rutas.py      # RAIZ, RUTA_CONFIGURACIONES, RUTA_AJUSTES (rutas absolutas)
motor_rust/
├── Cargo.toml
├── pyproject.toml       # Configuración de maturin
└── src/lib.rs           # listar_dispositivos_entrada(), CapturadorYinRust (cpal + YIN)
tests/
├── test_motor_audio.py  # YIN contra cuerdas pulsadas sintéticas (armónicos + ruido), conversión
│                          # de notas, cálculo de instrucción
├── test_maqamat.py      # Coherencia musical de las afinaciones de lira (sin cuerdas duplicadas,
│                          # cada maqam coincide con sus siete grados de referencia)
├── test_perfiles_afinacion.py  # Separación de perfiles por instrumento y migración de los antiguos
├── test_gestor_ajustes.py      # Migración y copias rotativas de ajustes
└── test_gestor_atajos.py       # Fusión de defaults y overrides de atajos de teclado
iniciar_afinador.py        # Punto de entrada, configura logging a afinador.log
requisitos.txt             # Dependencias de Python
INICIAR_AFINADOR.bat        # Lanzador para Windows
INSTALAR_AFINADOR.bat       # Instalador de dependencias y compilación opcional de Rust
```

---

## Instrumentos y afinaciones estándar

Los presets viven en `PRESETS_INSTRUMENTO` (`app/presets_instrumento.py`), como listas de `(nombre_cuerda, indice_nota, octava)`. `indice_nota` usa `NOMBRES_NOTAS` de `motor_audio.py` (0=Do, 1=Do#, 2=Re, 3=Re#, 4=Mi, 5=Fa, 6=Fa#, 7=Sol, 8=Sol#, 9=La, 10=La#, 11=Si). La octava sigue la notación científica con La4=440 Hz como referencia.

| Instrumento | Afinación |
|---|---|
| Cromático | Sin cuerda objetivo: detecta la nota cromática más cercana a lo que suene |
| Lira de 16 cuerdas (Aklot) | Diatónica en Do mayor, Sol3 → La5 (16 notas: Sol3 La3 Si3 Do4 Re4 Mi4 Fa4 Sol4 La4 Si4 Do5 Re5 Mi5 Fa5 Sol5 La5) |
| Ukelele | Sol4, Do4, Mi4, La4 (GCEA reentrante, soprano/concierto estándar) |
| Guitarra | Mi2, La2, Re3, Sol3, Si3, Mi4 (EADGBE estándar) |

Si se añade un instrumento nuevo, verificar su afinación estándar real (no asumir) antes de codificar el preset — ya ha pasado que el valor por defecto asumido para la lira no coincidía con el modelo real de la usuaria (Aklot arranca en Sol3, no en Do3).

### Retoque fino por cuerda (cuartos de tono) y escalas/afinaciones alternativas

Cada cuerda puede desplazarse de su nota de fábrica en pasos de cuarto de tono (50 cents,
`CENTS_POR_CUARTO_TONO` en `motor_audio.py`), guardado en `self.ajustes_finos_cuerdas`
(`VentanaPrincipal`) con clave `"{instrumento}||{nombre_cuerda}"` y persistido en
`ajustes.json`. `frecuencia_con_desplazamiento(indice_nota, octava, cuartos_tono)` es la
única función que debe calcular la frecuencia real de una cuerda — tanto la instrucción de
afinación (`_actualizar_deteccion`) como el tono de referencia (`_al_reproducir_referencia`)
pasan siempre por `_frecuencia_objetivo_actual()`, que lee ese mismo desplazamiento. Nunca
dupliques el cálculo de frecuencia objetivo en un sitio nuevo sin pasar por ahí, o divergirán
entre lo que suena y lo que se compara.

`ESCALAS_POR_INSTRUMENTO` (`app/presets_instrumento.py`) define, por instrumento, diccionarios de
`nombre_cuerda → cuartos_tono` que se aplican de golpe sobre `ajustes_finos_cuerdas` al
cambiar el selector "Escala / afinación" (`_al_cambiar_escala`): incluye los maqams árabes
de la lira (Rast, Bayati, Hijaz, verificados contra Touma, "The Music of the Arabs") y
afinaciones alternativas de guitarra y ukelele. Un cuarto de tono (50 cents) es una
diferencia real pero sutil al oído en un tono aislado — no asumas que "suena igual" significa
que el retoque no se aplicó; usa la reproducción de la afinación completa o la
confirmación por voz de la referencia (ver más abajo) para verificarlo objetivamente en
vez de fiarte del oído.

---

## Reglas críticas de arquitectura

### Rutas: siempre absolutas
Nunca uses rutas relativas para archivos de configuración persistente. Usa siempre `RAIZ` de `config_rutas.py` como base:

```python
from app.config_rutas import RUTA_AJUSTES
```

`iniciar_afinador.py` resuelve la ruta del log de forma independiente, con `os.path.dirname(os.path.abspath(__file__))`, porque vive en la raíz del proyecto y no depende de `app/`.

### Ajustes: persistencia atómica
`app/gestor_ajustes.py` guarda `configuraciones/ajustes.json` escribiendo primero a un archivo temporal y renombrando después sobre el destino (evita corrupción si la app se cierra a medias). El dispositivo de entrada se persiste por **nombre**, nunca por índice — los índices de PortAudio/cpal pueden cambiar entre sesiones al conectar o desconectar hardware. `configuraciones/` está en `.gitignore`: es estado local del usuario, no se commitea.

### Hilos: wxPython no es thread-safe
Toda actualización de UI ocurre en el hilo principal. La captura de audio corre siempre en hilos secundarios (nativos de Rust vía `cpal`, o `threading.Thread` en el respaldo Python), y notifica a la GUI exclusivamente a través de `wx.CallAfter`:

```python
def _al_detectar_tono(self, resultado, rms):
    wx.CallAfter(self._actualizar_deteccion, resultado, rms)
```

No actualices controles wx directamente desde el hilo de audio ni desde el callback que llega del backend Rust. Produce crashes impredecibles con NVDA activo.

### Diagnóstico de nivel de entrada: nunca fallar en silencio
El `rms` llega en todos los callbacks de detección, aunque no haya nota detectada (por debajo del umbral). `VentanaPrincipal` lo usa para mantener visible el nivel de entrada en todo momento y para avisar por voz si tras `SEGUNDOS_ESPERA_DIAGNOSTICO_SENAL` no se ha detectado ninguna señal real — porque para una usuaria ciega, una app que "no dice nada" es indistinguible de una app rota. Cualquier función nueva de captura debe seguir exponiendo el nivel de señal en vez de limitarse a silenciar cuando no hay nota.

### Retroalimentación acústica: pausar la captura al reproducir tonos
`GeneradorTonos.reproducir()` siempre pausa el capturador activo (`capturador.pausar()`) antes de reproducir y lo reanuda (`capturador.reanudar()`) al terminar, para que el algoritmo no confunda el altavoz con la cuerda. Cualquier nueva vía de reproducción de audio debe respetar este mismo patrón. Las frecuencias graves (por debajo de 200 Hz) reciben además una compensación de amplitud en `GeneradorTonos._compensar_percepcion_grave()`, porque a igual amplitud se perciben más flojas y los altavoces pequeños las reproducen peor.

### Anuncios por voz: throttling obligatorio, y un solo canal de voz
Ninguna instrucción de afinación se anuncia por voz de forma inmediata. `AnunciadorNVDA.procesar_instruccion()` exige que el mensaje lleve estable un mínimo de 350 ms y que difiera del último ya pronunciado. No llames a `AnunciadorNVDA.hablar()` directamente desde el bucle de detección de tono — pasa siempre por `procesar_instruccion()`, o la app satura la cola de voz del lector de pantalla en cuanto la señal esté un poco inestable. Además, cualquier otro anuncio (diagnóstico, confirmaciones) comparte el mismo canal de voz que las instrucciones de afinación, y la mayoría de lectores de pantalla cortan lo que se está diciendo en cuanto llega un texto nuevo — un anuncio secundario que se repite con frecuencia (como el nivel de entrada) puede cortar a medias la instrucción real antes de que la usuaria la oiga completa. Los anuncios que no sean la instrucción de afinación deben ser puntuales (una sola vez por evento), nunca una narración continua.

Por la misma razón, `_al_reproducir_referencia` anuncia con `hablar()` (evento puntual, no
`procesar_instruccion()`) si el tono que va a sonar lleva retoque aplicado y cuántos cents,
antes de reproducirlo — un cuarto de tono es una diferencia real pero difícil de distinguir
de oído en una nota aislada, así que la app confirma por voz en vez de dejar que la usuaria
dude de si el retoque se aplicó de verdad.

### Micrófonos con cancelación de ruido por IA
Los portátiles con reducción de ruido inteligente en el micrófono (Lenovo Vantage y similares) están entrenados para reconocer voz humana y suelen filtrar el sonido de instrumentos acústicos como si fuera ruido de fondo. Documentado en el README: hay que desactivar esa función para poder usar el afinador con el micrófono integrado.

### Atajos de teclado configurables: nunca la tecla Espacio
Ocho atajos son configurables vía `app/gestor_atajos.py` (mismo patrón que Epub TTS
Accesible: `teclas_predeterminadas.json` con los valores de fábrica, nunca tocado a mano,
y `teclas_usuario.json` solo con los overrides — se fusionan al cargar con `cargar_atajos()`).
`VentanaPrincipal._configurar_aceleradores_globales()` reconstruye la `wx.AcceleratorTable`
del `wx.Frame` a partir de ese diccionario en cada arranque y cada vez que se reasigna, quita
o restablece un atajo desde `_DialogoAtajos` (botón "Personalizar atajos de teclado..." en
Audio y ajustes) — nunca hace falta reiniciar la app para que un cambio surta efecto.
`NOMBRES_METODO_ATAJO` mapea cada clave del JSON al nombre del método que la ejecuta
(resuelto con `getattr` en tiempo de ejecución, no una tabla de `wx.NewIdRef()` fija).

| Clave (gestor_atajos) | Atajo de fábrica | Acción |
|---|---|---|
| `reproducir_referencia` | `Ctrl+P` | Reproducir el tono de referencia de la cuerda/nota seleccionada |
| `alternar_escucha` | `Ctrl+E` | Iniciar/detener la escucha del micrófono |
| `subir_cuarto_tono` / `bajar_cuarto_tono` | `Ctrl+Mayús+Flecha arriba/abajo` | Retocar la cuerda seleccionada en cuartos de tono |
| `restablecer_ajuste_fino` | `Ctrl+Mayús+R` | Restablecer el retoque de la cuerda seleccionada |
| `deshacer_retoque` | `Ctrl+Mayús+Z` | Deshacer el último retoque en cuartos de tono (cualquier cuerda, vía `self._historial_retoques`) |
| `escucha_previa_escala` | `Ctrl+Mayús+P` | Reproducir la afinación completa activa, todas las cuerdas seguidas (`GeneradorTonos.reproducir_secuencia`) |
| `repetir_instruccion` | `Ctrl+Mayús+V` | Repetir la última instrucción de afinación anunciada |

`F1`, `Ctrl+1/2/3` y la tecla Menú/Mayús+F10 quedan **fuera** de `gestor_atajos.py`: se
despachan por su propio manejador de teclado (`_al_navegacion_con_tab`, `EVT_CONTEXT_MENU`)
y no compiten por la misma tecla que los ocho de arriba, así que no hace falta que sean
reasignables — reasignarlos rompería convenciones fijadas en toda la app (F1 es "ayuda" en
todos lados; Ctrl+1/2/3 es "cambiar de pestaña").

`_DialogoCapturaTecla` (la ventana modal que espera la pulsación al reasignar) impide
explícitamente asignar `Espacio` solo, sin modificador: es la tecla con la que NVDA activa
controles con foco, y un atajo global ahí compite con eso. Si se añade un atajo nuevo,
añadirlo también a `_DEFAULTS_EMBEBIDOS` (`gestor_atajos.py`) y a `NOMBRES_METODO_ATAJO`
(`ventana_principal.py`) — nunca lo dupliques en un panel hijo aparte de la tabla central del
frame, o la ambigüedad puede disparar el manejador equivocado.

### Menú contextual (siguiendo el patrón de Epub TTS Accesible)
`_al_menu_contextual` (bindado a `wx.EVT_CONTEXT_MENU` en el frame: clic derecho, tecla
Menú o Mayús+F10, desde cualquier pestaña) abre un único menú — a diferencia de Epub TTS,
que tiene un menú distinto por pestaña porque cada una opera sobre un tipo de elemento
distinto (libro, fragmento...). El afinador no tiene esa variedad de contenido por pestaña,
así que un solo menú global basta: ayuda, ver atajos, visitar tiflotutos.com, y las tres
acciones sobre `registros/` (abrir la carpeta, copiar el log completo o solo el último
error al portapapeles) — mismos nombres y comportamiento que en Epub TTS, para quien ya
conoce esa app. "Ver atajos de teclado" lee `cargar_atajos()` en vivo (ya no es una lista
estática): si se añade o cambia un atajo en `gestor_atajos.py`, este ítem se actualiza solo.

### Modo identificación de nota
La casilla `casilla_modo_solo_escucha` (etiqueta visible "Modo identificación de nota";
persistida internamente como `modo_solo_escucha` en `ajustes.json` — nombre interno sin
cambiar a propósito, es solo una clave de JSON) hace que `_actualizar_deteccion` anuncie
solo la nota detectada (p. ej. "Sol3"), sin calcular ni pronunciar instrucción de sube/baja
ni disparar la confirmación/avance automático — para identificar por oído lo que suena en
vez de afinar hacia un objetivo. Sigue siendo un modo de la escucha del micrófono (`Ctrl+E`),
no una función independiente — el nombre visible se cambió porque "modo solo escucha"
competía con el propio significado de "escucha" (encender el micrófono) y con "reproducir la
afinación completa" (que también se llamaba "escucha previa"). Si se toca esta función,
mantener el `return` temprano que evita ejecutar el resto de la lógica de afinación con la
casilla activa, o volverán a sonar instrucciones que el modo promete no dar.

### Detección automática de cuerda
`casilla_deteccion_automatica_cuerda` (persistida como `deteccion_automatica_cuerda`), opt-in
y desactivada por defecto. `_detectar_cuerda_automaticamente()`, llamada desde
`_actualizar_deteccion` justo después del filtro de mediana, compara la frecuencia detectada
contra la frecuencia real (con retoque) de cada cuerda del preset activo y selecciona la más
cercana con `selector_cuerda.SetSelection()` — que **no** dispara `EVT_CHOICE`, así que el
propio método reproduce a mano el reinicio de estado que haría `_al_cambiar_cuerda`. Solo
cambia de cuerda si la diferencia es menor a `MARGEN_CENTS_DETECCION_AUTOMATICA` (55 cents),
para no saltar de cuerda con ruido o armónicos ambiguos entre cuerdas adyacentes.

### Reproducir la afinación completa (antes "escucha previa")
`_al_escucha_previa_escala` (botón "Reproducir la afinación completa", `Ctrl+Mayús+P`) reproduce
una sola vez cada cuerda de la afinación activa, en su frecuencia objetivo final (de fábrica
más el retoque de escala/manual ya aplicado), de la más grave a la más aguda, vía
`reproducir_secuencia()`. En las cuerdas que llevan retoque (`cuartos_tono` distinto de cero
en `retoques_escala_activa` + `ajustes_finos_cuerdas`), reproduce primero la nota de fábrica y
justo después la retocada (comparación A/B) — un cuarto de tono es una diferencia real pero
difícil de distinguir en una nota aislada, y el contraste directo la hace audible sin depender
de recordar cómo sonaba la cuerda anterior. Las cuerdas sin retoque suenan una sola vez.

### Nivel de detalle de las instrucciones
`selector_verbosidad` (persistido como `instrucciones_detalladas`) tiene dos modos: conciso
(el texto de `TEXTOS_INSTRUCCION` tal cual) y detallado, que le añade los cents exactos con
`.format()` después de traducir/construir el texto base — nunca antes, para no romper el
diccionario `TEXTOS_INSTRUCCION` con cadenas dinámicas.

### Errores: nunca silenciosos
Prohibido `except: pass` o `except Exception: pass` sin logging. Mínimo:
```python
logger.exception("contexto descriptivo del error")
```
En Rust, equivalente: nunca ignorar un `Result` de error con `let _ =` en una ruta donde el fallo deba ser visible — usar como mínimo `eprintln!` (ver `err_fn` y los brazos `Err` en `motor_rust/src/lib.rs`) o propagar el error a Python con `PyResult`.

---

## Pruebas

`tests/test_motor_audio.py` valida YIN contra señales sintéticas que simulan cuerdas pulsadas reales (fundamental + armónicos con amplitud decreciente, envolvente de decaimiento, ruido de fondo) — no senoidales puras, porque ahí es donde un YIN mal implementado sufre saltos de octava. Se ejecutan con:

```
python -m unittest discover -s tests -v
```

Si se toca `estimar_frecuencia_yin` (Python) o su equivalente en Rust (`motor_rust/src/lib.rs`), correr estas pruebas antes de dar el cambio por terminado. No añadir pruebas que dependan de hardware de audio real ni de wxPython — deben poder correr en cualquier máquina, incluida una sin pantalla ni micrófono.

---

## Accesibilidad NVDA: checklist obligatorio

Antes de dar cualquier cambio de interfaz por terminado, verificar:

1. ¿El foco llega a donde debe al cambiar de control?
2. ¿Las casillas y controles anuncian su estado al navegar con flechas?
3. ¿Las instrucciones de afinación se anuncian sin saturar la cola de voz (ver throttling arriba)?
4. ¿El pitido de confirmación ("AFINADA") suena una sola vez por acierto, no en bucle mientras la nota se mantiene afinada?
5. ¿Los atajos nuevos evitan la tecla Espacio y están centralizados en la tabla de aceleradores del frame?

Si algo de esto falla tras un cambio, es un bug crítico, no cosmético.

---

## Lo que no hacer (resumen)

- No mezcles inglés en nombres, comentarios, logs o cadenas de interfaz.
- No actualices la UI desde hilos secundarios ni desde callbacks de Rust sin `wx.CallAfter`.
- No reproduzcas audio de referencia sin pausar antes la captura activa.
- No hables por NVDA sin pasar por el throttling de `AnunciadorNVDA.procesar_instruccion()`.
- No uses `except: pass` sin logging, ni su equivalente silencioso en Rust.
- No asumas la afinación estándar de un instrumento nuevo sin verificarla.
- No rompas la paridad de interfaz entre el backend Rust y el respaldo Python de `CapturadorYIN`.
- No uses la tecla `Espacio` como atajo de teclado.
- No persistas el dispositivo de audio por índice; guarda siempre su nombre.
- No commitees binarios compilados de la extensión Rust (`.pyd`, `.so`, `target/`).
- No incluyas ninguna referencia a conversaciones, sesiones de IA ni proceso de desarrollo en el código ni en los comentarios.
