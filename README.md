# AfinadorAccesible

Afinador cromático de escritorio para Windows, accesible por diseño para personas ciegas usuarias de NVDA, JAWS o Narrador.

## Requisitos

- Python 3.12+
- Windows (para la integración con lectores de pantalla vía `accessible_output3`)

Las dependencias exactas y sus versiones mínimas están en
[`requisitos.txt`](requisitos.txt). Rust **no** es un requisito para usar la
aplicación: solo sirve para compilar el motor alternativo opcional.

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
Para instalarlo todo de una vez en un entorno propio de la aplicación, ejecuta
`INSTALAR_AFINADOR.bat`. El instalador ofrece compilar el motor opcional de Rust si ya está
instalado el toolchain correspondiente; no es necesario para usar el afinador.

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

## Interfaz y accesibilidad

La ventana tiene un tamaño inicial cómodo sin maximizar y se adapta si se hace
más grande. Las tres pestañas siguen el orden de una sesión normal:

- **Afinar**: instrumento, cuerda, detección, indicaciones y tonos de referencia.
- **Afinaciones especiales**: afinaciones alternativas y la escucha previa.
- **Audio y ajustes**: dispositivo, canal de la Scarlett, WASAPI, nivel de entrada,
  calibración, nombres de notas y opciones menos frecuentes.

Tab y Mayús+Tab recorren únicamente controles utilizables; desde el primer o último
control vuelven al selector de pestañas. Los botones tienen
texto completo; los iconos nativos son un apoyo visual, nunca la única señal. La
carpeta `recursos/sonidos/` está preparada para efectos opcionales que tampoco
sustituirán los anuncios de NVDA, JAWS o Narrador.

## Atajos de teclado

- `F1`: abrir la ayuda local.
- `Ctrl+1`, `Ctrl+2`, `Ctrl+3`: abrir Afinar, Afinaciones especiales o Audio y ajustes.
- `Ctrl+P`: reproducir el tono de referencia de la cuerda/nota seleccionada.
- `Ctrl+E`: iniciar o detener la escucha del micrófono.
- `Ctrl+Mayús+Flecha arriba` / `Ctrl+Mayús+Flecha abajo`: subir o bajar la cuerda seleccionada
  según el tamaño elegido en "Ajuste manual de una cuerda": cuarto de tono, semitono o tono.
- `Ctrl+Mayús+R`: restablecer únicamente el ajuste manual de la cuerda seleccionada; la
  afinación o maqam elegido se conserva.
- `Ctrl+Mayús+Z`: deshacer el último retoque en cuartos de tono (sobre cualquier cuerda, no
  solo la seleccionada).
- `Ctrl+Mayús+P`: escucha previa de toda la afinación objetivo, cuerda por cuerda desde la
  más grave a la más aguda.
- `Ctrl+Mayús+V`: repetir la última instrucción de afinación anunciada.

## Retoque fino por cuerda (cuartos de tono)

Para el mapa técnico, las reglas de accesibilidad y las pruebas, consulta
[DEVELOPMENT.md](DEVELOPMENT.md), [estructura_proyecto.txt](estructura_proyecto.txt) y
[AUDITORIA_EPUB_TTS.md](AUDITORIA_EPUB_TTS.md).

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

El selector "Escala o afinación" cambia de opciones según el instrumento activo y aplica
de golpe los retoques correspondientes sobre la afinación de fábrica.

### Lira: maqam árabe (cuartos de tono)

La lira Aklot conserva una **afinación fija**: cada maqam ajusta sus 16 cuerdas
para contener sus siete grados en varias octavas. La cuerda más grave es Sol,
pero la tónica se indica en el nombre del maqam; por ejemplo, en Bayati sobre Re
la tónica es Re, aunque la escucha previa comience por Sol grave. La app muestra
esta aclaración al elegir el maqam.

Esta adaptación es fiel a los grados de la escala dentro de una aproximación de
24 divisiones por octava. No pretende sustituir la expresividad de un oud sin
trastes, las palancas de un qanun ni las modulaciones que exigirían volver a
afinar cuerdas durante una interpretación.

Para que la lista sea manejable, la pestaña **Afinaciones especiales** permite
elegir primero una familia (Rast, Bayati, Hijaz, Sikah, Saba, Kurd, Nahawand,
Ajam o Nikriz). Después muestra solo esa familia, junto a la afinación de fábrica
y a la personalizada. Sikah incluye sus variantes Huzam, Iraq y Bastanigar.

- **Maqam Rast (sobre Sol)**: la cuerda de Si baja un cuarto de tono y la de Fa sube un
  cuarto de tono, en todas las octavas.
- **Maqam Bayati (sobre Re)**: la cuerda de Si baja un semitono completo y la de Mi baja
  medio tono.
- **Maqam Hijaz (sobre Re)**: la cuerda de Si baja un semitono, la de Mi baja un semitono
  y la de Fa sube un semitono (el característico segundo aumentado del maqam).

Patrones verificados contra la teoría estándar de intervalos en cuartos de tono.

### Guitarra: afinaciones alternativas estándar

Drop D, Open G, Open D y DADGAD — todas bajan o mantienen la tensión de las cuerdas estándar,
por lo que resultan opciones razonables tanto para guitarra acústica como electroclásica.
No se incluyen afinaciones que suben varias cuerdas y pueden aumentar demasiado la tensión.

### Ukelele soprano

Con cuerdas normales, la aplicación mantiene únicamente la afinación estándar Sol–Do–Mi–La.
Low G requiere montar una cuerda específica y la afinación Re requiere un juego preparado para
esa tensión; por seguridad no se muestran como opciones de este instrumento.

En instrumentos con trastes (guitarra, ukelele) estas afinaciones solo desplazan la cuerda
al aire entera: los trastes siguen fijos en semitonos occidentales, así que no dan acceso a
cuartos de tono nuevos en el mástil — para maqam en esos instrumentos hace falta afinar a
una de estas disposiciones y luego doblar la cuerda (bending) por oído.

Cada retoque aplicado por una escala se puede seguir ajustando a mano con
`Ctrl+Mayús+Flecha arriba/abajo` si el oído dice otra cosa.

## Perfiles personales y copia de seguridad

En la pestaña **Afinaciones especiales**, el bloque "Afinaciones personales"
permite guardar la afinación actual con un nombre y recuperarla más tarde. Se
guarda tanto el maqam o afinación base como los retoques manuales de cada cuerda.
Por tanto, puedes crear, por ejemplo, una versión propia de Bayati y volver a
ella sin retocar de nuevo las 16 cuerdas.

Los perfiles se separan por instrumento y se pueden cargar, renombrar o eliminar.
Los presets incluidos nunca se modifican. **Exportar todos los perfiles** guarda una
copia JSON; **Importar perfiles desde copia** añade perfiles nuevos sin sobrescribir
otros que ya existan con el mismo nombre.

## Nombres de notas y aviso de tensión

En **Audio y ajustes** se puede elegir entre Do–Re–Mi y C–D–E. Es solo una preferencia
de presentación y anuncios: los cálculos siguen usando índices cromáticos y frecuencias.
Al intentar subir una cuerda dos semitonos o más sobre su afinación estándar, el afinador
solicita confirmación para evitar una subida accidental de tensión.

## Escucha previa de la escala

`Ctrl+Mayús+P` reproduce, una sola vez y en orden, el tono de referencia de cada cuerda de
la afinación activa (con sus retoques ya aplicados), para saber de antemano cómo debería
sonar el instrumento completo antes de afinarlo cuerda por cuerda. Como la mayoría de
escalas y maqams solo modifican unas pocas cuerdas respecto a la afinación de fábrica, es la
forma más clara de notar cuáles cambian y cuáles no. Se puede interrumpir a mitad con
`Ctrl+E` (detiene también la captura del micrófono) o volviendo a pulsar `Ctrl+Mayús+P`.

La escucha previa reproduce una vez las notas objetivo completas, desde la cuerda más grave
hasta la más aguda. Así permite comprobar cómo debe quedar el instrumento sin mezclar la
afinación de fábrica con otra nota de comparación.

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
instrucción y la nota detectada, p. ej. "Sube un poco" y "Sol4") y "Detallado", que añade
los cents exactos de desviación (p. ej. "Sube un poco (+18 cents)").

## Ajustes persistentes

El dispositivo de entrada, la tasa de muestreo, el tamaño de búfer, el instrumento, la
cuerda seleccionada y las opciones de accesibilidad se guardan automáticamente en
`configuraciones/ajustes.json` y se restauran al volver a abrir la aplicación.

## Diagnóstico de nivel de entrada

La etiqueta "Nivel de entrada" muestra en vivo el volumen (RMS) que está captando el
micrófono, para comprobar visualmente si hay señal. Si tras iniciar la escucha no se
detecta ninguna señal en unos segundos, la app lo anuncia por voz (puede indicar que el
dispositivo seleccionado no es el correcto, o que está silenciado a nivel de Windows).

La opción "Desmutear el micrófono si Windows lo tiene silenciado" está desactivada por
defecto. Al activarla, la aplicación puede desmutear el dispositivo seleccionado antes de
iniciar la escucha (requiere `pycaw`, instalado por defecto en Windows vía `requisitos.txt`).

## Avance automático de cuerda

Al mantener la afinación correcta ("AFINADA") de forma estable durante poco más de un
segundo, el selector de cuerda avanza automáticamente a la siguiente de la lista (no
aplica en modo Cromático, que no tiene una secuencia de cuerdas).

## Pruebas

```
python -m unittest discover -s tests -v
```

Además de estas pruebas automáticas, antes de distribuir una versión deben
realizarse las comprobaciones de teclado, NVDA y dispositivos reales indicadas
en [`PRUEBAS_MANUALES_ACCESIBILIDAD.md`](PRUEBAS_MANUALES_ACCESIBILIDAD.md).

## Documentación

- [`LEEME.txt`](LEEME.txt): punto de partida para quien descarga la aplicación.
- [`ayuda.html`](ayuda.html): manual de uso local; también se abre con `F1`.
- [`DEVELOPMENT.md`](DEVELOPMENT.md): arquitectura, reglas técnicas y pruebas.
- [`BITACORA_DE_DESARROLLO.md`](BITACORA_DE_DESARROLLO.md): historia y decisiones
  del proyecto.
- [`documentos/Fases_Del_Proyecto/VISION_PERSONAL.md`](documentos/Fases_Del_Proyecto/VISION_PERSONAL.md):
  propósito y criterios que no se deben perder al evolucionar la aplicación.
- [`PRUEBAS_MANUALES_ACCESIBILIDAD.md`](PRUEBAS_MANUALES_ACCESIBILIDAD.md): lista
  de validación previa a una publicación.
- [`AUDITORIA_EPUB_TTS.md`](AUDITORIA_EPUB_TTS.md): patrones adaptados del otro
  proyecto y los que no corresponden aquí.
- [`GUIA_SCRIPTS.md`](GUIA_SCRIPTS.md): qué hace cada archivo `.bat`.

## Estado del proyecto

La rama `review-claude` contiene una versión funcional con pruebas unitarias de
la lógica musical, perfiles y audio. Aún no debe considerarse una versión
estable de distribución hasta completar las pruebas manuales con NVDA, la
lira, guitarra, ukelele y los dispositivos de entrada reales. La rama `main`
permanece sin tocar durante esa validación.

## Estructura

```
app/
├── motor_audio.py     # Captura de audio (dispatcher Rust/Python), algoritmo YIN de respaldo,
│                       # generador de tonos de referencia
├── conector_nvda.py   # Salida de voz al lector de pantalla activo, con throttling por estabilidad
├── interfaz/          # Ventana principal y recursos de interfaz wxPython
├── interfaz_gui.py    # Fachada de compatibilidad para importaciones anteriores
├── gestor_ajustes.py  # Persistencia atómica de ajustes en configuraciones/ajustes.json
├── control_microfono.py  # Desmute automático del micrófono a nivel de Windows (pycaw)
└── config_rutas.py    # Rutas absolutas del proyecto
recursos/sonidos/       # Ubicación documentada para efectos WAV opcionales
motor_rust/             # Extensión nativa opcional: captura de audio (cpal) + YIN, vía PyO3
tests/                  # Pruebas del algoritmo YIN y la lógica de notas/instrucciones
iniciar_afinador.py     # Punto de entrada
requisitos.txt          # Dependencias de Python
INICIAR_AFINADOR.bat    # Lanzador para Windows
INSTALAR_AFINADOR.bat   # Instalación guiada de las dependencias
documentos/             # Visión y documentación de planificación
```

## Instrumentos soportados

- Cromático (cualquier nota)
- Lira de 16 cuerdas (Aklot): diatónica en Do mayor, Sol3 a La5
- Ukelele: Sol4, Do4, Mi4, La4 (GCEA reentrante estándar)
- Guitarra: Mi2, La2, Re3, Sol3, Si3, Mi4 (afinación estándar)
