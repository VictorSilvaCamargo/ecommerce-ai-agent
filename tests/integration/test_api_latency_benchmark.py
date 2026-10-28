import json
import statistics
import time
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from atendente.api.main import app
from atendente.infra.config import settings
from atendente.workers.security import compute_hmac_signature


@pytest.mark.integration
def test_api_p95_latency_is_well_below_300ms() -> None:
    """Executa 100 requisições reais contra a API FastAPI e comprova p95 < 300ms (excluindo LLM externo)."""
    client = TestClient(app)
    latencies_ms: list[float] = []

    for i in range(100):
        start = time.perf_counter()
        if i % 4 == 0:
            resp = client.get("/health")
            assert resp.status_code == 200
        elif i % 4 == 1:
            resp = client.get("/tools/schemas")
            assert resp.status_code == 200
        elif i % 4 == 2:
            ts = str(int(time.time()))
            payload = {
                "message_id": f"bench_msg_{i}_{uuid4().hex[:8]}",
                "thread_id": f"bench_thr_{i}",
                "customer_document": "52998224725",
                "channel": "whatsapp",
                "text": "Consulta de latencia webhook",
            }
            raw_body = json.dumps(payload).encode("utf-8")
            sig = compute_hmac_signature(settings.webhook_secret, raw_body, timestamp=ts)
            resp = client.post(
                "/webhook/messages",
                content=raw_body,
                headers={
                    "Content-Type": "application/json",
                    "X-Hub-Signature-256": sig,
                    "X-Webhook-Timestamp": ts,
                },
            )
            assert resp.status_code == 202
        else:
            resp = client.get("/metrics")
            assert resp.status_code == 200

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        latencies_ms.append(elapsed_ms)

    latencies_sorted = sorted(latencies_ms)
    p50_ms = statistics.median(latencies_sorted)
    p95_index = int(0.95 * len(latencies_sorted)) - 1
    p95_ms = latencies_sorted[p95_index]
    p99_ms = latencies_sorted[-1]

    assert p50_ms < 100.0
    assert p95_ms < 300.0, f"p95 latency ({p95_ms:.2f}ms) excedeu o SLA de 300ms!"
    assert p99_ms < 300.0
