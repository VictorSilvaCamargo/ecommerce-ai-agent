from pathlib import Path

import pytest

from atendente.rag.chunker import ChunkingConfig, chunk_directory
from atendente.rag.embeddings import DeterministicEmbeddingService
from atendente.rag.retriever import HybridRetriever
from atendente.rag.store import InMemoryVectorStore


@pytest.fixture
async def populated_retriever() -> HybridRetriever:
    kb_dir = Path("data/kb")
    chunks = chunk_directory(kb_dir, ChunkingConfig(target_tokens=512, overlap_tokens=64))

    embedding_service = DeterministicEmbeddingService(dimension=384)
    chunks_with_emb = [
        chk.model_copy(update={"embedding": embedding_service.embed_text(chk.content)})
        for chk in chunks
    ]

    store = InMemoryVectorStore()
    await store.add_chunks(chunks_with_emb)

    return HybridRetriever(
        vector_store=store, embedding_service=embedding_service, relevance_threshold=0.012
    )


@pytest.mark.unit
async def test_retriever_b2c_query_success(populated_retriever: HybridRetriever) -> None:
    results = await populated_retriever.retrieve(
        query="qual é o prazo para solicitar devolução por arrependimento?", segment="B2C", limit=3
    )

    assert len(results) >= 1
    # Garante que a política correta foi recuperada entre os primeiros resultados
    has_target_chunk = any(
        "Direito de Arrependimento" in r.chunk.section or "Política de Trocas" in r.chunk.title
        for r in results
    )
    assert has_target_chunk is True
    assert any("7" in r.chunk.content and "dias corridos" in r.chunk.content for r in results)


@pytest.mark.unit
async def test_retriever_b2b_query_success(populated_retriever: HybridRetriever) -> None:
    results = await populated_retriever.retrieve(
        query="qual é o tempo de atendimento e SLA do contrato Platinum para chamados críticos?",
        segment="B2B",
        limit=3,
    )

    assert len(results) >= 1
    top = results[0]
    assert "Platinum" in top.chunk.content or "SLA" in top.chunk.title
    assert top.chunk.segment == "B2B"


@pytest.mark.unit
async def test_retriever_segment_isolation(populated_retriever: HybridRetriever) -> None:
    # Consulta feita com perfil B2C não pode retornar documentos restritos a B2B
    b2c_results = await populated_retriever.retrieve(
        query="qual é a multa e crédito por descumprimento de SLA contratual?",
        segment="B2C",
        limit=5,
    )

    for r in b2c_results:
        assert r.chunk.segment != "B2B", "Documento corporativo B2B vazou em consulta B2C!"


@pytest.mark.unit
async def test_retriever_abstention_on_unrelated_query(
    populated_retriever: HybridRetriever,
) -> None:
    # Query sem nenhuma relação com e-commerce ou NovaLoja
    results = await populated_retriever.retrieve(
        query="receita de bolo de cenoura com cobertura de chocolate e calda",
        segment="B2C",
        limit=3,
    )

    # O mecanismo de relevância mínima deve descartar resultados espúrios (abstenção)
    assert len(results) == 0
