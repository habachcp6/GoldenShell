@echo off
REM GoldenShell Installer - Windows
echo 🐚 Installing GoldenShell...

REM Create virtual environment
python -m venv venv
call venv\Scripts\activate.bat

REM Install GoldenShell
pip install --upgrade pip -q
pip install . -q

echo.
echo ✅ GoldenShell installed successfully!
echo.
echo To use GoldenShell, activate the venv first:
echo   venv\Scripts\activate
echo.
echo Then run:
echo   goldenshell --help
