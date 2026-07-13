@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
set "ICON=%ROOT%\assets\icon.ico"

echo.
echo   ═══════════════════════════════════════
echo     Signal Studio  —  сборка EXE
echo   ═══════════════════════════════════════
echo   Иконка: %ICON%
echo.

if not exist ".venv\Scripts\python.exe" (
    echo   [X] Нет .venv. Создайте:  python -m venv .venv
    pause
    exit /b 1
)

echo   [1] Очистка старой сборки...
if exist "build" rd /s /q "build"
if exist "dist\Signal Studio.exe" del /q "dist\Signal Studio.exe"
if exist "Signal Studio.spec" del /q "Signal Studio.spec"

echo   [2] Установка PyInstaller...
.venv\Scripts\python.exe -m pip install -q pyinstaller

echo   [3] Сборка (onefile, иконка из assets)...
.venv\Scripts\pyinstaller.exe --noconfirm --clean --name="Signal Studio" --onefile --windowed ^
  --distpath=dist --workpath=build --specpath=. ^
  --additional-hooks-dir=hooks ^
  --add-data="gui;gui" --add-data="core;core" --add-data="assets;assets" ^
  --icon="assets\icon.ico" ^
  --hidden-import=PyQt6.QtCore --hidden-import=PyQt6.QtGui --hidden-import=PyQt6.QtWidgets ^
  --hidden-import=numpy --hidden-import=scipy --hidden-import=scipy.signal --hidden-import=sounddevice --hidden-import=cffi --hidden-import=_cffi_backend ^
  --exclude-module=tkinter --exclude-module=matplotlib --exclude-module=pytest ^
  --exclude-module=pyqtgraph.opengl --exclude-module=pyqtgraph.canvas --exclude-module=OpenGL ^
  --noupx --log-level=WARN ^
  main.py

if errorlevel 1 (
    echo.
    echo   [X] Сборка не удалась.
    pause
    exit /b 1
)

if not exist "dist\Signal Studio.exe" (
    echo   [X] EXE не найден в dist
    pause
    exit /b 1
)

echo.
echo   ═══════════════════════════════════════
echo     Готово:  dist\Signal Studio.exe
echo   ═══════════════════════════════════════
echo.
%SystemRoot%\System32\ie4uinit.exe -show 2>nul
explorer "%~dp0dist"
endlocal
