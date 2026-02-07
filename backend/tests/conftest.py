import importlib
import os
import sys
from pathlib import Path
import tempfile

import pytest
from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("MPLCONFIGDIR", tempfile.mkdtemp(prefix="mplconfig-test-"))


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("db") / "sentinel_test.db"


@pytest.fixture(scope="session")
def backend_app_module(test_db_path: Path):
    if str(BACKEND_DIR) in sys.path:
        sys.path.remove(str(BACKEND_DIR))
    sys.path.insert(0, str(BACKEND_DIR))

    os.environ.setdefault("SENTINEL_TESTING", "1")
    os.environ.setdefault("SENTINEL_DISABLE_BACKGROUND_TASKS", "1")
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{test_db_path}")
    os.environ.setdefault("SECRET_KEY", "test-secret-key")
    os.environ.setdefault("DEFAULT_ADMIN_ID", "admin")
    os.environ.setdefault("DEFAULT_ADMIN_NAME", "Admin User")
    os.environ.setdefault("DEFAULT_ADMIN_PASSWORD", "admin")
    os.environ.setdefault("DEFAULT_ANALYST_ID", "analyst")
    os.environ.setdefault("DEFAULT_ANALYST_NAME", "Alice Williams")
    os.environ.setdefault("DEFAULT_ANALYST_PASSWORD", "password")

    for module_name in ("main", "database", "config", "models", "schemas", "auth"):
        if module_name in sys.modules:
            sys.modules.pop(module_name)

    import main

    return main


@pytest.fixture()
def client(backend_app_module):
    backend_app_module.models.Base.metadata.drop_all(bind=backend_app_module.database.engine)
    backend_app_module.models.Base.metadata.create_all(bind=backend_app_module.database.engine)

    with TestClient(backend_app_module.app) as c:
        yield c


@pytest.fixture()
def token(client):
    admin_id = os.environ.get("DEFAULT_ADMIN_ID", "admin")
    admin_password = os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin")
    res = client.post(
        "/token",
        data={"username": admin_id, "password": admin_password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    body = res.json()
    return body.get("accessToken") or body["access_token"]


@pytest.fixture()
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def baseline_test_patches(backend_app_module, monkeypatch):
    class NoopTask:
        def delay(self, *_args, **_kwargs):
            return None

        def apply(self, *_args, **_kwargs):
            return None

    class SioStub:
        async def emit(self, _event, _payload):
            return None

    monkeypatch.setattr(backend_app_module.tasks, "run_soar_automation", NoopTask())
    monkeypatch.setattr(backend_app_module.tasks, "run_prediction_analysis", NoopTask())
    monkeypatch.setattr(backend_app_module.notifications, "send_alert", lambda *_: None)
    monkeypatch.setattr(backend_app_module.ml_engine, "predict_anomaly", lambda *_: 1)
    monkeypatch.setattr(backend_app_module, "sio", SioStub())
