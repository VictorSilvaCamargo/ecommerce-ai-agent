from collections.abc import AsyncGenerator
from pathlib import Path

import pytest

from atendente.agent.graph import build_conversation_graph
from atendente.agent.nodes import AgentNodeHandler
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
from atendente.rag.chunker import ChunkingConfig, chunk_directory
from atendente.rag.embeddings import DeterministicEmbeddingService
from atendente.rag.retriever import HybridRetriever
from atendente.rag.store import InMemoryVectorStore
from atendente.tools.service import NovaLojaToolsService


@pytest.fixture
async def tools_service_with_rag() -> AsyncGenerator[NovaLojaToolsService, None]:
    db = DatabaseManager(db_url="sqlite+aiosqlite:///:memory:")
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Ingestão RAG de teste
    chunks = chunk_directory(Path("data/kb"), ChunkingConfig(target_tokens=512, overlap_tokens=64))
    embedder = DeterministicEmbeddingService(dimension=384)
    chunks_with_emb = [
        chk.model_copy(update={"embedding": embedder.embed_text(chk.content)}) for chk in chunks
    ]
    vector_store = InMemoryVectorStore()
    await vector_store.add_chunks(chunks_with_emb)
    retriever = HybridRetriever(
        vector_store=vector_store, embedding_service=embedder, relevance_threshold=0.012
    )

    async with db.session_factory() as session:
        await seed_data(session)
        audit_repo = InMemoryAuditRepository()
        service = NovaLojaToolsService(
            customer_repo=CustomerRepository(session),
            order_repo=OrderRepository(session),
            refund_repo=RefundRepository(session),
            ticket_repo=TicketRepository(session),
            contract_repo=ContractRepository(session),
            invoice_repo=InvoiceRepository(session),
            audit_repo=audit_repo,
            retriever=retriever,
        )
        yield service

    await db.engine.dispose()


@pytest.mark.asyncio
async def test_b2c_journey_order_and_refund_with_confirmation(
    tools_service_with_rag: NovaLojaToolsService,
) -> None:
    handler = AgentNodeHandler(
        tools_service=tools_service_with_rag,
        retriever=tools_service_with_rag.retriever,
    )
    graph = build_conversation_graph(handler)
    thread_config = {"configurable": {"thread_id": "session-b2c-1"}}

    # Turno 1: Identificação e consulta de pedido
    input_1 = {
        "messages": [
            {
                "role": "user",
                "content": "Olá, meu CPF é 52998224725 e quero saber do pedido ord_b2c_recent",
            }
        ]
    }
    state_1 = await graph.ainvoke(input_1, config=thread_config)
    assert state_1["customer_id"] == "cust_b2c_maria"
    assert state_1["customer_segment"] == "B2C"
    assert state_1["authenticated"] is True
    assert "NL887766554BR" in state_1["last_response"]

    # Turno 2: Solicitação de reembolso (ação sensível) -> deve ser bloqueada para confirmação
    input_2 = {
        "messages": [
            *state_1["messages"],
            {
                "role": "user",
                "content": "Quero solicitar o reembolso do pedido ord_b2c_recent porque veio com defeito",
            },
        ]
    }
    state_2 = await graph.ainvoke(input_2, config=thread_config)
    assert state_2["action_confirmed"] is False
    assert state_2["pending_action"] is not None
    assert "Confirmação" in state_2["last_response"]

    # Turno 3: Usuário confirma explicitamente
    input_3 = {
        "messages": [
            *state_2["messages"],
            {"role": "user", "content": "Sim, confirmo a solicitação de reembolso"},
        ]
    }
    state_3 = await graph.ainvoke(input_3, config=thread_config)
    assert state_3["action_confirmed"] is True
    assert state_3["pending_action"] is None
    assert "reembolso" in state_3["last_response"].lower()
    assert state_3["last_tool_result"]["success"] is True


@pytest.mark.asyncio
async def test_b2b_journey_sla_contract(tools_service_with_rag: NovaLojaToolsService) -> None:
    handler = AgentNodeHandler(
        tools_service=tools_service_with_rag,
        retriever=tools_service_with_rag.retriever,
    )
    graph = build_conversation_graph(handler)
    thread_config = {"configurable": {"thread_id": "session-b2b-1"}}

    input_data = {
        "messages": [
            {
                "role": "user",
                "content": "CNPJ 11222333000181, gostaria de consultar o SLA do nosso contrato",
            }
        ]
    }
    state = await graph.ainvoke(input_data, config=thread_config)
    assert state["customer_id"] == "cust_b2b_xpto"
    assert state["customer_segment"] == "B2B"
    assert state["authenticated"] is True
    assert (
        "Uptime garantido" in state["last_response"] or "contrato" in state["last_response"].lower()
    )


@pytest.mark.asyncio
async def test_rag_knowledge_query(tools_service_with_rag: NovaLojaToolsService) -> None:
    handler = AgentNodeHandler(
        tools_service=tools_service_with_rag,
        retriever=tools_service_with_rag.retriever,
    )
    graph = build_conversation_graph(handler)
    thread_config = {"configurable": {"thread_id": "session-rag-1"}}

    input_data = {
        "messages": [
            {
                "role": "user",
                "content": "Qual é a política de devolução e prazo de arrependimento pelo CDC?",
            }
        ]
    }
    state = await graph.ainvoke(input_data, config=thread_config)
    assert len(state["retrieved_docs"]) > 0
    assert "políticas oficiais" in state["last_response"]


@pytest.mark.asyncio
async def test_handoff_requested_explicitly(tools_service_with_rag: NovaLojaToolsService) -> None:
    handler = AgentNodeHandler(
        tools_service=tools_service_with_rag,
        retriever=tools_service_with_rag.retriever,
    )
    graph = build_conversation_graph(handler)
    thread_config = {"configurable": {"thread_id": "session-handoff-1"}}

    input_data = {
        "messages": [
            {
                "role": "user",
                "content": "Por favor, transfira para um atendente humano",
            }
        ]
    }
    state = await graph.ainvoke(input_data, config=thread_config)
    assert state["handoff_requested"] is True
    assert "transferindo" in state["last_response"].lower()


@pytest.mark.asyncio
async def test_long_conversation_summarization_and_context_preservation(
    tools_service_with_rag: NovaLojaToolsService,
) -> None:
    handler = AgentNodeHandler(
        tools_service=tools_service_with_rag,
        retriever=tools_service_with_rag.retriever,
    )
    graph = build_conversation_graph(handler)
    thread_config = {"configurable": {"thread_id": "session-long-1"}}

    # Turno inicial: autenticação com CPF da Maria
    state = await graph.ainvoke(
        {"messages": [{"role": "user", "content": "Olá, meu CPF é 52998224725"}]},
        config=thread_config,
    )
    assert state["customer_id"] == "cust_b2c_maria"
    assert state["authenticated"] is True

    # Simular 10 turnos adicionais de dúvidas gerais
    for i in range(10):
        state = await graph.ainvoke(
            {
                "messages": [
                    *state["messages"],
                    {"role": "user", "content": f"Dúvida {i}: como funciona o prazo de devolução?"},
                ]
            },
            config=thread_config,
        )

    # A lista de mensagens ativas foi compactada e summary foi preenchido
    assert len(state["messages"]) <= 8
    assert state["summary"] is not None
    assert "Sumarizado" in state["summary"]
    # Contexto do cliente foi preservado intacto
    assert state["customer_id"] == "cust_b2c_maria"
    assert state["authenticated"] is True
