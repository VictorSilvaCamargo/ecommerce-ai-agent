import json
from collections.abc import AsyncGenerator

import pytest

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
from atendente.mcp_server.server import create_novaloja_mcp_server
from atendente.tools.service import NovaLojaToolsService


@pytest.fixture
async def mcp_tools_service() -> AsyncGenerator[NovaLojaToolsService, None]:
    db = DatabaseManager("sqlite+aiosqlite:///:memory:")
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with db.session_factory() as session:
        await seed_data(session)

    async with db.session_factory() as session:
        yield NovaLojaToolsService(
            customer_repo=CustomerRepository(session),
            order_repo=OrderRepository(session),
            refund_repo=RefundRepository(session),
            ticket_repo=TicketRepository(session),
            contract_repo=ContractRepository(session),
            invoice_repo=InvoiceRepository(session),
            audit_repo=InMemoryAuditRepository(),
        )
    await db.engine.dispose()


@pytest.mark.integration
async def test_mcp_server_exposes_all_8_tools_and_executes_calls(
    mcp_tools_service: NovaLojaToolsService,
) -> None:
    server = create_novaloja_mcp_server(mcp_tools_service)
    tools = await server.list_tools()
    tool_names = {t.name for t in tools}
    assert tool_names == {
        "identificar_cliente",
        "consultar_pedido",
        "solicitar_reembolso",
        "abrir_chamado",
        "consultar_contrato_sla",
        "consultar_fatura",
        "buscar_base_conhecimento",
        "transferir_para_humano",
    }

    # Testar identificar_cliente via protocolo MCP
    res_ident = await server.call_tool(
        "identificar_cliente",
        {"doc_number": "52998224725", "verification_code": "123456"},
    )
    assert res_ident.is_error is False
    text_block = res_ident.content[0].text  # type: ignore[union-attr]
    payload_ident = json.loads(text_block)
    assert payload_ident["success"] is True
    assert payload_ident["data"]["segment"] == "B2C"
    customer_id = payload_ident["data"]["id"]

    # Testar consultar_pedido via protocolo MCP
    res_order = await server.call_tool(
        "consultar_pedido",
        {"order_id": "ord_b2c_recent", "customer_id": customer_id},
    )
    assert res_order.is_error is False
    payload_order = json.loads(res_order.content[0].text)  # type: ignore[union-attr]
    assert payload_order["success"] is True
    assert payload_order["data"]["id"] == "ord_b2c_recent"

    # Testar consultar_contrato_sla via protocolo MCP (B2B)
    res_sla = await server.call_tool(
        "consultar_contrato_sla",
        {"customer_id": "cust_b2b_xpto"},
    )
    assert res_sla.is_error is False
    payload_sla = json.loads(res_sla.content[0].text)  # type: ignore[union-attr]
    assert payload_sla["success"] is True
    assert payload_sla["data"]["resolution_sla_hours"] == 4

    # Testar consultar_fatura via protocolo MCP (B2B)
    res_inv = await server.call_tool(
        "consultar_fatura",
        {"customer_id": "cust_b2b_xpto"},
    )
    assert res_inv.is_error is False
    payload_inv = json.loads(res_inv.content[0].text)  # type: ignore[union-attr]
    assert payload_inv["success"] is True
    assert len(payload_inv["data"]) >= 1

    # Testar abrir_chamado via protocolo MCP
    res_tkt = await server.call_tool(
        "abrir_chamado",
        {
            "customer_id": "cust_b2b_xpto",
            "titulo": "Incidente MCP",
            "descricao": "Teste de abertura de chamado via MCP",
            "prioridade": "HIGH",
        },
    )
    assert res_tkt.is_error is False
    payload_tkt = json.loads(res_tkt.content[0].text)  # type: ignore[union-attr]
    assert payload_tkt["success"] is True
    assert payload_tkt["data"]["title"] == "Incidente MCP"

    # Testar solicitar_reembolso via protocolo MCP (exige confirmado=True)
    res_ref = await server.call_tool(
        "solicitar_reembolso",
        {
            "order_id": "ord_b2c_recent",
            "customer_id": customer_id,
            "motivo": "Defeito constatado",
            "confirmado": True,
        },
    )
    assert res_ref.is_error is False
    payload_ref = json.loads(res_ref.content[0].text)  # type: ignore[union-attr]
    assert payload_ref["success"] is True

    # Testar buscar_base_conhecimento via protocolo MCP
    res_kb = await server.call_tool(
        "buscar_base_conhecimento",
        {"query": "politica de devolucao", "segmento": "B2C", "limit": 2},
    )
    assert res_kb.is_error is False

    # Testar transferir_para_humano via protocolo MCP
    res_handoff = await server.call_tool(
        "transferir_para_humano",
        {
            "customer_id": customer_id,
            "motivo": "Solicitacao de atendimento especializado via MCP",
            "resumo_conversa": "Cliente consultou pedido ord_b2c_recent e pediu especialista.",
        },
    )
    assert res_handoff.is_error is False
    payload_handoff = json.loads(res_handoff.content[0].text)  # type: ignore[union-attr]
    assert payload_handoff["success"] is True
    assert payload_handoff["data"]["status"] == "TRANSFERRED"
