import time

import pytest

from atendente.workers.idempotency import InMemoryIdempotencyStore
from atendente.workers.security import compute_hmac_signature, verify_webhook_hmac
from atendente.workers.tasks import (
    InMemoryDLQStore,
    MessageWorkerProcessor,
    TransientWorkerError,
    WebhookMessagePayload,
)


@pytest.mark.unit
def test_hmac_signature_verification_and_tampering_defense() -> None:
    secret = "test-webhook-secret-key-32-bytes"
    raw_body = b'{"message_id": "msg_01", "text": "Ola"}'
    now_ts = str(int(time.time()))

    valid_sig = compute_hmac_signature(secret, raw_body, timestamp=now_ts)
    assert valid_sig.startswith("sha256=")

    # Assinatura válida dentro da janela de tempo
    assert (
        verify_webhook_hmac(
            secret=secret,
            signature_header=valid_sig,
            raw_body=raw_body,
            timestamp_header=now_ts,
        )
        is True
    )

    # Corpo adulterado (Tampering) -> deve falhar
    tampered_body = b'{"message_id": "msg_01", "text": "Transferir R$ 10000"}'
    assert (
        verify_webhook_hmac(
            secret=secret,
            signature_header=valid_sig,
            raw_body=tampered_body,
            timestamp_header=now_ts,
        )
        is False
    )

    # Replay Attack (timestamp expirado há 10 minutos, limite 300s) -> deve falhar
    expired_ts = str(int(time.time()) - 600)
    expired_sig = compute_hmac_signature(secret, raw_body, timestamp=expired_ts)
    assert (
        verify_webhook_hmac(
            secret=secret,
            signature_header=expired_sig,
            raw_body=raw_body,
            timestamp_header=expired_ts,
            max_age_seconds=300,
        )
        is False
    )


@pytest.mark.unit
async def test_idempotency_store_blocks_duplicates() -> None:
    store = InMemoryIdempotencyStore()
    first = await store.check_and_lock("msg_unique_123", ttl_seconds=60)
    second = await store.check_and_lock("msg_unique_123", ttl_seconds=60)

    assert first is True
    assert second is False

    # Após release (ex: falha antes de enfileirar), pode ser adquirido novamente
    await store.release("msg_unique_123")
    third = await store.check_and_lock("msg_unique_123", ttl_seconds=60)
    assert third is True


@pytest.mark.unit
async def test_worker_retries_with_exponential_backoff_and_succeeds() -> None:
    dlq = InMemoryDLQStore()
    call_count = 0

    async def flaky_handler(payload: WebhookMessagePayload) -> dict[str, str]:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TransientWorkerError(f"Falha transitória de rede na tentativa {call_count}")
        return {"response": f"Processado com sucesso na tentativa {call_count}"}

    processor = MessageWorkerProcessor(
        handler_fn=flaky_handler,
        dlq_store=dlq,
        max_retries=3,
        base_backoff_seconds=0.001,
    )

    payload = WebhookMessagePayload(
        message_id="msg_retry_ok",
        thread_id="thr_01",
        text="Qual o status do meu pedido?",
    )
    result = await processor.process_with_retry(payload)

    assert result["status"] == "processed"
    assert result["attempts"] == 3
    assert call_count == 3
    assert len(await dlq.list_entries()) == 0


@pytest.mark.unit
async def test_worker_exhausts_retries_and_routes_to_dlq() -> None:
    dlq = InMemoryDLQStore()
    call_count = 0

    async def always_failing_handler(payload: WebhookMessagePayload) -> dict[str, str]:
        nonlocal call_count
        call_count += 1
        raise TransientWorkerError("Banco de dados indisponível permanentemente")

    processor = MessageWorkerProcessor(
        handler_fn=always_failing_handler,
        dlq_store=dlq,
        max_retries=3,
        base_backoff_seconds=0.001,
    )

    payload = WebhookMessagePayload(
        message_id="msg_dead_letter",
        thread_id="thr_02",
        text="Mensagem que vai para a DLQ",
    )
    result = await processor.process_with_retry(payload)

    assert result["status"] == "dlq"
    assert result["attempts"] == 3
    assert call_count == 3

    entries = await dlq.list_entries()
    assert len(entries) == 1
    assert entries[0].message_id == "msg_dead_letter"
    assert entries[0].queue_name == "dlq_unhandled_messages"
    assert "indisponível" in entries[0].error_reason
