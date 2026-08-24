@echo off
cd /d "%~dp0"
cls
echo ---------------------------------------------------
echo    INICIANDO AFINADOR ACCESIBLE...
echo ---------------------------------------------------
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" iniciar_afinador.py
) else (
    python iniciar_afinador.py
)
echo.
echo ---------------------------------------------------
echo    PROGRAMA CERRADO O FINALIZADO
echo    (Si ves un error arriba, leelo ahora)
echo ---------------------------------------------------
pause
