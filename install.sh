#!/usr/bin/env bash
# GoldenShell installer for Linux/macOS

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

# Try normal install first
if $PYTHON -m pip install --quiet . 2>/dev/null; then
    echo ""
    echo "Installation complete!"
# Debian/Kali/Ubuntu: use --break-system-packages
elif $PYTHON -m pip install --quiet . --break-system-packages 2>/dev/null; then
    echo ""
    echo "Installation complete!"
    # Persist setting so future "pip install ." also works
    PIP_CONF=~/.config/pip/pip.conf
    mkdir -p "$(dirname "$PIP_CONF")"
    if ! grep -q "break-system-packages" "$PIP_CONF" 2>/dev/null; then
        printf '[install]\nbreak-system-packages = true\n' >> "$PIP_CONF"
        echo "Note: Configured pip for future installs (~/.config/pip/pip.conf)"
    fi
# Fallback: pipx
elif command -v pipx &>/dev/null; then
    pipx install . --quiet
    echo ""
    echo "Installation complete! (via pipx)"
else
    echo ""
    echo "ERROR: Could not install. Try manually:"
    echo "  pip install . --break-system-packages"
    echo "  OR: sudo apt install pipx -y && pipx install ."
    exit 1
fi

echo ""
# Check PATH
if command -v goldenshell &>/dev/null; then
    echo "Usage: goldenshell --help"
else
    USER_BIN=$($PYTHON -m site --user-base)/bin
    echo "NOTE: Run this to use 'goldenshell' directly:"
    echo "  export PATH=\"$USER_BIN:\$PATH\""
    echo "  OR: python3 -m goldenshell --help"
fi
