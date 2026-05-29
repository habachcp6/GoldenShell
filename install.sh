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

# Detect if running on Debian/Kali/Ubuntu (externally-managed)
EXTERNALLY_MANAGED=false
SITE_PACKAGES=$($PYTHON -c "import sysconfig; print(sysconfig.get_path('stdlib'))")
if [ -f "$SITE_PACKAGES/EXTERNALLY-MANAGED" ]; then
    EXTERNALLY_MANAGED=true
fi

# If Debian/Kali: configure pip to allow system-wide install
if [ "$EXTERNALLY_MANAGED" = true ]; then
    echo "Detected: Debian/Kali/Ubuntu environment"
    PIP_CONF_DIR="$HOME/.config/pip"
    PIP_CONF_FILE="$PIP_CONF_DIR/pip.conf"
    mkdir -p "$PIP_CONF_DIR"
    if ! grep -q "break-system-packages" "$PIP_CONF_FILE" 2>/dev/null; then
        cat >> "$PIP_CONF_FILE" << 'EOF'

[global]
break-system-packages = true
EOF
        echo "Configured: ~/.config/pip/pip.conf (break-system-packages = true)"
    fi
fi

# Install
echo "Installing GoldenShell..."
$PYTHON -m pip install --quiet .

echo ""
echo "Installation complete!"
echo ""

# Check PATH
if command -v goldenshell &>/dev/null; then
    echo "Usage: goldenshell --help"
else
    USER_BIN=$($PYTHON -m site --user-base)/bin
    echo "NOTE: Add Python bin to PATH if 'goldenshell' not found:"
    echo "  export PATH=\"$USER_BIN:\$PATH\""
    echo ""
    echo "Or use: python3 -m goldenshell --help"
fi
