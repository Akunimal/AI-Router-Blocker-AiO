@echo off
REM =====================================================================
REM  Build script para compilar AI Network Blocker en un .exe portable
REM  Requiere: Python 3.x + PyInstaller (pip install pyinstaller)
REM =====================================================================

echo.
echo ============================================================
echo   AI Network Blocker — Build Script
echo ============================================================
echo.

REM Verificar que PyInstaller está disponible
python -m PyInstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller no esta instalado.
    echo Ejecuta: pip install pyinstaller
    pause
    exit /b 1
)

echo [1/3] Limpiando builds anteriores...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "ai_blocker.spec" del /f /q ai_blocker.spec

echo [2/3] Compilando ai_blocker.py a .exe ...
echo.

REM Opciones de compilación:
REM   --onefile      → Un solo archivo .exe portátil
REM   --windowed     → Sin ventana de consola (solo la GUI tkinter)
REM   --uac-admin    → Solicita elevación UAC al ejecutar el .exe
REM   --name         → Nombre del ejecutable final
REM   --clean        → Limpia la caché de PyInstaller antes de compilar

python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --uac-admin ^
    --add-data "translations.json;." ^
    --add-data "icon.ico;." ^
    --add-data "icon_green.ico;." ^
    --add-data "icon_red.ico;." ^
    --name "AI-Router-Blocker-AiO" ^
    --clean ^
    ai_blocker.py

echo.
if %errorlevel% neq 0 (
    echo [ERROR] La compilacion ha fallado. Revisa los errores arriba.
    pause
    exit /b 1
)

echo [3/3] Copiando ejecutable a la raiz del proyecto...
copy /y "dist\AI-Router-Blocker-AiO.exe" "AI-Router-Blocker-AiO.exe" >nul

echo.
echo ============================================================
echo   Build completado exitosamente!
echo.
echo   Ejecutable: AI-Router-Blocker-AiO.exe
echo   Tamaño:
for %%A in ("AI-Router-Blocker-AiO.exe") do echo     %%~zA bytes
echo.
echo   NOTA: El .exe solicita permisos de Administrador
echo   automaticamente al ejecutarse (UAC).
echo ============================================================
echo.
pause
