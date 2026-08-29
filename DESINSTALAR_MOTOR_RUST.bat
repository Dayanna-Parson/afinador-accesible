@echo off
setlocal
cd /d "%~dp0"
cls
echo ---------------------------------------------------
echo    DESINSTALAR EL MOTOR OPCIONAL DE RUST
echo ---------------------------------------------------
echo.
echo Esto quita el modulo motor_rust del entorno de la aplicacion.
echo El afinador seguira funcionando igual, con su motor compatible
echo de Python (mismas afinaciones, mismo maqam, misma interfaz).
echo.

if not exist ".venv\Scripts\python.exe" (
    echo No se encontro el entorno de la aplicacion ^(.venv^).
    echo Si nunca ejecutaste INSTALAR_AFINADOR.bat en esta carpeta, no hay nada que desinstalar.
    goto :fin
)

set "PYTHON_AFINADOR=%CD%\.venv\Scripts\python.exe"

"%PYTHON_AFINADOR%" -c "import motor_rust" >nul 2>&1
if errorlevel 1 (
    echo El motor de Rust no esta instalado en este entorno. No hay nada que hacer.
    goto :fin
)

echo Desinstalando motor_rust...
"%PYTHON_AFINADOR%" -m pip uninstall motor_rust -y
if errorlevel 1 (
    echo No se pudo desinstalar motor_rust.
    goto :fin
)

echo.
echo Motor de Rust desinstalado. La proxima vez que abras el afinador,
echo usara automaticamente su motor compatible de Python.

:fin
echo.
pause
endlocal
