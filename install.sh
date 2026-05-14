#!/bin/bash
# GoldenShell Installer - Linux/macOS
set -e

echo "🐚 Installing GoldenShell..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install GoldenShell
pip install --upgrade pip -q
pip install . -q

echo ""
echo "✅ GoldenShell installed successfully!"
echo ""
echo "To use GoldenShell, activate the venv first:"
echo "  source venv/bin/activate"
echo ""
echo "Then run:"
echo "  goldenshell --help"
