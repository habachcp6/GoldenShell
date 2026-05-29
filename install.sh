#!/usr/bin/env bash
# GoldenShell installer for Linux/macOS
set -e

echo "GoldenShell - Installer"
echo "================================"

# Check Python
PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
    echo "ERROR: Python 3.10+ is required but not found."
    exit 1
fi

PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "OK: Python $PY_VERSION detected"

# Install directly (no venv)
echo "Installing GoldenShell..."
$PYTHON -m pip install --quiet .

echo ""
echo "Installation complete!"
echo ""
echo "Usage: goldenshell --help"
