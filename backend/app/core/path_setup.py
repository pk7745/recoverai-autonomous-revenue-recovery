import sys
from pathlib import Path

# Ensure both project root (recoverai/) and backend/ are always present in sys.path
core_dir = Path(__file__).resolve().parent
backend_dir = core_dir.parent.parent
project_root = backend_dir.parent

for p in [str(project_root), str(backend_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)
