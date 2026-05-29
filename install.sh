#!/usr/bin/env bash
# GoldenShell installer — Universal (Linux / macOS)
# Works on: Debian, Kali, Ubuntu, Fedora, Arch, macOS — no sudo needed

echo "GoldenShell - Installer"
echo "================================"

# ── 1. Check Python ─────────────────────────────────────────────────────────
PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
    echo "ERROR: Python 3.10+ is required."
    echo "Install: sudo apt install python3  (Debian/Kali/Ubuntu)"
    echo "         sudo dnf install python3  (Fedora)"
    echo "         sudo pacman -S python     (Arch)"
    exit 1
fi

PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "OK: Python $PY_VERSION detected"

# ── 2. Install ───────────────────────────────────────────────────────────────
echo "Installing GoldenShell..."

# --user: installs to ~/.local/bin — works on ALL distros, no sudo, no venv
if ! $PYTHON -m pip install --user --quiet . 2>/dev/null; then
    echo "ERROR: pip install failed."
    echo "Try manually: python3 -m pip install --user ."
    exit 1
fi

echo "Installation complete!"
echo ""

# ── 3. PATH check ────────────────────────────────────────────────────────────
USER_BIN=$($PYTHON -m site --user-base)/bin

if command -v goldenshell &>/dev/null; then
    echo "Usage: goldenshell --help"
else
    echo "NOTE: Add to PATH to use 'goldenshell' directly:"
    echo ""
    echo "  echo 'export PATH=\"$USER_BIN:\$PATH\"' >> ~/.bashrc && source ~/.bashrc"
    echo ""
    echo "Or use without PATH:"
    echo "  python3 -m goldenshell --help"
fi
