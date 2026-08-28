# Guía de scripts de Windows

## `INSTALAR_AFINADOR.bat`

Es lo primero que ejecuto tras descargar el código. Crea o reutiliza un
entorno virtual de Python, instala lo que pide `requisitos.txt` y ofrece
compilar el motor Rust solo si ya tengo su toolchain instalado. Esa parte es
opcional: el afinador funciona sin ella.

Se puede volver a ejecutar sin miedo: actualiza las dependencias del entorno,
pero nunca toca perfiles ni ajustes ya guardados.

## `INICIAR_AFINADOR.bat`

Abre el afinador con el entorno que creó el instalador. Si la app se cierra
por un error, la ventana se queda abierta para poder leer el mensaje antes de
pulsar una tecla y cerrarla de verdad.

## `iniciar_afinador.py`

El punto de entrada cuando estoy desarrollando: `python iniciar_afinador.py`
desde una consola, con las dependencias ya instaladas.

## Regla al tocar estos scripts

Un `.bat` tiene que situarse primero en su propia carpeta, nunca asumir desde
dónde lo abrieron. Los mensajes van en español claro, y con tiempo suficiente
para leerse con un lector de pantalla antes de que la ventana se cierre sola.
