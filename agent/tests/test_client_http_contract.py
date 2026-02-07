import types

import client as agent_client


class _TrainerStub:
    def __init__(self):
        self.last_round_id = None
        self.logs = []

    def add_log(self, entry):
        self.logs.append(entry)

    def train(self):
        return {"ok": True}

    def build_secure_update(self, **_kwargs):
        return {"round_id": "round-1", "masked_update": [0.1, 0.2, 0.3], "num_samples": 3}

    def build_mask_reveal(self):
        return {"round_id": "round-1", "mask": [0.01, 0.01, 0.01]}


def test_agent_login_success(monkeypatch):
    agent = agent_client.SentinelAgent()
    agent.base_url = "http://example.test"

    def fake_post(url, data=None, **_kwargs):
        assert url == "http://example.test/token"
        assert data["username"]
        assert data["password"]
        return types.SimpleNamespace(status_code=200, json=lambda: {"access_token": "t"})

    monkeypatch.setattr(agent_client.requests, "post", fake_post)
    assert agent.login() is True
    assert agent.token == "t"


def test_agent_fetch_settings_handles_camel_and_snake(monkeypatch):
    agent = agent_client.SentinelAgent()
    agent.base_url = "http://example.test"
    agent.token = "t"

    def fake_get(url, headers=None, **_kwargs):
        assert url == "http://example.test/settings"
        assert headers["Authorization"] == "Bearer t"
        return types.SimpleNamespace(status_code=200, json=lambda: {"screenTimeLimit": True, "screenTimeDurationMinutes": 5})

    monkeypatch.setattr(agent_client.requests, "get", fake_get)
    agent.fetch_settings()
    assert agent.settings["screenTimeLimit"] is True


def test_agent_send_log_encrypts_sensitive_fields(monkeypatch):
    agent = agent_client.SentinelAgent()
    agent.trainer = _TrainerStub()
    agent.base_url = "http://example.test"
    agent.token = "t"
    agent.ip_address = "127.0.0.1"

    captured = {}

    def fake_post(url, json=None, headers=None, **_kwargs):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return types.SimpleNamespace(status_code=200, text="ok")

    monkeypatch.setattr(agent_client.requests, "post", fake_post)
    agent.send_log("KEYLOG", "keystrokes", {"a": 1}, "INFO")

    assert captured["url"] == "http://example.test/logs"
    assert captured["headers"]["Authorization"] == "Bearer t"
    assert captured["json"]["description"].startswith("[ENCRYPTED] ")
    assert captured["json"]["details"].startswith("[ENCRYPTED] ")
    assert captured["json"]["activity_summary"] is not None
    assert len(agent.trainer.logs) == 1


def test_agent_secure_federated_flow(monkeypatch):
    agent = agent_client.SentinelAgent()
    agent.base_url = "http://example.test"
    agent.token = "t"
    agent.host_name = "host-a"
    agent.trainer = _TrainerStub()

    calls = {"post": [], "get": []}

    def fake_get(url, headers=None, timeout=None, **_kwargs):
        calls["get"].append((url, headers, timeout))
        if url.endswith("/ml/federated/rounds/start"):
            return types.SimpleNamespace(status_code=404, json=lambda: {})
        if "/ml/federated/rounds/" in url:
            return types.SimpleNamespace(status_code=404, json=lambda: {"detail": "not found"})
        return types.SimpleNamespace(status_code=200, json=lambda: {})

    def fake_post(url, json=None, headers=None, timeout=None, **_kwargs):
        calls["post"].append((url, json, headers, timeout))
        if url.endswith("/ml/federated/rounds/start"):
            return types.SimpleNamespace(status_code=200, json=lambda: {"round": {"round_id": "round-1", "min_clients": 1, "timeout_seconds": 300}})
        if url.endswith("/ml/federated-update"):
            return types.SimpleNamespace(status_code=200, text="ok", json=lambda: {"status": "accepted"})
        if url.endswith("/ml/federated/reveal-mask"):
            return types.SimpleNamespace(status_code=200, text="ok", json=lambda: {"status": "accepted"})
        return types.SimpleNamespace(status_code=200, text="ok", json=lambda: {})

    monkeypatch.setattr(agent_client.requests, "get", fake_get)
    monkeypatch.setattr(agent_client.requests, "post", fake_post)

    agent._send_federated_secure_update()

    post_urls = [c[0] for c in calls["post"]]
    assert "http://example.test/ml/federated/rounds/start" in post_urls
    assert "http://example.test/ml/federated-update" in post_urls
    assert "http://example.test/ml/federated/reveal-mask" in post_urls
