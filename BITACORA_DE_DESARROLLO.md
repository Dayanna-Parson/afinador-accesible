# Bitácora de desarrollo — AfinadorAccesible

## El origen

Este proyecto nace de una necesidad concreta: afinar una lira Aklot de 16
cuerdas desde Windows de una forma realmente manejable sin visión. Los
afinadores disponibles no resultaban suficientemente accesibles, claros o
cómodos para el flujo de trabajo con NVDA. La respuesta fue la misma que guía
los demás proyectos de Dayanna: si una herramienta necesaria no existe o no se
puede usar bien, construirla.

El objetivo nunca fue añadir instrumentos al azar. La aplicación está centrada
en los tres instrumentos que realmente se usan: lira Aklot de 16 cuerdas,
guitarra acústica/electroclásica y ukelele soprano.

## Decisiones de base

- **Windows y wxPython.** Los controles nativos ofrecen una navegación más
  predecible con NVDA, JAWS y Narrador que una interfaz web improvisada.
- **Código e interfaz en español.** Es una decisión de mantenimiento y de
  comprensión, no una limitación técnica.
- **Audio desacoplado de la interfaz.** La captura y el cálculo nunca deben
  bloquear los controles; wxPython solo se actualiza desde el hilo principal.
- **Ajustes locales y atómicos.** Perder perfiles personales por un cierre a
  mitad de una escritura sería inaceptable.

## Del afinador básico a una herramienta musical

La primera versión resolvía la detección de nota y la afinación básica. Después
se añadieron calibración de La4, selección de dispositivo y canal para la
Scarlett, vigilancia de captura, sensibilidad, ganancia, WASAPI opcional y
anuncios de voz con cadencia controlada.

La interfaz se reorganizó en tres pestañas: **Afinar**, **Afinaciones
especiales** y **Audio y ajustes**. La división no busca llenar la ventana de
controles: separa la tarea inmediata, las decisiones musicales menos frecuentes
y la configuración técnica.

## Música árabe y la lira

La incorporación de maqamat exigió una corrección importante: una lira
diatónica sin palancas no es un oud ni un qanun. Puede retunearse para reflejar
los grados de un maqam en una aproximación de 24 divisiones por octava, pero no
modula durante una interpretación ni sustituye las inflexiones de un
instrumento árabe sin trastes.

Los mapas de las escalas se mantienen separados de la interfaz y se prueban con
datos de referencia. La afinación estándar de la lira se conserva exacta:
Sol3–La3–Si3–Do4–Re4–Mi4–Fa4–Sol4–La4–Si4–Do5–Re5–Mi5–Fa5–Sol5–La5; no se
introducen alteraciones ni cuartos de tono cuando no se han elegido.

## Perfiles y seguridad

Las afinaciones personales se guardan por instrumento. Un perfil de lira puede
partir de un maqam y conservar sus retoques; guitarra y ukelele mantienen sus
propias afinaciones abiertas. Las copias JSON permiten transportar perfiles sin
pisar otros existentes.

Los retoques manuales de la lira permiten cuarto de tono, semitono y tono. En
guitarra y ukelele se restringen a semitonos y tonos: sus trastes siguen siendo
occidentales. Al subir una cuerda dos semitonos o más desde el estándar, la app
avisa del riesgo de tensión antes de continuar.

## Estado actual

La lógica cuenta con pruebas automatizadas y la documentación se ha organizado
para que otra desarrolladora pueda continuar el proyecto sin depender de una
conversación. Queda una fase imprescindible: pruebas reales de navegación con
NVDA, detección acústica, Scarlett y los tres instrumentos. Esa validación,
documentada en `PRUEBAS_MANUALES_ACCESIBILIDAD.md`, es la condición para llamar
a una versión estable y proponer pasarla a `main`.

— Dayanna Parson, agosto de 2026
