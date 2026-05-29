@echo off
:: GoldenShell installer for Windows
setlocal

echo GoldenShell - Installer
echo ================================

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.10+ is required but not found.
    echo Download from: https://python.org/downloads
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PY_VERSION=%%v
echo OK: Python %PY_VERSION% detected

:: Install directly (no venv)
echo Installing GoldenShell...
python -m pip install --quiet .
if errorlevel 1 (
    echo ERROR: Installation failed.
    pause
    exit /b 1
)

echo.
echo Installation complete!
echo.
echo Usage: goldenshell --help
echo.
pause
