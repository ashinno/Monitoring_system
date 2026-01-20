import types
import uuid
from datetime import datetime


def test_ml_train_endpoint_triggers_training(client, auth_headers, backend_app_module, monkeypatch):
    called = {"count": 0}

    def fake_train_model(logs):
        called["count"] += 1
        assert isinstance(logs, list)

    monkeypatch.setattr(backend_app_module.ml_engine, "train_model", fake_train_model)
    res = client.post("/ml/train", headers=auth_headers)
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

    monkeypatch.setattr(backend_app_module.ml_engine, "federated_aggregator", AggregatorStub())

    res = client.post("/ml/federated-update", json={"w": [1, 2, 3]}, headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "accepted"
    assert body["global_model_updated"] is True


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


def test_simulation_routes(client, auth_headers, backend_app_module, monkeypatch):
    class SimulatorStub:
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
                    "traffic_type": "HTTP",
                    "volume": "low",
                    "pattern": "steady",
                    "packet_size_range": [500, 1500],
                    "error_rate": 0.0,
                    "latency": 0,
                    "attack_type": None,
                },
                "stats": {"packets_generated": 0, "bytes_generated": 0, "errors_simulated": 0},
            }

    monkeypatch.setattr(backend_app_module, "simulator", SimulatorStub())

    res = client.post(
        "/simulation/start",
        json={"trafficType": "HTTP", "volume": "low", "pattern": "steady", "packetSizeRange": [500, 1500], "errorRate": 0.0, "latency": 0},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["isRunning"] is True

    res = client.get("/simulation/status", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["isRunning"] is True

    res = client.post("/simulation/stop", headers=auth_headers)
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
