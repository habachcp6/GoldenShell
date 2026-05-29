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

echo "Installing GoldenShell..."

# Try normal pip install first
if $PYTHON -m pip install --quiet . 2>/dev/null; then
    INSTALL_OK=true
# Debian/Kali/Ubuntu: externally-managed-environment → try --break-system-packages
elif $PYTHON -m pip install --quiet . --break-system-packages 2>/dev/null; then
    INSTALL_OK=true
    echo "NOTE: Installed with --break-system-packages (Debian/Kali mode)"
# Fallback: pipx
elif command -v pipx &>/dev/null; then
    pipx install . --quiet
    INSTALL_OK=true
    echo "NOTE: Installed via pipx"
else
    echo ""
    echo "ERROR: pip install failed. Try one of:"
    echo "  1) pip install . --break-system-packages"
    echo "  2) sudo apt install pipx -y && pipx install ."
    exit 1
fi

echo ""
echo "Installation complete!"
echo ""

# Check if goldenshell is in PATH
if command -v goldenshell &>/dev/null; then
    echo "Usage: goldenshell --help"
else
    echo "NOTE: 'goldenshell' not found in PATH."
    echo "Use: python3 -m goldenshell --help"
    echo "Or add Python's bin dir to PATH:"
    echo "  export PATH=\"\$($PYTHON -m site --user-base)/bin:\$PATH\""
fi
