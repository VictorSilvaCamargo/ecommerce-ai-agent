from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import BaseModel, Field


class ToolAuditEntry(BaseModel):
    id: str = Field(default_factory=lambda: f"aud_{uuid4().hex[:12]}")
    tool_name: str
    customer_id: Optional[str] = None
    input_payload: dict[str, Any]
    output_payload: Optional[Any] = None
    error: Optional[dict[str, Any]] = None
    latency_ms: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditRepository(ABC):
    @abstractmethod
    async def log_tool_execution(self, entry: ToolAuditEntry) -> None:
        """Registra a execução de uma ferramenta na trilha de auditoria."""
        pass

    @abstractmethod
    async def get_logs_by_customer(self, customer_id: str) -> list[ToolAuditEntry]:
        """Recupera logs de ferramentas associados a um cliente."""
        pass


class InMemoryAuditRepository(AuditRepository):
    """Implementação em memória para testes rápidos e execução desconectada."""

    def __init__(self) -> None:
        self.entries: list[ToolAuditEntry] = []

    async def log_tool_execution(self, entry: ToolAuditEntry) -> None:
        self.entries.append(entry)

    async def get_logs_by_customer(self, customer_id: str) -> list[ToolAuditEntry]:
        return [e for e in self.entries if e.customer_id == customer_id]


class MongoAuditRepository(AuditRepository):
    """Implementação oficial de persistência de auditoria no MongoDB."""

    def __init__(self, mongo_uri: str, database_name: str = "novaloja_audit"):
        self.client: AsyncIOMotorClient[dict[str, Any]] = AsyncIOMotorClient(mongo_uri)
        self.db: AsyncIOMotorDatabase[dict[str, Any]] = self.client[database_name]
        self.collection = self.db["tool_audit_logs"]

    async def log_tool_execution(self, entry: ToolAuditEntry) -> None:
        doc = entry.model_dump()
        doc["_id"] = entry.id
        await self.collection.insert_one(doc)

    async def get_logs_by_customer(self, customer_id: str) -> list[ToolAuditEntry]:
        cursor = self.collection.find({"customer_id": customer_id}).sort("timestamp", -1)
        results = await cursor.to_list(length=100)
        return [ToolAuditEntry(**{k: v for k, v in doc.items() if k != "_id"}) for doc in results]
