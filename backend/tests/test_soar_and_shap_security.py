import uuid
from datetime import datetime
import importlib
import sys

import pytest


def test_celery_soar_task_runs_sync_engine(backend_app_module, monkeypatch):
    tasks_module = importlib.reload(sys.modules["tasks"])
    called = {"log_id": None}

    def fake_run(log_id):
        called["log_id"] = log_id

    monkeypatch.setattr(tasks_module.soar_engine.engine, "run_automation", fake_run)
    test_log_id = str(uuid.uuid4())
    tasks_module.run_soar_automation(test_log_id)
    assert called["log_id"] == test_log_id


def test_shap_explanation_for_dict_input(client, auth_headers, backend_app_module, monkeypatch):
    class PipelineStub:
        feature_columns = ["hour", "day_of_week", "user_encoded", "activity_type_encoded"]

        def load_artifacts(self):
            return True

        def preprocess(self, df, training=False):
            return df.assign(hour=0.0, day_of_week=0.0, user_encoded=1.0, activity_type_encoded=2.0)[
                self.feature_columns
            ]

    class ModelStub:
        model = object()

        def load(self):
            return True

        def predict_score(self, _X):
            return [-0.7]

        def predict(self, _X):
            return [-1]

    class ExplainerStub:
        def shap_values(self, X):
            return [[0.11, -0.05, 0.22, -0.01]]

    monkeypatch.setattr(backend_app_module.ml_engine, "_get_model_signature", lambda: 123.0)
    monkeypatch.setattr(backend_app_module.ml_engine, "DataPipeline", PipelineStub)
    monkeypatch.setattr(backend_app_module.ml_engine, "IsolationForestModel", ModelStub)
    monkeypatch.setattr(backend_app_module.ml_engine.shap, "TreeExplainer", lambda _model: ExplainerStub())
    backend_app_module.ml_engine._SHAP_STATE.update(
        {
            "signature": None,
            "pipeline": None,
            "model": None,
            "explainer": None,
        }
    )

    explanation = backend_app_module.ml_engine.explain_prediction(
        {
            "timestamp": datetime.now().isoformat(),
            "user": "alice",
            "activity_type": "LOGIN",
            "risk_level": "HIGH",
            "description": "suspicious login",
        }
    )

    assert "hour" in explanation
    assert "__anomaly_score__" in explanation
    assert explanation["__prediction__"] == -1.0


def test_strict_security_rejects_weak_default_passwords(monkeypatch):
    monkeypatch.setenv("ENFORCE_STRICT_SECURITY", "1")
    monkeypatch.setenv("DEFAULT_ADMIN_PASSWORD", "admin")
    monkeypatch.setenv("DEFAULT_ANALYST_PASSWORD", "password")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("SENTINEL_TESTING", "1")

    if "backend.config" in sys.modules:
        sys.modules.pop("backend.config")

    with pytest.raises(RuntimeError) as exc_info:
        import backend.config  # noqa: F401

    assert "Strict security mode" in str(exc_info.value)
