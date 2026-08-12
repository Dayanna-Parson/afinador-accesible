# AfinadorAccesible

Afinador cromático de escritorio para Windows, accesible por diseño para personas ciegas usuarias de NVDA, JAWS o Narrador.

## Requisitos

- Python 3.12+
- Windows (para la integración con lectores de pantalla vía `accessible_output3`)

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

## Estructura

```
app/
├── motor_audio.py     # Captura de audio (dispatcher Rust/Python), algoritmo YIN de respaldo,
│                       # generador de tonos de referencia
├── conector_nvda.py   # Salida de voz al lector de pantalla activo, con throttling por estabilidad
└── interfaz_gui.py    # Ventana principal wxPython
motor_rust/             # Extensión nativa opcional: captura de audio (cpal) + YIN, vía PyO3
iniciar_afinador.py     # Punto de entrada
requisitos.txt          # Dependencias de Python
INICIAR_AFINADOR.bat    # Lanzador para Windows
```

## Instrumentos soportados

- Cromático (cualquier nota)
- Lira de 16 cuerdas (Aklot): diatónica en Do mayor, Sol3 a La5
- Ukelele: Sol4, Do4, Mi4, La4 (GCEA reentrante estándar)
- Guitarra: Mi2, La2, Re3, Sol3, Si3, Mi4 (afinación estándar)
