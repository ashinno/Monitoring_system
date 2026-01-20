import statistics
import time
import uuid
from datetime import datetime
import os

import pytest


@pytest.mark.performance
def test_create_log_throughput_under_light_load(client, backend_app_module, monkeypatch):
    monkeypatch.setattr(backend_app_module.ml_engine, "predict_anomaly", lambda _: 1)
    monkeypatch.setattr(backend_app_module.notifications, "send_alert", lambda *_: None)

    class DummyTask:
        def delay(self, *_args, **_kwargs):
            return None

        def apply(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr(backend_app_module.tasks, "run_soar_automation", DummyTask())
    monkeypatch.setattr(backend_app_module.tasks, "run_prediction_analysis", DummyTask())

    class SioStub:
        async def emit(self, _event, _payload):
            return None

    monkeypatch.setattr(backend_app_module, "sio", SioStub())

    samples = []
    for _ in range(30):
        start = time.perf_counter()
        res = client.post(
            "/logs",
            json={
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "user": "perf",
                "activityType": "SYSTEM",
                "riskLevel": "INFO",
                "description": "ok",
                "details": "ok",
            },
        )
        assert res.status_code == 200
        samples.append((time.perf_counter() - start) * 1000.0)

    p95 = statistics.quantiles(samples, n=20)[18]
    threshold_ms = float(os.getenv("SENTINEL_P95_MS", "500.0"))
    assert p95 <= threshold_ms
