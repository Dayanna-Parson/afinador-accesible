# Guía de scripts de Windows

## `INSTALAR_AFINADOR.bat`

Es el punto de instalación para quien descarga el código. Crea o reutiliza un
entorno virtual de Python, instala lo indicado en `requisitos.txt` y ofrece
compilar el motor Rust solo si ya están disponibles sus herramientas. No hace
falta aceptar esa opción para usar el afinador.

Ejecutarlo otra vez es seguro: actualiza las dependencias del entorno de la
aplicación, pero no borra perfiles ni ajustes personales.

## `INICIAR_AFINADOR.bat`

Abre el afinador usando el entorno creado por el instalador. Si la aplicación
se cierra por un error, la ventana permanece abierta para que se pueda leer el
mensaje antes de pulsar una tecla.

## `iniciar_afinador.py`

Es el punto de entrada para desarrollo. Se puede ejecutar desde una consola con
`python iniciar_afinador.py` después de instalar las dependencias.

## Regla al modificar scripts

Un archivo `.bat` debe empezar situándose en su propia carpeta. No debe asumir
desde qué ubicación lo ha abierto la persona usuaria. Los mensajes deben estar
en español claro y dejar tiempo suficiente para leer cualquier error con un
lector de pantalla.
