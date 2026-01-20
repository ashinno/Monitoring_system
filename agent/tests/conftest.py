import sys
from pathlib import Path


AGENT_DIR = Path(__file__).resolve().parents[1]
if str(AGENT_DIR) in sys.path:
    sys.path.remove(str(AGENT_DIR))
sys.path.insert(0, str(AGENT_DIR))

if "config" in sys.modules:
    sys.modules.pop("config")

