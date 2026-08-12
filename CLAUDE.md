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
| `ventana_principal` | `app/interfaz_gui.py` |

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

**Nunca** debe romperse esta compatibilidad de interfaz: cualquier cambio en un backend tiene que reflejarse en el otro, o al menos no cambiar la forma en que `interfaz_gui.py` los consume. La conversión de frecuencia a nota (`frecuencia_a_nota`), el cálculo de instrucción de afinación (`calcular_instruccion`) y toda la lógica de UI/NVDA se quedan siempre en Python — Rust solo se encarga de la captura y el DSP en tiempo real.

La extensión Rust se compila con `maturin` (ver `motor_rust/pyproject.toml` y el README). El binario compilado (`.pyd`/`.so`) nunca se commitea; cada máquina lo compila una vez.

---

## Estructura de archivos

```
app/
├── motor_audio.py     # CapturadorYIN (despachador Rust/Python), _CapturadorYINPuroPython
│                       # (respaldo), YIN en Python puro, GeneradorTonos, conversión nota↔frecuencia
├── conector_nvda.py    # AnunciadorNVDA: accessible_output3 + throttling por estabilidad (350 ms)
├── interfaz_gui.py     # VentanaPrincipal: wx.Frame raíz, presets de instrumento, flujo de captura
├── gestor_ajustes.py    # cargar_ajustes()/guardar_ajustes(): persistencia atómica en
│                        # configuraciones/ajustes.json
└── config_rutas.py      # RAIZ, RUTA_CONFIGURACIONES, RUTA_AJUSTES (rutas absolutas)
motor_rust/
├── Cargo.toml
├── pyproject.toml       # Configuración de maturin
└── src/lib.rs           # listar_dispositivos_entrada(), CapturadorYinRust (cpal + YIN)
tests/
└── test_motor_audio.py  # YIN contra cuerdas pulsadas sintéticas (armónicos + ruido), conversión
│                          # de notas, cálculo de instrucción
iniciar_afinador.py        # Punto de entrada, configura logging a afinador.log
requisitos.txt             # Dependencias de Python
INICIAR_AFINADOR.bat        # Lanzador para Windows
```

---

## Instrumentos y afinaciones estándar

Los presets viven en `PRESETS_INSTRUMENTO` (`app/interfaz_gui.py`), como listas de `(nombre_cuerda, indice_nota, octava)`. `indice_nota` usa `NOMBRES_NOTAS` de `motor_audio.py` (0=Do, 1=Do#, 2=Re, 3=Re#, 4=Mi, 5=Fa, 6=Fa#, 7=Sol, 8=Sol#, 9=La, 10=La#, 11=Si). La octava sigue la notación científica con La4=440 Hz como referencia.

| Instrumento | Afinación |
|---|---|
| Cromático | Sin cuerda objetivo: detecta la nota cromática más cercana a lo que suene |
| Lira de 16 cuerdas (Aklot) | Diatónica en Do mayor, Sol3 → La5 (16 notas: Sol3 La3 Si3 Do4 Re4 Mi4 Fa4 Sol4 La4 Si4 Do5 Re5 Mi5 Fa5 Sol5 La5) |
| Ukelele | Sol4, Do4, Mi4, La4 (GCEA reentrante, soprano/concierto estándar) |
| Guitarra | Mi2, La2, Re3, Sol3, Si3, Mi4 (EADGBE estándar) |

Si se añade un instrumento nuevo, verificar su afinación estándar real (no asumir) antes de codificar el preset — ya ha pasado que el valor por defecto asumido para la lira no coincidía con el modelo real de la usuaria (Aklot arranca en Sol3, no en Do3).

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
    wx.CallAfter(self._actualizar_deteccion, resultado)
```

No actualices controles wx directamente desde el hilo de audio ni desde el callback que llega del backend Rust. Produce crashes impredecibles con NVDA activo.

### Retroalimentación acústica: pausar la captura al reproducir tonos
`GeneradorTonos.reproducir()` siempre pausa el capturador activo (`capturador.pausar()`) antes de reproducir y lo reanuda (`capturador.reanudar()`) al terminar, para que el algoritmo no confunda el altavoz con la cuerda. Cualquier nueva vía de reproducción de audio debe respetar este mismo patrón.

### Anuncios por voz: throttling obligatorio
Ninguna instrucción de afinación se anuncia por voz de forma inmediata. `AnunciadorNVDA.procesar_instruccion()` exige que el mensaje lleve estable un mínimo de 350 ms y que difiera del último ya pronunciado. No llames a `AnunciadorNVDA.hablar()` directamente desde el bucle de detección de tono — pasa siempre por `procesar_instruccion()`, o la app satura la cola de voz del lector de pantalla en cuanto la señal esté un poco inestable.

### Atajos de teclado: nunca la tecla Espacio
`Ctrl+P` reproduce el tono de referencia y `Ctrl+E` alterna la escucha (`VentanaPrincipal._construir_atajos`, `app/interfaz_gui.py`), declarados en una única `wx.AcceleratorTable` a nivel de `wx.Frame`. Prohibido usar `Espacio` como atajo: es la tecla con la que NVDA activa controles con foco, y un atajo global en Espacio compite con eso. Si se añaden más atajos, mantenerlos todos en la misma tabla central del frame — no dupliques el mismo atajo en un panel hijo y en el frame a la vez, o la ambigüedad puede disparar el manejador equivocado.

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
