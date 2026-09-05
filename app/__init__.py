import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
backend_app = backend_dir / "app"

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

__path__.append(str(backend_app))
