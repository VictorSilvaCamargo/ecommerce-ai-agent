import time
from abc import ABC, abstractmethod
from typing import Any


class IdempotencyStore(ABC):
    """Interface de controle de idempotência para recepção de webhooks."""

    @abstractmethod
    async def check_and_lock(self, message_id: str, ttl_seconds: int = 86400) -> bool:
        """Retorna True se a chave foi adquirida pela primeira vez (SETNX); False se já foi processada."""
        pass

    @abstractmethod
    async def release(self, message_id: str) -> None:
        """Libera a chave de idempotência caso o enfileiramento falhe antes de persistir."""
        pass


class InMemoryIdempotencyStore(IdempotencyStore):
    """Implementação em memória com controle de expiração (TTL) para testes e desenvolvimento local."""

    def __init__(self) -> None:
        self._locks: dict[str, float] = {}

    async def check_and_lock(self, message_id: str, ttl_seconds: int = 86400) -> bool:
        now = time.monotonic()
        key = f"webhook:idemp:{message_id}"
        expiry = self._locks.get(key)
        if expiry is not None and expiry > now:
            return False

        self._locks[key] = now + ttl_seconds
        return True

    async def release(self, message_id: str) -> None:
        key = f"webhook:idemp:{message_id}"
        self._locks.pop(key, None)


class RedisIdempotencyStore(IdempotencyStore):
    """Implementação em produção baseada em Redis SETNX com expiração atômica."""

    def __init__(self, redis_client: Any) -> None:
        self.redis = redis_client

    async def check_and_lock(self, message_id: str, ttl_seconds: int = 86400) -> bool:
        key = f"webhook:idemp:{message_id}"
        acquired = await self.redis.set(key, "1", nx=True, ex=ttl_seconds)
        return bool(acquired)

    async def release(self, message_id: str) -> None:
        key = f"webhook:idemp:{message_id}"
        await self.redis.delete(key)
