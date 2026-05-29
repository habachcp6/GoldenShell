#!/usr/bin/env bash
# GoldenShell installer — Universal (Linux / macOS)

echo "GoldenShell - Installer"
echo "================================"

# ── Check Python ─────────────────────────────────────────────────────────────
PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
    echo "ERROR: Python 3.10+ is required."
    echo "  Debian/Kali/Ubuntu:  sudo apt install python3 python3-pip"
    echo "  Fedora:              sudo dnf install python3 python3-pip"
    echo "  Arch:                sudo pacman -S python python-pip"
    exit 1
fi

PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python $PY_VERSION detected"

# ── Install ──────────────────────────────────────────────────────────────────
echo "Installing GoldenShell..."

# --break-system-packages: bỏ qua rào cản PEP 668 trên Debian/Kali/Ubuntu
# Trên các distro không cần flag này, pip tự bỏ qua — không ảnh hưởng gì.
$PYTHON -m pip install . --break-system-packages --quiet 2>/dev/null

if [ $? -ne 0 ]; then
    # Fallback cho pip cũ (< 23.0) chưa hỗ trợ --break-system-packages
    $PYTHON -m pip install . --quiet 2>/dev/null
fi

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Installation failed."
    echo "Try: python3 -m pip install . --break-system-packages"
    exit 1
fi

echo ""
echo "Installation complete!"
echo ""

# ── PATH check ───────────────────────────────────────────────────────────────
if command -v goldenshell &>/dev/null; then
    echo "Usage: goldenshell --help"
else
    echo "Run: python3 -m goldenshell --help"
fi
