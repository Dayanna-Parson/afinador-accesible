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
- `Ctrl+Mayús+Flecha arriba` / `Ctrl+Mayús+Flecha abajo`: retocar la cuerda seleccionada en
  cuartos de tono (50 cents cada uno; dos cuartos de tono = un semitono).
- `Ctrl+Mayús+R`: restablecer el retoque de la cuerda seleccionada.
- `Ctrl+Mayús+Z`: deshacer el último retoque en cuartos de tono (sobre cualquier cuerda, no
  solo la seleccionada).
- `Ctrl+Mayús+P`: escucha previa de toda la escala/afinación activa, cuerda por cuerda en
  orden, con los retoques aplicados (comparación A/B en las cuerdas retocadas).

## Retoque fino por cuerda (cuartos de tono)

Cada cuerda puede desplazarse de su nota diatónica de fábrica en pasos de cuarto de tono
(50 cents), independientemente de las demás. Dos usos:

- **Sostenidos y bemoles fuera de la escala diatónica**: la lira de 16 cuerdas no tiene
  sostenidos ni bemoles de fábrica; con dos cuartos de tono (un semitono) se puede subir o
  bajar cualquier cuerda a la nota que haga falta.
- **Cuartos de tono árabes (maqam)**: con un solo cuarto de tono se afina exactamente a
  medio camino entre dos semitonos occidentales, como en la música árabe-egipcia.

El retoque se guarda por cuerda (y se recuerda entre sesiones) hasta que se restablece con
`Ctrl+Mayús+R`. Tanto la instrucción de afinación como el tono de referencia (`Ctrl+P`)
tienen en cuenta el retoque activo.

## Escalas y afinaciones alternativas

El selector "Escala / afinación" cambia de opciones según el instrumento activo y aplica
de golpe los retoques correspondientes sobre la afinación de fábrica.

### Lira: maqam árabe (cuartos de tono)

- **Maqam Rast (sobre Sol)**: la cuerda de Si baja medio tono y la de Fa sube medio tono
  (cuarto de tono cada una), en todas las octavas.
- **Maqam Bayati (sobre Re)**: la cuerda de Si baja un semitono completo y la de Mi baja
  medio tono.
- **Maqam Hijaz (sobre Re)**: la cuerda de Si baja un semitono, la de Mi baja un semitono
  y la de Fa sube un semitono (el característico segundo aumentado del maqam).

Patrones verificados contra la teoría estándar de intervalos en cuartos de tono.

### Guitarra: afinaciones alternativas estándar

Drop D, Open G, Open D y DADGAD — todas verificadas nota por nota contra sus afinaciones
de referencia reales.

### Ukelele: afinaciones alternativas estándar

Sol grave (Low G, sin reentrancia, la cuerda de Sol baja una octava en vez de ser la más
aguda) y la afinación Re tradicional (todas las cuerdas un tono entero por encima de la
afinación estándar, común en partituras hawaianas antiguas).

En instrumentos con trastes (guitarra, ukelele) estas afinaciones solo desplazan la cuerda
al aire entera: los trastes siguen fijos en semitonos occidentales, así que no dan acceso a
cuartos de tono nuevos en el mástil — para maqam en esos instrumentos hace falta afinar a
una de estas disposiciones y luego doblar la cuerda (bending) por oído.

Cada retoque aplicado por una escala se puede seguir ajustando a mano con
`Ctrl+Mayús+Flecha arriba/abajo` si el oído dice otra cosa.

## Escucha previa de la escala

`Ctrl+Mayús+P` reproduce, una sola vez y en orden, el tono de referencia de cada cuerda de
la afinación activa (con sus retoques ya aplicados), para saber de antemano cómo debería
sonar el instrumento completo antes de afinarlo cuerda por cuerda. Como la mayoría de
escalas y maqams solo modifican unas pocas cuerdas respecto a la afinación de fábrica, es la
forma más clara de notar cuáles cambian y cuáles no. Se puede interrumpir a mitad con
`Ctrl+E` (detiene también la captura del micrófono) o volviendo a pulsar `Ctrl+Mayús+P`.

En las cuerdas que llevan retoque, la escucha previa reproduce primero la nota de fábrica y
justo después la retocada (comparación A/B), porque un cuarto de tono es una diferencia
sutil que se nota mucho mejor por contraste directo que recordando cómo sonaba antes.

## Modo solo escucha

La casilla "Modo solo escucha" desactiva las instrucciones de sube/baja y el pitido de
confirmación: la app solo dice la nota que detecta en cada momento (por ejemplo "Sol3"),
sin compararla con ninguna cuerda objetivo. Útil para identificar por oído qué se está
tocando en vez de afinar hacia una nota concreta.

## Detección automática de cuerda

La casilla "Detectar automáticamente qué cuerda suena" compara la nota detectada contra
todas las cuerdas de la afinación activa (con sus retoques) y selecciona sola la más
cercana, anunciando "Cuerda detectada: ...". Así no hace falta navegar el selector de cuerda
a mano antes de tocar cada una; solo cambia de cuerda seleccionada si la coincidencia es
razonablemente cercana (55 cents), para no saltar con ruido o armónicos ambiguos.

## Nivel de detalle de las instrucciones

El selector "Nivel de detalle de las instrucciones" tiene dos opciones: "Conciso" (la
instrucción sola, p. ej. "Sube un poco") y "Detallado", que añade los cents exactos de
desviación (p. ej. "Sube un poco (+18 cents)").

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
