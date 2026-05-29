#!/usr/bin/env bash
# GoldenShell installer for Linux/macOS
set -e

echo "🐚 GoldenShell — Installer"
echo "================================"

# Check Python version
PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
    echo "❌ Python 3.10+ is required but not found."
    exit 1
fi

PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PY_VERSION detected"

# Create virtual environment
echo "📦 Creating virtual environment..."
$PYTHON -m venv venv

# Install using venv pip directly (no need to activate)
echo "⬇️  Installing GoldenShell..."
venv/bin/pip install --quiet .

echo ""
echo "✅ Installation complete!"
echo ""
echo "Usage:"
echo "  source venv/bin/activate"
echo "  goldenshell --help"
echo ""
echo "Or without activating:"
echo "  venv/bin/goldenshell --help"
