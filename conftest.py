"""
Root Pytest Configuration — Virtual IoT Security Laboratory

Ensures both the root project and the backend directory are added to sys.path
so tests can import from backend.app and device_simulator cleanly.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))