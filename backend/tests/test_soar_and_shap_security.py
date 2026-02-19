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


def test_soar_engine_respects_guardrails(backend_app_module, monkeypatch):
    engine = backend_app_module.soar_engine.SOAREngine()

    playbook = backend_app_module.models.Playbook(
        id="pb-guard",
        name="guard",
        is_active=True,
        trigger_field="riskLevel",
        trigger_operator="equals",
        trigger_value="CRITICAL",
        action_type="LOCK_USER",
        action_target=None,
        min_confidence=0.9,
        requires_approval=True,
        rate_limit_count=1,
        rate_limit_window_seconds=300,
        scope="global",
    )
    log = backend_app_module.models.Log(
        id="log-1",
        timestamp=datetime.now().isoformat(),
        user="alice",
        activity_type="SYSTEM",
        risk_level="CRITICAL",
        description="test",
        details="test",
        activity_summary='{"confidence": 0.95}',
    )

    class DBStub:
        def __init__(self):
            self.audit = []

        def add(self, item):
            if item.__class__.__name__ == "PlaybookActionAudit":
                self.audit.append(item)

        def commit(self):
            return None

    db = DBStub()
    called = {"executed": 0}

    monkeypatch.setattr(engine, "_execute_action", lambda *_args, **_kwargs: called.__setitem__("executed", called["executed"] + 1))
    monkeypatch.setattr(engine, "_check_trigger", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        backend_app_module.soar_engine,
        "models",
        backend_app_module.models,
    )

    engine._evaluate_rules = engine._evaluate_rules.__get__(engine, backend_app_module.soar_engine.SOAREngine)
    monkeypatch.setattr(
        backend_app_module.soar_engine,
        "database",
        backend_app_module.database,
    )

    monkeypatch.setattr(
        type("Q", (), {}),
        "all",
        lambda self: [playbook],
        raising=False,
    )

    # run through direct checks since query chain is tightly coupled
    confidence = engine._extract_confidence(log)
    assert confidence == 0.95
    assert engine._approval_required(playbook, confidence) is True
