@echo off
setlocal
cd /d "%~dp0"
cls
echo ---------------------------------------------------
echo    INSTALADOR DE AFINADOR ACCESIBLE
echo ---------------------------------------------------
echo.

py -3.12 -c "import sys" >nul 2>&1
if not errorlevel 1 (
    set "COMANDO_PYTHON=py -3.12"
) else (
    python -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>&1
    if errorlevel 1 (
        echo No se encontro Python 3.12 o superior.
        echo Instalalo desde https://www.python.org/downloads/windows/
        echo Durante la instalacion, marca la opcion para agregar Python al PATH.
        goto :fin
    )
    set "COMANDO_PYTHON=python"
)

if not exist ".venv\Scripts\python.exe" (
    echo Creando el entorno de la aplicacion...
    %COMANDO_PYTHON% -m venv .venv
    if errorlevel 1 (
        echo No se pudo crear el entorno de la aplicacion.
        goto :fin
    )
)

set "PYTHON_AFINADOR=%CD%\.venv\Scripts\python.exe"
echo Actualizando las herramientas de instalacion...
"%PYTHON_AFINADOR%" -m pip install --upgrade pip
if errorlevel 1 goto :error_dependencias

echo Instalando las dependencias necesarias...
"%PYTHON_AFINADOR%" -m pip install -r requisitos.txt
if errorlevel 1 goto :error_dependencias

echo.
choice /C SN /N /M "¿Compilar tambien el motor opcional de Rust? [S/N]"
if errorlevel 2 goto :instalacion_completa

where cargo >nul 2>&1
if errorlevel 1 (
    echo.
    echo Rust no esta instalado. El afinador funcionara con su motor compatible de Python.
    echo Para compilar el motor opcional mas adelante, instala Rust y vuelve a ejecutar este archivo.
    goto :instalacion_completa
)

echo Instalando la herramienta de compilacion de Rust...
"%PYTHON_AFINADOR%" -m pip install maturin
if errorlevel 1 goto :error_dependencias

echo Compilando el motor opcional de Rust...
pushd motor_rust
"%PYTHON_AFINADOR%" -m maturin develop --release
set "RESULTADO_RUST=%ERRORLEVEL%"
popd
if not "%RESULTADO_RUST%"=="0" (
    echo No se pudo compilar Rust. El afinador seguira funcionando con Python.
)

:instalacion_completa
echo.
echo Instalacion terminada.
echo Para abrir el afinador, ejecuta INICIAR_AFINADOR.bat.
goto :fin

:error_dependencias
echo.
echo No se pudieron instalar todas las dependencias. Comprueba tu conexion a Internet.

:fin
echo.
pause
endlocal
