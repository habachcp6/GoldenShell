"""Allow running goldenshell as a module: python -m goldenshell"""
import sys

# Fix Unicode rendering on Windows terminals (CP1252 -> UTF-8)
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from goldenshell.cli import app

app()
