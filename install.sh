#!/usr/bin/env bash
# GoldenShell installer — Universal (Linux / macOS)
# Tested: Kali, Ubuntu, Debian, Fedora, Arch, macOS

echo "GoldenShell - Installer"
echo "================================"

# ── 1. Check Python ──────────────────────────────────────────────────────────
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

# ── 2. Install ───────────────────────────────────────────────────────────────
echo "Installing GoldenShell..."

INSTALL_OK=false

# Try 1: Normal pip (works on Fedora, Arch, macOS, old Ubuntu)
if $PYTHON -m pip install . --quiet 2>/dev/null; then
    INSTALL_OK=true
# Try 2: PEP 668 systems (Kali, Debian, Ubuntu 23.04+)
elif $PYTHON -m pip install . --break-system-packages --quiet 2>/dev/null; then
    INSTALL_OK=true
fi

if [ "$INSTALL_OK" = false ]; then
    echo ""
    echo "ERROR: pip install failed. Try manually:"
    echo "  python3 -m pip install . --break-system-packages"
    exit 1
fi

# ── 3. Detect binary location & fix PATH ─────────────────────────────────────
# Find where pip installed the 'goldenshell' script
GOLDENSHELL_BIN=$($PYTHON -c "
import sysconfig, os
# Check user scheme first (non-root install)
user_scripts = sysconfig.get_path('scripts', scheme='posix_user')
sys_scripts  = sysconfig.get_path('scripts')
for d in [user_scripts, sys_scripts]:
    if d and os.path.isfile(os.path.join(d, 'goldenshell')):
        print(d)
        break
" 2>/dev/null)

if [ -n "$GOLDENSHELL_BIN" ] && [ -d "$GOLDENSHELL_BIN" ]; then
    # Add to current session
    export PATH="$GOLDENSHELL_BIN:$PATH"

    # Persist to shell config if not already there
    for SHELL_RC in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
        if [ -f "$SHELL_RC" ]; then
            if ! grep -q "$GOLDENSHELL_BIN" "$SHELL_RC" 2>/dev/null; then
                echo "" >> "$SHELL_RC"
                echo "# GoldenShell" >> "$SHELL_RC"
                echo "export PATH=\"$GOLDENSHELL_BIN:\$PATH\"" >> "$SHELL_RC"
                echo "Added $GOLDENSHELL_BIN to $SHELL_RC"
            fi
            break
        fi
    done
fi

# ── 4. Verify ────────────────────────────────────────────────────────────────
echo ""
echo "Installation complete!"
echo ""

if command -v goldenshell &>/dev/null; then
    echo "✅ Usage: goldenshell --help"
else
    echo "✅ Installed! Open a new terminal, then run:"
    echo "   goldenshell --help"
    echo ""
    echo "   Or in this session:"
    echo "   python3 -m goldenshell --help"
fi
