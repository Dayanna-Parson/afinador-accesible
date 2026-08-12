# AfinadorAccesible

Afinador cromático de escritorio para Windows, accesible por diseño para personas ciegas usuarias de NVDA, JAWS o Narrador.

## Requisitos

- Python 3.12+
- Windows (para la integración con lectores de pantalla vía `accessible_output3`)

## Instalación

```
pip install -r requirements.txt
```

## Ejecución

```
python iniciar_afinador.py
```

## Estructura

```
app/
├── motor_audio.py     # Captura de audio, algoritmo YIN, generador de tonos de referencia
├── conector_nvda.py   # Salida de voz al lector de pantalla activo, con throttling por estabilidad
└── interfaz_gui.py    # Ventana principal wxPython
iniciar_afinador.py     # Punto de entrada
```

## Instrumentos soportados

- Cromático (cualquier nota)
- Lira de 16 cuerdas (afinación diatónica por defecto, editable)
- Ukelele (afinación reentrante estándar)
- Guitarra (afinación estándar de 6 cuerdas)
