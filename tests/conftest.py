import sys
from pathlib import Path

# Allow importing the Reflex app package without requiring installation.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
