# AfinadorAccesible

Afinador cromático de escritorio para Windows, accesible por diseño para personas ciegas usuarias de NVDA, JAWS o Narrador.

## Requisitos

- Python 3.12+
- Windows (para la integración con lectores de pantalla vía `accessible_output3`)

### Ajuste imprescindible en portátiles con reducción de ruido por IA

Si el portátil tiene una función de "Cancelación de ruido del micrófono" (Lenovo Vantage,
Dolby, o similar), **desactívala** para usar el afinador. Estas funciones están entrenadas
para reconocer voz humana y suelen filtrar o atenuar fuertemente el sonido de instrumentos
acústicos, tratándolo como "ruido de fondo". En Lenovo Vantage: Sonido → Entrada →
Cancelación de ruido del micrófono → **Desactivado** (en vez de "Normal" o "Varias voces").

## Instalación

```
git clone https://github.com/Dayanna-Parson/afinador-accesible.git
cd afinador-accesible
pip install -r requisitos.txt
python iniciar_afinador.py
```

En Windows también puedes ejecutar `INICIAR_AFINADOR.bat` una vez instalados los requisitos.

### Extensión nativa opcional (Rust)

La captura de audio y el algoritmo YIN tienen una implementación alternativa en Rust
(`motor_rust/`, con `cpal` en vez de `sounddevice`), pensada para menor latencia y acceso
más directo al dispositivo (WASAPI en Windows). Es opcional: si no está compilada, la app
usa automáticamente la implementación en Python puro con la misma interfaz.

Para compilarla e instalarla en el entorno activo:

```
pip install maturin
cd motor_rust
maturin develop --release
```

En Windows hace falta el toolchain de Rust (`rustup`) y Visual Studio Build Tools (C++).

## Ejecución

```
python iniciar_afinador.py
```

## Atajos de teclado

- `Ctrl+P`: reproducir el tono de referencia de la cuerda/nota seleccionada.
- `Ctrl+E`: iniciar o detener la escucha del micrófono.

## Ajustes persistentes

El dispositivo de entrada, la tasa de muestreo, el tamaño de búfer, el instrumento y la
cuerda seleccionados se guardan automáticamente en `configuraciones/ajustes.json` y se
restauran al volver a abrir la aplicación.

## Diagnóstico de nivel de entrada

La etiqueta "Nivel de entrada" muestra en vivo el volumen (RMS) que está captando el
micrófono, para comprobar visualmente si hay señal. Si tras iniciar la escucha no se
detecta ninguna señal en unos segundos, la app lo anuncia por voz (puede indicar que el
dispositivo seleccionado no es el correcto, o que está silenciado a nivel de Windows).

En Windows, al iniciar la escucha también se comprueba automáticamente si el micrófono
seleccionado está silenciado a nivel de sistema y, si lo está, se desmutea solo (requiere
`pycaw`, instalado por defecto en Windows vía `requisitos.txt`).

## Avance automático de cuerda

Al mantener la afinación correcta ("AFINADA") de forma estable durante poco más de un
segundo, el selector de cuerda avanza automáticamente a la siguiente de la lista (no
aplica en modo Cromático, que no tiene una secuencia de cuerdas).

## Pruebas

```
python -m unittest discover -s tests -v
```

## Estructura

```
app/
├── motor_audio.py     # Captura de audio (dispatcher Rust/Python), algoritmo YIN de respaldo,
│                       # generador de tonos de referencia
├── conector_nvda.py   # Salida de voz al lector de pantalla activo, con throttling por estabilidad
├── interfaz_gui.py    # Ventana principal wxPython
├── gestor_ajustes.py  # Persistencia atómica de ajustes en configuraciones/ajustes.json
├── control_microfono.py  # Desmute automático del micrófono a nivel de Windows (pycaw)
└── config_rutas.py    # Rutas absolutas del proyecto
motor_rust/             # Extensión nativa opcional: captura de audio (cpal) + YIN, vía PyO3
tests/                  # Pruebas del algoritmo YIN y la lógica de notas/instrucciones
iniciar_afinador.py     # Punto de entrada
requisitos.txt          # Dependencias de Python
INICIAR_AFINADOR.bat    # Lanzador para Windows
```

## Instrumentos soportados

- Cromático (cualquier nota)
- Lira de 16 cuerdas (Aklot): diatónica en Do mayor, Sol3 a La5
- Ukelele: Sol4, Do4, Mi4, La4 (GCEA reentrante estándar)
- Guitarra: Mi2, La2, Re3, Sol3, Si3, Mi4 (afinación estándar)
