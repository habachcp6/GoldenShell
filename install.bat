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

:: Create virtual environment
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)

:: Install using venv pip directly (no activation needed)
echo Installing GoldenShell...
venv\Scripts\pip install --quiet .
if errorlevel 1 (
    echo ERROR: Installation failed.
    pause
    exit /b 1
)

echo.
echo Installation complete!
echo.
echo To use GoldenShell:
echo   venv\Scripts\activate
echo   goldenshell --help
echo.
echo Or without activating:
echo   venv\Scripts\goldenshell --help
echo.
pause
