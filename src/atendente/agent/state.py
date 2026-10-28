from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CustomerSegmentType = Literal["B2C", "B2B", "INDEFINIDO"]


class ConversationState(BaseModel):
    """Estado tipado da conversação gerenciada pelo LangGraph.

    Mantém o histórico de mensagens, identificação e autenticação do cliente,
    intenção ativa, pendências de ferramentas sensíveis, documentos RAG recuperados,
    contadores de falhas para handoff e sumarização periódica.
    """

    model_config = ConfigDict(extra="ignore")

    customer_id: str | None = None
    customer_document: str | None = None
    customer_segment: CustomerSegmentType = "INDEFINIDO"
    authenticated: bool = False
    channel: str = "web"
    messages: list[dict[str, Any]] = Field(default_factory=list)
    active_intent: str | None = None
    pending_action: dict[str, Any] | None = None
    action_confirmed: bool = False
    retrieved_docs: list[dict[str, Any]] = Field(default_factory=list)
    handoff_requested: bool = False
    handoff_reason: str | None = None

    # Campos de controle de loop, frustração e sumarização
    consecutive_unresolved_turns: int = 0
    frustration_detected: bool = False
    summary: str | None = None
    last_tool_result: dict[str, Any] | None = None
    last_response: str | None = None
