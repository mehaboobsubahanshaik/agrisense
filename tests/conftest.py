import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DEV_MODE", "true")
