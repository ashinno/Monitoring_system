import types

import client as agent_client


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

