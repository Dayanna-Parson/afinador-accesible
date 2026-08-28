# Bitácora de desarrollo — AfinadorAccesible

## El origen

Empecé esto porque necesitaba afinar mi lira Aklot de 16 cuerdas desde Windows
de una forma que de verdad pudiera usar sin ver la pantalla. Los afinadores que
probé no eran lo bastante claros ni cómodos con NVDA. Es la misma lógica que
sigo en mis demás proyectos: si la herramienta que necesito no existe o no
funciona bien para mí, la construyo.

Nunca quise una lista larga de instrumentos. Me interesan los tres que uso de
verdad: mi lira Aklot de 16 cuerdas, mi guitarra acústica/electroclásica y mi
ukelele soprano.

## Decisiones de base

- **Windows y wxPython.** Sus controles nativos se llevan mejor con NVDA, JAWS
  y Narrador que cualquier interfaz web improvisada.
- **Código e interfaz en español.** Es cómo trabajo y cómo mantengo mis
  proyectos, no una limitación técnica.
- **Audio desacoplado de la interfaz.** La captura y el cálculo no pueden
  bloquear los controles; wxPython solo se toca desde el hilo principal.
- **Ajustes locales y atómicos.** Perder un perfil por un cierre a medias
  mientras se escribe el archivo sería inaceptable.

## Del afinador básico a una herramienta musical

La primera versión solo resolvía detectar la nota y decir sube/baja. Después
fui añadiendo calibración de La4, selección de dispositivo y canal para la
Scarlett, vigilancia de la captura, ganancia, sensibilidad, modo exclusivo
WASAPI opcional y anuncios de voz con cadencia controlada para no saturar la
cola de NVDA.

La interfaz acabó organizada en tres pestañas: **Afinar**, **Afinaciones
especiales** y **Audio y ajustes**. No es por llenar hueco: separa la tarea
del día a día, las decisiones musicales que tomo de vez en cuando, y la
configuración técnica que casi nunca toco.

## Música árabe y la lira

Meter maqamat me obligó a corregirme algo importante: una lira diatónica sin
palancas no es un oud ni un qanun. Puedo reafinarla para que refleje los
grados de un maqam en una aproximación de 24 divisiones por octava, pero no
modula a mitad de una interpretación ni sustituye las inflexiones de un
instrumento árabe sin trastes.

Los mapas de las escalas viven separados de la interfaz y se prueban contra
datos de referencia. La afinación estándar de la lira se mantiene exacta:
Sol3-La3-Si3-Do4-Re4-Mi4-Fa4-Sol4-La4-Si4-Do5-Re5-Mi5-Fa5-Sol5-La5, sin
alteraciones ni cuartos de tono salvo que yo los elija.

## Perfiles y seguridad

Guardo las afinaciones personales por instrumento. Un perfil de lira puede
partir de un maqam y conservar mis retoques encima; guitarra y ukelele
guardan sus propias afinaciones abiertas. Las copias en JSON me dejan mover
perfiles de un sitio a otro sin pisar los que ya tengo.

En la lira, el retoque manual admite cuarto de tono, semitono o tono. En
guitarra y ukelele lo dejé solo en semitonos y tonos, porque sus trastes
siguen siendo occidentales. Y si intento subir una cuerda dos semitonos o
más sobre el estándar, la app me avisa del riesgo de tensión antes de dejarme
seguir.

## Estado actual

La lógica ya tiene pruebas automatizadas y la documentación está organizada
para que pueda retomar el proyecto sin depender de recordar por qué decidí
cada cosa. Me queda una fase que no pienso saltarme: probarlo de verdad con
NVDA, con los tres instrumentos y con la Scarlett conectada. Esa validación
está en `PRUEBAS_MANUALES_ACCESIBILIDAD.md`, y es la condición para llamar
estable a esta versión y pasarla a `main`.
