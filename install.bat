@echo off
:: GoldenShell installer for Windows
setlocal EnableDelayedExpansion

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

:: Install directly
echo Installing GoldenShell...
python -m pip install --quiet .
if errorlevel 1 (
    echo ERROR: Installation failed.
    pause
    exit /b 1
)

:: Add Python Scripts to PATH for current session
for /f "delims=" %%i in ('python -c "import sysconfig; print(sysconfig.get_path(\"scripts\"))"') do set SCRIPTS_DIR=%%i
if not "!SCRIPTS_DIR!"=="" (
    set PATH=!SCRIPTS_DIR!;!PATH!
)

:: Verify goldenshell is accessible
where goldenshell >nul 2>&1
if errorlevel 1 (
    echo.
    echo Installation complete!
    echo.
    echo NOTE: 'goldenshell' command may not be in PATH yet.
    echo Use this command instead:
    echo   python -m goldenshell --help
    echo.
    echo Or add this to your PATH manually:
    echo   !SCRIPTS_DIR!
) else (
    echo.
    echo Installation complete!
    echo.
    echo Usage: goldenshell --help
)
echo.
pause
