import sys
import os
from pathlib import Path

# Add backend directory to sys.path so 'app' and its submodules are discoverable
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Signal Vercel environment
os.environ.setdefault("VERCEL", "1")

from app.main import app

# Expose app for Vercel ASGI serverless handler
__all__ = ["app"]
