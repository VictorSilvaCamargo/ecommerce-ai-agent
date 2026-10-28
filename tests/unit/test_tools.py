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
from atendente.tools.service import (
    AbrirChamadoInput,
    BuscarBaseConhecimentoInput,
    ConsultarContratoSLAInput,
    ConsultarFaturaInput,
    ConsultarPedidoInput,
    IdentificarClienteInput,
    NovaLojaToolsService,
    SolicitarReembolsoInput,
    TransferirParaHumanoInput,
)


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


@pytest.mark.unit
async def test_identificar_cliente_success(tools_service: NovaLojaToolsService) -> None:
    res = await tools_service.identificar_cliente(
        IdentificarClienteInput(doc_number="529.982.247-25", verification_code="123456")
    )
    assert res.success is True
    assert res.data is not None
    assert res.data.name == "Maria Silva"
    assert res.data.id == "cust_b2c_maria"


@pytest.mark.unit
async def test_identificar_cliente_invalid_code(tools_service: NovaLojaToolsService) -> None:
    res = await tools_service.identificar_cliente(
        IdentificarClienteInput(doc_number="529.982.247-25", verification_code="12")
    )
    assert res.success is False
    assert res.error is not None
    assert res.error.code == "INVALID_VERIFICATION_CODE"


@pytest.mark.unit
async def test_consultar_pedido_success(tools_service: NovaLojaToolsService) -> None:
    res = await tools_service.consultar_pedido(
        ConsultarPedidoInput(order_id="ord_b2c_recent", customer_id="cust_b2c_maria")
    )
    assert res.success is True
    assert res.data is not None
    assert res.data.total_cents == 49900
    assert len(res.data.items) == 1


@pytest.mark.unit
async def test_consultar_pedido_unauthorized(tools_service: NovaLojaToolsService) -> None:
    res = await tools_service.consultar_pedido(
        ConsultarPedidoInput(order_id="ord_b2c_recent", customer_id="cust_b2b_xpto")
    )
    assert res.success is False
    assert res.error is not None
    assert res.error.code == "UNAUTHORIZED_ACCESS"


@pytest.mark.unit
async def test_solicitar_reembolso_sensitive_action_requires_confirmation(
    tools_service: NovaLojaToolsService,
) -> None:
    # Passo 1: Solicitação SEM confirmação -> Deve retornar erro CONFIRMATION_REQUIRED com detalhes
    res = await tools_service.solicitar_reembolso(
        SolicitarReembolsoInput(
            order_id="ord_b2c_recent",
            customer_id="cust_b2c_maria",
            motivo="Produto veio com defeito",
            confirmado=False,
        )
    )
    assert res.success is False
    assert res.error is not None
    assert res.error.code == "CONFIRMATION_REQUIRED"
    assert res.error.details["eligible"] is True
    assert res.error.details["amount_cents"] == 49900


@pytest.mark.unit
async def test_solicitar_reembolso_sensitive_action_approved_when_confirmed(
    tools_service: NovaLojaToolsService,
) -> None:
    # Passo 2: Solicitação COM confirmação -> Deve aprovar e persistir o reembolso
    res = await tools_service.solicitar_reembolso(
        SolicitarReembolsoInput(
            order_id="ord_b2c_recent",
            customer_id="cust_b2c_maria",
            motivo="Produto veio com defeito",
            confirmado=True,
        )
    )
    assert res.success is True
    assert res.data is not None
    assert res.data.status.value == "APPROVED"
    assert res.data.amount_cents == 49900


@pytest.mark.unit
async def test_solicitar_reembolso_ineligible_order(tools_service: NovaLojaToolsService) -> None:
    # Pedido antigo (20 dias de entregue) -> Não elegível mesmo se confirmado
    res = await tools_service.solicitar_reembolso(
        SolicitarReembolsoInput(
            order_id="ord_b2c_old",
            customer_id="cust_b2c_maria",
            motivo="Arrependimento",
            confirmado=True,
        )
    )
    assert res.success is False
    assert res.error is not None
    assert res.error.code == "INELIGIBLE_REFUND"


@pytest.mark.unit
async def test_abrir_chamado_b2b_calculates_platinum_sla(
    tools_service: NovaLojaToolsService,
) -> None:
    res = await tools_service.abrir_chamado(
        AbrirChamadoInput(
            customer_id="cust_b2b_xpto",
            titulo="Instabilidade na integração",
            descricao="Webhooks não estão respondendo",
            prioridade="CRITICAL",
        )
    )
    assert res.success is True
    assert res.data is not None
    # Cliente Platinum com prioridade CRITICAL tem SLA de 2 horas
    assert res.data.sla_hours == 2


@pytest.mark.unit
async def test_abrir_chamado_b2c_calculates_default_sla(
    tools_service: NovaLojaToolsService,
) -> None:
    res = await tools_service.abrir_chamado(
        AbrirChamadoInput(
            customer_id="cust_b2c_maria",
            titulo="Dúvida sobre entrega",
            descricao="Gostaria de saber o prazo exato",
            prioridade="MEDIUM",
        )
    )
    assert res.success is True
    assert res.data is not None
    # Cliente B2C com prioridade MEDIUM tem SLA de 48 horas
    assert res.data.sla_hours == 48


@pytest.mark.unit
async def test_consultar_contrato_sla_success_for_b2b(tools_service: NovaLojaToolsService) -> None:
    res = await tools_service.consultar_contrato_sla(
        ConsultarContratoSLAInput(customer_id="cust_b2b_xpto")
    )
    assert res.success is True
    assert res.data is not None
    assert res.data.tier.value == "PLATINUM"
    assert res.data.account_manager == "Roberto Santos"


@pytest.mark.unit
async def test_consultar_contrato_sla_rejected_for_b2c(tools_service: NovaLojaToolsService) -> None:
    res = await tools_service.consultar_contrato_sla(
        ConsultarContratoSLAInput(customer_id="cust_b2c_maria")
    )
    assert res.success is False
    assert res.error is not None
    assert res.error.code == "NOT_B2B_CUSTOMER"


@pytest.mark.unit
async def test_consultar_fatura(tools_service: NovaLojaToolsService) -> None:
    res = await tools_service.consultar_fatura(ConsultarFaturaInput(customer_id="cust_b2b_xpto"))
    assert res.success is True
    assert res.data is not None
    assert len(res.data) == 2


@pytest.mark.unit
async def test_buscar_base_conhecimento(tools_service: NovaLojaToolsService) -> None:
    res = await tools_service.buscar_base_conhecimento(
        BuscarBaseConhecimentoInput(query="como funciona a devolução?", segmento="B2C")
    )
    assert res.success is True
    assert res.data is not None
    assert len(res.data) >= 1
    assert "Política de Trocas" in res.data[0]["title"]


@pytest.mark.unit
async def test_buscar_base_conhecimento_with_retriever_and_abstention(
    tools_service: NovaLojaToolsService,
) -> None:
    from pathlib import Path

    from atendente.rag.chunker import ChunkingConfig, chunk_directory
    from atendente.rag.embeddings import DeterministicEmbeddingService
    from atendente.rag.retriever import HybridRetriever
    from atendente.rag.store import InMemoryVectorStore

    chunks = chunk_directory(Path("data/kb"), ChunkingConfig(target_tokens=512, overlap_tokens=64))
    emb_service = DeterministicEmbeddingService(dimension=384)
    chunks_with_emb = [
        chk.model_copy(update={"embedding": emb_service.embed_text(chk.content)}) for chk in chunks
    ]
    store = InMemoryVectorStore()
    await store.add_chunks(chunks_with_emb)

    retriever = HybridRetriever(
        vector_store=store, embedding_service=emb_service, relevance_threshold=0.012
    )
    tools_service.retriever = retriever

    # 1. Consulta com sucesso
    res = await tools_service.buscar_base_conhecimento(
        BuscarBaseConhecimentoInput(
            query="quais são os níveis de SLA do contrato B2B?", segmento="B2B"
        )
    )
    assert res.success is True
    assert res.data is not None
    assert len(res.data) >= 1
    assert any("SLA" in x["title"] for x in res.data)

    # 2. Consulta desconexa (abstenção)
    res_abstain = await tools_service.buscar_base_conhecimento(
        BuscarBaseConhecimentoInput(
            query="qual é a receita de bolo de fubá com goiabada?", segmento="B2B"
        )
    )
    assert res_abstain.success is False
    assert res_abstain.error is not None
    assert res_abstain.error.code == "NO_RELEVANT_KNOWLEDGE"
    assert res_abstain.error.details["abstained"] is True


@pytest.mark.unit
async def test_transferir_para_humano(tools_service: NovaLojaToolsService) -> None:
    res = await tools_service.transferir_para_humano(
        TransferirParaHumanoInput(
            customer_id="cust_b2c_maria",
            motivo="Cliente insatisfeito com resposta automática",
            resumo_conversa="Cliente perguntou sobre reembolso e pediu atendente humano.",
        )
    )
    assert res.success is True
    assert res.data is not None
    assert "protocolo" in res.data
    assert res.data["status"] == "TRANSFERRED"


@pytest.mark.unit
async def test_audit_log_recorded_for_every_tool(tools_service: NovaLojaToolsService) -> None:
    audit_repo = tools_service.audit_repo
    assert isinstance(audit_repo, InMemoryAuditRepository)

    # Executa duas tools
    await tools_service.identificar_cliente(
        IdentificarClienteInput(doc_number="52998224725", verification_code="123456")
    )
    await tools_service.consultar_pedido(
        ConsultarPedidoInput(order_id="ord_b2c_recent", customer_id="cust_b2c_maria")
    )

    customer_logs = await audit_repo.get_logs_by_customer("cust_b2c_maria")
    assert len(customer_logs) >= 2
    assert any(log.tool_name == "identificar_cliente" for log in customer_logs)
    assert any(log.tool_name == "consultar_pedido" for log in customer_logs)
