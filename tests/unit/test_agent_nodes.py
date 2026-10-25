from collections.abc import AsyncGenerator

import pytest

from atendente.agent.nodes import AgentNodeHandler
from atendente.agent.state import ConversationState
from atendente.infra.audit import InMemoryAuditRepository
from atendente.infra.db.database import DatabaseManager
from atendente.infra.db.models import Base
from atendente.infra.db.repositories import (
    ContractRepository,
    CustomerRepository,
    InvoiceRepository,
    OrderRepository,
    RefundRepository,
    TicketRepository,
)
from atendente.infra.db.seed import seed_data
from atendente.tools.service import NovaLojaToolsService


@pytest.fixture
async def tools_service() -> AsyncGenerator[NovaLojaToolsService, None]:
    db = DatabaseManager(db_url="sqlite+aiosqlite:///:memory:")
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with db.session_factory() as session:
        await seed_data(session)
        audit_repo = InMemoryAuditRepository()
        yield NovaLojaToolsService(
            customer_repo=CustomerRepository(session),
            order_repo=OrderRepository(session),
            refund_repo=RefundRepository(session),
            ticket_repo=TicketRepository(session),
            contract_repo=ContractRepository(session),
            invoice_repo=InvoiceRepository(session),
            audit_repo=audit_repo,
        )

    await db.engine.dispose()


@pytest.fixture
def node_handler(tools_service: NovaLojaToolsService) -> AgentNodeHandler:
    return AgentNodeHandler(tools_service=tools_service)


@pytest.mark.unit
async def test_node_identify_b2c(node_handler: AgentNodeHandler) -> None:
    # Maria Silva CPF 529.982.247-25
    state = ConversationState(messages=[{"role": "user", "content": "Olá, meu CPF é 52998224725"}])
    update = await node_handler.identify(state)
    assert update["customer_document"] == "52998224725"
    assert update["customer_segment"] == "B2C"
    assert update["authenticated"] is True
    assert update["customer_id"] == "cust_b2c_maria"


@pytest.mark.unit
async def test_node_identify_b2b(node_handler: AgentNodeHandler) -> None:
    # XPTO CNPJ 11.222.333/0001-81
    state = ConversationState(
        messages=[{"role": "user", "content": "Represento a empresa, CNPJ 11222333000181"}]
    )
    update = await node_handler.identify(state)
    assert update["customer_document"] == "11222333000181"
    assert update["customer_segment"] == "B2B"
    assert update["authenticated"] is True
    assert update["customer_id"] == "cust_b2b_xpto"


@pytest.mark.unit
async def test_node_classify_intent(node_handler: AgentNodeHandler) -> None:
    state_pedido = ConversationState(
        messages=[{"role": "user", "content": "Quero saber do pedido PED-12345"}]
    )
    up1 = await node_handler.classify_intent(state_pedido)
    assert up1["active_intent"] == "consultar_pedido"

    state_reembolso = ConversationState(
        messages=[{"role": "user", "content": "Quero meu dinheiro de volta, estorno imediato"}]
    )
    up2 = await node_handler.classify_intent(state_reembolso)
    assert up2["active_intent"] == "solicitar_reembolso"

    state_humano = ConversationState(
        messages=[{"role": "user", "content": "Quero falar com um atendente humano"}]
    )
    up3 = await node_handler.classify_intent(state_humano)
    assert up3["active_intent"] == "falar_com_atendente"


@pytest.mark.unit
async def test_node_confirm_action_blocks_unconfirmed_sensitive_action(
    node_handler: AgentNodeHandler,
) -> None:
    state = ConversationState(
        customer_id="cust_b2c_maria",
        active_intent="solicitar_reembolso",
        pending_action={
            "tool_name": "solicitar_reembolso",
            "parameters": {
                "order_id": "ord_b2c_recent",
                "customer_id": "cust_b2c_maria",
                "reason": "Defeito",
            },
        },
        action_confirmed=False,
        messages=[{"role": "user", "content": "Quero reembolso"}],
    )
    update = await node_handler.confirm_action(state)
    assert update["action_confirmed"] is False
    assert "Confirmação" in update["last_response"]
    assert update["last_tool_result"] is None


@pytest.mark.unit
async def test_node_confirm_action_executes_when_confirmed(node_handler: AgentNodeHandler) -> None:
    state = ConversationState(
        customer_id="cust_b2c_maria",
        active_intent="confirmar_acao",
        pending_action={
            "tool_name": "solicitar_reembolso",
            "parameters": {
                "order_id": "ord_b2c_recent",
                "customer_id": "cust_b2c_maria",
                "reason": "Defeito",
            },
        },
        action_confirmed=False,
        messages=[{"role": "user", "content": "Sim, eu confirmo"}],
    )
    update = await node_handler.confirm_action(state)
    assert update["action_confirmed"] is True
    assert update["last_tool_result"] is not None
    assert update["pending_action"] is None


@pytest.mark.unit
async def test_node_evaluate_handoff_on_three_unresolved_turns(
    node_handler: AgentNodeHandler,
) -> None:
    state = ConversationState(
        customer_id="cust_b2c_maria",
        consecutive_unresolved_turns=3,
        messages=[{"role": "user", "content": "Ainda não resolveu nada!"}],
    )
    update = await node_handler.evaluate_handoff(state)
    assert update["handoff_requested"] is True
    assert (
        "tentativas" in update["handoff_reason"].lower()
        or "limite" in update["handoff_reason"].lower()
    )


@pytest.mark.unit
async def test_node_summarize_history(node_handler: AgentNodeHandler) -> None:
    messages = [{"role": "user", "content": f"Mensagem número {i}"} for i in range(12)]
    state = ConversationState(messages=messages)
    update = await node_handler.summarize_history(state)
    assert len(update["messages"]) <= 4
    assert update["summary"] is not None
    assert "Mensagem número" in update["summary"]
