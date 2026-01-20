from pathlib import Path


ROOT = Path(__file__).resolve().parent


def pytest_sessionstart(session):
    (ROOT / "reports").mkdir(parents=True, exist_ok=True)
