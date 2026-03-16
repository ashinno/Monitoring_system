import json
import uuid
from datetime import datetime


def test_create_log_applies_keyword_policy_and_emits(client, auth_headers, backend_app_module, monkeypatch):
    class SioStub:
        def __init__(self):
            self.emitted = []

        async def emit(self, event, payload):
            self.emitted.append((event, payload))

    sio = SioStub()
    monkeypatch.setattr(backend_app_module, "sio", sio)
    monkeypatch.setattr(backend_app_module.ml_engine, "predict_anomaly", lambda _: 1)
    monkeypatch.setattr(backend_app_module.notifications, "send_alert", lambda *_: None)

    class DummyTask:
        def delay(self, *_args, **_kwargs):
            raise RuntimeError("no broker")

        def apply(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr(backend_app_module.tasks, "run_soar_automation", DummyTask())
    monkeypatch.setattr(backend_app_module.tasks, "run_prediction_analysis", DummyTask())

    res = client.put(
        "/settings",
        json={
            "blockGambling": False,
            "blockSocialMedia": False,
            "enforceSafeSearch": True,
            "screenTimeLimit": True,
            "screenTimeDurationMinutes": 120,
            "alertOnKeywords": True,
            "captureScreenshots": False,
            "keywords": ["confidential"],
        },
        headers=auth_headers,
    )
    assert res.status_code == 200

    log_id = str(uuid.uuid4())
    res = client.post(
        "/logs",
        json={
            "id": log_id,
            "timestamp": datetime.now().isoformat(),
            "user": "agent1",
            "activityType": "KEYLOG",
            "riskLevel": "INFO",
            "description": "This contains confidential info",
            "details": "details",
            "activitySummary": json.dumps({"a": 1}),
            "ipAddress": "127.0.0.1",
            "location": "Local",
        },
    )
    assert res.status_code == 200
    created = res.json()
    assert created["id"] == log_id
    assert created["riskLevel"] == "HIGH"
    assert "KEYWORD DETECTED" in created["description"]
    assert any(e[0] == "new_log" for e in sio.emitted)
    heatmap_events = [payload for event, payload in sio.emitted if event == "key_heatmap_update"]
    assert heatmap_events
    assert heatmap_events[-1] == {"a": 1}


def test_logs_read_and_keylog_stats(client, auth_headers):
    base_log = {
        "timestamp": datetime.now().isoformat(),
        "user": "agent1",
        "activityType": "KEYLOG",
        "riskLevel": "INFO",
        "description": "abc",
        "details": "def",
        "ipAddress": "127.0.0.1",
        "location": "Local",
    }

    for i in range(3):
        client.post(
            "/logs",
            json={**base_log, "id": str(uuid.uuid4()), "activitySummary": json.dumps({"x": i + 1})},
        )

    res = client.get("/logs", headers=auth_headers)
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) >= 3

    res = client.get("/logs/stats/keylogs", headers=auth_headers)
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_sessions"] >= 3
    assert stats["total_keystrokes"] == 6
    assert stats["total_duration_seconds"] == 0
    assert stats["top_apps"][0]["name"] == "Unknown"
    assert isinstance(stats["top_apps"], list)


def test_playbooks_crud(client, auth_headers):
    pb_id = f"pb-{uuid.uuid4().hex[:8]}"
    payload = {
        "id": pb_id,
        "name": "Test Rule",
        "isActive": True,
        "trigger": {"field": "riskLevel", "operator": "equals", "value": "CRITICAL"},
        "action": {"type": "LOCK_USER", "target": None},
    }

    res = client.post("/playbooks", json=payload, headers=auth_headers)
    assert res.status_code == 200
    created = res.json()
    assert created["id"] == pb_id

    res = client.get("/playbooks", headers=auth_headers)
    assert res.status_code == 200
    assert any(p["id"] == pb_id for p in res.json())

    res = client.put(f"/playbooks/{pb_id}/toggle", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["isActive"] is False

    res = client.delete(f"/playbooks/{pb_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == {"ok": True}

    res = client.put(f"/playbooks/{pb_id}/toggle", headers=auth_headers)
    assert res.status_code == 404


def test_playbook_guardrail_fields_roundtrip(client, auth_headers):
    pb_id = f"pb-{uuid.uuid4().hex[:8]}"
    payload = {
        "id": pb_id,
        "name": "Guardrail Rule",
        "isActive": True,
        "trigger": {"field": "riskLevel", "operator": "equals", "value": "HIGH"},
        "action": {"type": "LOCK_USER", "target": None},
        "minConfidence": 0.75,
        "requiresApproval": True,
        "rateLimitCount": 2,
        "rateLimitWindowSeconds": 60,
        "scope": "internal_only",
    }

    res = client.post("/playbooks", json=payload, headers=auth_headers)
    assert res.status_code == 200
    created = res.json()
    assert created["minConfidence"] == 0.75
    assert created["requiresApproval"] is True
    assert created["rateLimitCount"] == 2
    assert created["rateLimitWindowSeconds"] == 60
    assert created["scope"] == "internal_only"


def test_settings_get_update_and_validation(client, auth_headers):
    res = client.get("/settings", headers=auth_headers)
    assert res.status_code == 200
    settings = res.json()
    assert "keywords" in settings

    res = client.put(
        "/settings",
        json={
            "blockGambling": True,
            "blockSocialMedia": False,
            "enforceSafeSearch": True,
            "screenTimeLimit": True,
            "screenTimeDurationMinutes": 15,
            "alertOnKeywords": True,
            "captureScreenshots": False,
            "keywords": ["password"],
        },
        headers=auth_headers,
    )
    assert res.status_code == 200
    updated = res.json()
    assert updated["screenTimeDurationMinutes"] == 15
