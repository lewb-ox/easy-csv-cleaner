@echo off
setlocal

set "APP_PYTHON_EXE=%~dp0.build-venv\Scripts\python.exe"
if not exist "%APP_PYTHON_EXE%" set "APP_PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
if not exist "%APP_PYTHON_EXE%" (
    echo Could not find a project virtual environment at .build-venv or .venv.
    echo Create one with a standard Python installation that includes Tcl/Tk.
    exit /b 1
)

"%APP_PYTHON_EXE%" -c "from PyInstaller.utils.hooks.tcl_tk import TclTkInfo; info = TclTkInfo(); print('Tkinter available:', info.available); raise SystemExit(0 if info.available else 1)"
if errorlevel 1 (
    echo This Python environment does not have working Tcl/Tk support.
    echo Install standard Python from python.org with Tcl/Tk selected, recreate the virtual environment, and retry.
    exit /b 1
)

"%APP_PYTHON_EXE%" -m PyInstaller --noconfirm --clean --onefile --windowed --name EasyCsvCleaner "%~dp0app.py"
if errorlevel 1 exit /b %errorlevel%

echo.
echo Build complete: dist\EasyCsvCleaner.exe
