import types
import uuid
from datetime import datetime


def test_ml_train_endpoint_triggers_training(client, auth_headers, backend_app_module, monkeypatch):
    called = {"count": 0}

    def fake_train_model(data_source, train_config=None):
        called["count"] += 1
        # endpoint now passes SQLAlchemy Session
        assert data_source is not None
        assert isinstance(train_config, dict)

    monkeypatch.setattr(backend_app_module.ml_engine, "train_model", fake_train_model)
    res = client.post("/ml/train", json={"autoencoder_epochs": 10, "data_limit": 5000}, headers=auth_headers)
    assert res.status_code == 200
    assert called["count"] == 1


def test_ml_federated_update_endpoint_accepts_weights(client, auth_headers, backend_app_module, monkeypatch):
    class AggregatorStub:
        def __init__(self):
            self.local_updates = []

        def collect_update(self, agent_id, weights):
            self.local_updates.append((agent_id, weights))

        def aggregate(self):
            return {"ok": True}

        def start_round(self, min_clients=None, timeout_seconds=None, round_id=None):
            return {
                "round_id": round_id or "round-test",
                "min_clients": min_clients or 1,
                "timeout_seconds": timeout_seconds or 300,
                "submitted_clients": 0,
                "revealed_clients": 0,
                "pending_reveals": 0,
                "finalized": False,
            }

        def get_round_status(self, round_id):
            return {
                "round_id": round_id,
                "min_clients": 1,
                "timeout_seconds": 300,
                "submitted_clients": 1,
                "revealed_clients": 1,
                "pending_reveals": 0,
                "finalized": False,
            }

        def reveal_mask(self, round_id, agent_id, mask):
            return {
                "accepted": True,
                "global_model_updated": True,
                "round": self.get_round_status(round_id),
                "aggregate": {"round_id": round_id, "feature_vector": mask},
            }

    monkeypatch.setattr(backend_app_module.ml_engine, "federated_aggregator", AggregatorStub())

    res = client.post("/ml/federated-update", json={"w": [1, 2, 3]}, headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "accepted"
    assert body["global_model_updated"] is True
    assert body["mode"] == "legacy"


def test_secure_federated_round_endpoints(client, auth_headers, backend_app_module, monkeypatch):
    class AggregatorStub:
        def __init__(self):
            self.latest_secure_global = {"round_id": "round-1", "feature_vector": [0.1, 0.2, 0.3]}

        def start_round(self, min_clients=None, timeout_seconds=None, round_id=None):
            return {
                "round_id": round_id or "round-1",
                "min_clients": min_clients or 2,
                "timeout_seconds": timeout_seconds or 300,
                "submitted_clients": 0,
                "revealed_clients": 0,
                "pending_reveals": 0,
                "finalized": False,
            }

        def get_round_status(self, round_id):
            return {
                "round_id": round_id,
                "min_clients": 2,
                "timeout_seconds": 300,
                "submitted_clients": 1,
                "revealed_clients": 0,
                "pending_reveals": 1,
                "finalized": False,
            }

        def collect_update(self, agent_id, payload):
            return {
                "mode": "secure",
                "accepted": True,
                "global_model_updated": False,
                "round": self.get_round_status(payload["round_id"]),
            }

        def reveal_mask(self, round_id, agent_id, mask):
            return {
                "accepted": True,
                "global_model_updated": True,
                "round": {
                    "round_id": round_id,
                    "min_clients": 2,
                    "timeout_seconds": 300,
                    "submitted_clients": 2,
                    "revealed_clients": 2,
                    "pending_reveals": 0,
                    "finalized": True,
                },
                "aggregate": {"round_id": round_id, "feature_vector": mask},
            }

    monkeypatch.setattr(backend_app_module.ml_engine, "federated_aggregator", AggregatorStub())

    start = client.post("/ml/federated/rounds/start", json={"min_clients": 2}, headers=auth_headers)
    assert start.status_code == 200
    round_id = start.json()["round"]["round_id"]

    submit = client.post(
        "/ml/federated-update",
        json={
            "round_id": round_id,
            "masked_update": [0.1, 0.2, 0.3],
            "num_samples": 10,
            "dp": {"epsilon": 1.0},
        },
        headers=auth_headers,
    )
    assert submit.status_code == 200
    assert submit.json()["mode"] == "secure"

    reveal = client.post(
        "/ml/federated/reveal-mask",
        json={"round_id": round_id, "mask": [0.01, 0.01, 0.01]},
        headers=auth_headers,
    )
    assert reveal.status_code == 200
    assert reveal.json()["global_model_updated"] is True

    status = client.get(f"/ml/federated/rounds/{round_id}", headers=auth_headers)
    assert status.status_code == 200
    assert status.json()["round"]["round_id"] == round_id

    global_model = client.get("/ml/federated/global-model", headers=auth_headers)
    assert global_model.status_code == 200
    assert global_model.json()["global_model"]["round_id"] == "round-1"


def test_analyze_endpoint_returns_analysis_result(client, auth_headers, backend_app_module, monkeypatch):
    monkeypatch.setattr(
        backend_app_module.analysis,
        "analyze_logs",
        lambda logs: {"summary": "ok", "threat_score": 0.0, "recommendations": [], "flagged_logs": []},
    )

    client.post(
        "/logs",
        json={
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "user": "agent1",
            "activityType": "SYSTEM",
            "riskLevel": "INFO",
            "description": "ok",
            "details": "ok",
        },
    )

    res = client.post("/analyze", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["summary"] == "ok"
    assert body["threatScore"] == 0.0


def test_system_metrics_endpoints(client, auth_headers, backend_app_module):
    res = client.get("/api/system-metrics", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert "cpu" in body and "memory" in body and "disk" in body

    db = backend_app_module.database.SessionLocal()
    try:
        backend_app_module.system_monitor.save_metric(db)
        db.commit()
    finally:
        db.close()

    res = client.get("/api/system-metrics/history", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_health_and_ready_endpoints(client, auth_headers):
    health = client.get("/health", headers=auth_headers)
    assert health.status_code == 200
    payload = health.json()
    assert payload["status"] in {"ok", "degraded"}
    assert "components" in payload

    ready = client.get("/ready", headers=auth_headers)
    assert ready.status_code in {200, 503}


def test_interception_routes(client, auth_headers, backend_app_module, monkeypatch):
    class InterceptorStub:
        def __init__(self):
            self.started = False

        def start(self, _config):
            self.started = True

        def stop(self):
            self.started = False

        def get_status(self):
            return {
                "is_running": self.started,
                "config": {
                    "is_running": self.started,
                    "interface": None,
                    "protocols": ["TCP", "UDP"],
                    "include_loopback": False,
                    "poll_interval_ms": 1000,
                },
                "stats": {"packets_intercepted": 0, "bytes_intercepted": 0, "errors": 0},
            }

        def get_available_interfaces(self):
            return ["en0", "lo0"]

    monkeypatch.setattr(backend_app_module, "interceptor", InterceptorStub())

    res = client.post(
        "/interception/start",
        json={"protocols": ["TCP", "UDP"], "includeLoopback": False, "pollIntervalMs": 1000},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["isRunning"] is True

    res = client.get("/interception/status", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["isRunning"] is True

    res = client.get("/interception/interfaces", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == ["en0", "lo0"]

    res = client.post("/interception/stop", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["isRunning"] is False


def test_simulation_profiles_crud(client, auth_headers):
    profile = {
        "name": f"p-{uuid.uuid4().hex[:8]}",
        "description": "d",
        "trafficType": "HTTP",
        "volume": "low",
        "pattern": "steady",
        "packetSizeRange": [500, 1500],
        "errorRate": 0.0,
        "latency": 0,
        "attackType": None,
    }

    res = client.post("/simulation/profiles", json=profile, headers=auth_headers)
    assert res.status_code == 200
    created = res.json()
    assert created["name"] == profile["name"]
    profile_id = created["id"]

    res = client.get("/simulation/profiles", headers=auth_headers)
    assert res.status_code == 200
    assert any(p["id"] == profile_id for p in res.json())

    res = client.delete(f"/simulation/profiles/{profile_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == {"ok": True}

    res = client.delete(f"/simulation/profiles/{profile_id}", headers=auth_headers)
    assert res.status_code == 404


def test_agent_management_routes(client, auth_headers, backend_app_module, monkeypatch):
    stub = types.SimpleNamespace(
        get_status=lambda: {"running": False},
        start_agent=lambda: {"ok": True},
        stop_agent=lambda: {"ok": True},
    )
    monkeypatch.setattr(backend_app_module.agent_manager, "agent_manager", stub)

    res = client.get("/agent/status", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["running"] is False

    res = client.post("/agent/start", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["ok"] is True

    res = client.post("/agent/stop", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["ok"] is True
