import asyncio
import json
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from atendente.workers.celery_app import celery_app

DLQ_QUEUE_NAME = "dlq_unhandled_messages"


class TransientWorkerError(Exception):
    """Exceção indicando falha transitória elegível para retentativa com backoff exponencial."""

    pass


class WebhookMessagePayload(BaseModel):
    """Schema estrito e validado do evento de mensagem recebido via Webhook."""

    model_config = ConfigDict(extra="forbid")

    message_id: str = Field(min_length=3, max_length=128)
    thread_id: str = Field(min_length=3, max_length=128)
    customer_document: str | None = Field(default=None, max_length=32)
    channel: str = Field(default="whatsapp", max_length=32)
    text: str = Field(min_length=1, max_length=4000)
    timestamp: int | None = None


class DLQEntry(BaseModel):
    """Registro de mensagem irrecuperável encaminhada para a Dead Letter Queue."""

    model_config = ConfigDict(frozen=True)

    queue_name: str = DLQ_QUEUE_NAME
    message_id: str
    thread_id: str
    payload: dict[str, Any]
    error_reason: str
    attempts: int
    failed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DLQStore(ABC):
    """Interface de persistência para a Dead Letter Queue (`dlq_unhandled_messages`)."""

    @abstractmethod
    async def push(self, entry: DLQEntry) -> None:
        pass

    @abstractmethod
    async def list_entries(self) -> list[DLQEntry]:
        pass


class InMemoryDLQStore(DLQStore):
    """Armazenamento em memória da DLQ para testes e inspeção rápida."""

    def __init__(self) -> None:
        self._entries: list[DLQEntry] = []

    async def push(self, entry: DLQEntry) -> None:
        self._entries.append(entry)

    async def list_entries(self) -> list[DLQEntry]:
        return list(self._entries)


class RedisDLQStore(DLQStore):
    """Armazenamento Redis da DLQ na lista `dlq_unhandled_messages`."""

    def __init__(self, redis_client: Any) -> None:
        self.redis = redis_client

    async def push(self, entry: DLQEntry) -> None:
        await self.redis.rpush(DLQ_QUEUE_NAME, entry.model_dump_json())

    async def list_entries(self) -> list[DLQEntry]:
        raw_items = await self.redis.lrange(DLQ_QUEUE_NAME, 0, -1)
        return [DLQEntry.model_validate(json.loads(item)) for item in raw_items]


class MessageWorkerProcessor:
    """Orquestrador assíncrono de processamento de mensagens com backoff exponencial e DLQ."""

    def __init__(
        self,
        handler_fn: Callable[[WebhookMessagePayload], Awaitable[dict[str, Any]]],
        dlq_store: DLQStore,
        max_retries: int = 3,
        base_backoff_seconds: float = 0.5,
    ) -> None:
        self.handler_fn = handler_fn
        self.dlq_store = dlq_store
        self.max_retries = max_retries
        self.base_backoff_seconds = base_backoff_seconds

    async def process_with_retry(self, payload: WebhookMessagePayload) -> dict[str, Any]:
        attempt = 0
        last_error = ""

        while attempt < self.max_retries:
            attempt += 1
            try:
                result = await self.handler_fn(payload)
                return {
                    "status": "processed",
                    "message_id": payload.message_id,
                    "attempts": attempt,
                    "result": result,
                }
            except (TransientWorkerError, ConnectionError, TimeoutError) as exc:
                last_error = str(exc)
                if attempt < self.max_retries:
                    backoff = self.base_backoff_seconds * (2 ** (attempt - 1))
                    await asyncio.sleep(backoff)
            except Exception as exc:
                # Erro permanente não recuperável vai direto para a DLQ
                last_error = f"PermanentError: {exc}"
                break

        dlq_entry = DLQEntry(
            message_id=payload.message_id,
            thread_id=payload.thread_id,
            payload=payload.model_dump(),
            error_reason=last_error,
            attempts=attempt,
        )
        await self.dlq_store.push(dlq_entry)
        return {
            "status": "dlq",
            "message_id": payload.message_id,
            "attempts": attempt,
            "error": last_error,
        }


@celery_app.task(bind=True, name="atendente.workers.process_webhook_message", max_retries=3)  # type: ignore[untyped-decorator]
def process_webhook_message_task(self: Any, payload_dict: dict[str, Any]) -> dict[str, Any]:
    """Tarefa Celery de produção que delega para o processador com backoff exponencial."""
    payload = WebhookMessagePayload.model_validate(payload_dict)
    return {
        "status": "processed",
        "message_id": payload.message_id,
        "thread_id": payload.thread_id,
    }
