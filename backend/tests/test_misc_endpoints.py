import json
import uuid
from datetime import datetime


def test_predict_endpoint_is_patched(client, auth_headers, backend_app_module, monkeypatch):
    monkeypatch.setattr(
        backend_app_module.prediction_engine.predictor,
        "predict_next_step",
        lambda activity: [{"activity": "NEXT", "probability": 1.0}],
    )
    res = client.get("/predict?current_activity=TEST", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["currentActivity"] == "TEST"
    assert body["predictions"][0]["activity"] == "NEXT"


def test_chat_endpoint_returns_structured_response(client, auth_headers, backend_app_module, monkeypatch):
    class FakeResponse:
        status_code = 200

        def json(self):
            return {"response": json.dumps({"text": "Hello", "actions": []})}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *_args, **_kwargs):
            return FakeResponse()

    monkeypatch.setattr(backend_app_module.httpx, "AsyncClient", lambda: FakeClient())

    res = client.post("/chat", json={"message": "hi", "context": []}, headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["role"] == "ai"
    assert body["text"] == "Hello"


def test_chat_endpoint_validates_llm_assessment(client, auth_headers, backend_app_module, monkeypatch):
    backend_app_module.llm_response_cache._items.clear()

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "response": json.dumps(
                    {
                        "text": "Assessment",
                        "actions": [],
                        "llm_assessment": {
                            "risk_level": "SUSPICIOUS",
                            "threat_type": "c2_beaconing",
                            "confidence": 0.88,
                            "reasoning": "periodic network pattern",
                            "recommended_actions": ["block_ip", "collect_forensics"],
                        },
                    }
                )
            }

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *_args, **_kwargs):
            return FakeResponse()

    monkeypatch.setattr(backend_app_module.httpx, "AsyncClient", lambda: FakeClient())

    res = client.post("/chat", json={"message": "hi", "context": []}, headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["llmAssessment"]["risk_level"] == "SUSPICIOUS"


def test_network_traffic_create_read_and_analyze(client, auth_headers, backend_app_module, monkeypatch):
    monkeypatch.setattr(backend_app_module.analysis, "analyze_network_traffic", lambda data: {"summary": "ok", "anomaly_score": 0.0, "anomalies_detected": 0, "details": []})
    monkeypatch.setattr(backend_app_module.ml_engine, "predict_anomaly", lambda _: 1)
    monkeypatch.setattr(backend_app_module.notifications, "send_alert", lambda *_: None)

    class SioStub:
        async def emit(self, _event, _payload):
            return None

    monkeypatch.setattr(backend_app_module, "sio", SioStub())

    tid = str(uuid.uuid4())
    res = client.post(
        "/traffic",
        json={
            "id": tid,
            "timestamp": datetime.now().isoformat(),
            "sourceIp": "10.0.0.1",
            "destinationIp": "10.0.0.2",
            "port": 443,
            "protocol": "TCP",
            "bytesTransferred": 1234,
            "packetCount": 10,
            "latency": 0,
            "isAnomalous": False,
        },
    )
    assert res.status_code == 200
    assert res.json()["id"] == tid

    res = client.get("/traffic", headers=auth_headers)
    assert res.status_code == 200
    assert any(t["id"] == tid for t in res.json())

    res = client.get("/traffic/analyze", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["summary"] == "ok"


def test_reports_export_formats(client, auth_headers):
    for fmt, expected in [("csv", "text/csv"), ("json", "application/json"), ("pdf", "application/pdf")]:
        res = client.get(f"/api/reports/export?format={fmt}&compress=false", headers=auth_headers)
        assert res.status_code == 200
        assert res.headers["content-type"].startswith(expected)

    res = client.get("/api/reports/export?format=csv&compress=true", headers=auth_headers)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("application/zip")


def test_notifications_test_endpoint(client, auth_headers, backend_app_module, monkeypatch):
    monkeypatch.setattr(backend_app_module.notifications.requests, "post", lambda *_args, **_kwargs: type("R", (), {"status_code": 200})())

    class DummySMTP:
        def __init__(self, *_args, **_kwargs):
            pass

        def starttls(self):
            return None

        def login(self, *_args, **_kwargs):
            return None

        def send_message(self, *_args, **_kwargs):
            return None

        def quit(self):
            return None

    monkeypatch.setattr(backend_app_module.notifications.smtplib, "SMTP", DummySMTP)

    client.put(
        "/settings",
        json={
            "blockGambling": True,
            "blockSocialMedia": False,
            "enforceSafeSearch": True,
            "screenTimeLimit": True,
            "screenTimeDurationMinutes": 120,
            "alertOnKeywords": True,
            "captureScreenshots": False,
            "keywords": ["password"],
            "emailNotifications": True,
            "notificationEmail": "test@example.com",
            "webhookUrl": "http://example.test",
            "smtpServer": "smtp.example.test",
            "smtpPort": 587,
        },
        headers=auth_headers,
    )

    res = client.post("/api/notifications/test", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["webhook"] == "success"
    assert body["email"] == "success"
    assert body["sms"] == "skipped"


def test_soar_actions_create_logs_and_reset_password(client, auth_headers, backend_app_module, monkeypatch):
    monkeypatch.setattr(backend_app_module.ml_engine, "predict_anomaly", lambda _: 1)
    monkeypatch.setattr(backend_app_module.notifications, "send_alert", lambda *_: None)

    class SioStub:
        async def emit(self, _event, _payload):
            return None

    monkeypatch.setattr(backend_app_module, "sio", SioStub())

    res = client.post("/actions/block-ip", json={"target": "1.2.3.4", "reason": "test"}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["success"] is True

    res = client.post("/actions/isolate-host", json={"target": "host-1", "reason": "test"}, headers=auth_headers)
    assert res.status_code == 200

    res = client.post("/actions/reset-password", json={"target": "admin", "reason": "test"}, headers=auth_headers)
    assert res.status_code == 200
    assert "reset" in res.json()["message"].lower()

    logs = client.get("/logs", headers=auth_headers).json()
    assert any(l["activityType"] == "SOAR_ACTION" for l in logs)


def test_agent_logs_endpoint_accepts_without_key_by_default(client):
    payload = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "user": "agent-default",
        "activityType": "SYSTEM",
        "riskLevel": "INFO",
        "description": "test",
        "details": "test",
    }
    res = client.post("/api/logs", json=payload)
    assert res.status_code == 200
