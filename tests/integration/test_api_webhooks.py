import json
import time

import pytest
from httpx import ASGITransport, AsyncClient

from atendente.api.main import app, dlq_store, idempotency_store
from atendente.infra.config import settings
from atendente.workers.security import compute_hmac_signature
from atendente.workers.tasks import DLQEntry


@pytest.mark.integration
async def test_webhook_valid_hmac_and_idempotency_deduplication() -> None:
    payload = {
        "message_id": "msg_wh_1001",
        "thread_id": "thr_wh_01",
        "customer_document": "52998224725",
        "channel": "whatsapp",
        "text": "Olá, gostaria de consultar meu pedido ord_b2c_recent",
    }
    raw_body = json.dumps(payload).encode("utf-8")
    now_ts = str(int(time.time()))
    sig = compute_hmac_signature(settings.webhook_secret, raw_body, timestamp=now_ts)

    await idempotency_store.release("msg_wh_1001")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start = time.perf_counter()
        resp1 = await client.post(
            "/webhook/messages",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": sig,
                "X-Webhook-Timestamp": now_ts,
            },
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert resp1.status_code == 202
        assert elapsed_ms < 200.0
        data1 = resp1.json()
        assert data1["status"] == "queued"
        assert data1["message_id"] == "msg_wh_1001"

        # Enviar exatamente o mesmo evento novamente (duplicata) -> 200 duplicate_ignored
        resp2 = await client.post(
            "/webhook/messages",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": sig,
                "X-Webhook-Timestamp": now_ts,
            },
        )
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "duplicate_ignored"


@pytest.mark.integration
async def test_webhook_rejects_invalid_hmac_and_replay_attack() -> None:
    payload = {
        "message_id": "msg_wh_attack_01",
        "thread_id": "thr_wh_02",
        "text": "Tentativa de spoofing sem assinatura válida",
    }
    raw_body = json.dumps(payload).encode("utf-8")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Assinatura forjada
        resp_bad_sig = await client.post(
            "/webhook/messages",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": "sha256=0000000000000000000000000000000000000000000000000000000000000000",
            },
        )
        assert resp_bad_sig.status_code == 401

        # 2. Replay attack com timestamp de 1 hora atrás
        old_ts = str(int(time.time()) - 3600)
        old_sig = compute_hmac_signature(settings.webhook_secret, raw_body, timestamp=old_ts)
        resp_replay = await client.post(
            "/webhook/messages",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": old_sig,
                "X-Webhook-Timestamp": old_ts,
            },
        )
        assert resp_replay.status_code == 401


@pytest.mark.integration
async def test_webhook_dlq_inspection_endpoint() -> None:
    await dlq_store.push(
        DLQEntry(
            message_id="msg_dlq_99",
            thread_id="thr_dlq_99",
            payload={"message_id": "msg_dlq_99", "text": "Falha simulada"},
            error_reason="Max retries exceeded",
            attempts=3,
        )
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/webhook/dlq",
            headers={"X-API-Key": settings.api_key},
        )
        assert resp.status_code == 200
        items = resp.json()
        assert any(item["message_id"] == "msg_dlq_99" for item in items)
