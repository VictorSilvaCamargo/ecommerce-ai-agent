from pathlib import Path
from typing import Any

import pytest

from atendente.rag.chunker import ChunkingConfig, chunk_directory
from atendente.rag.embeddings import DeterministicEmbeddingService
from atendente.rag.retriever import HybridRetriever
from atendente.rag.store import InMemoryVectorStore

EVAL_DATASET: list[dict[str, Any]] = [
    {
        "query": "qual é o prazo de dias para devolução por direito de arrependimento?",
        "expected_doc": "politica_trocas_devolucoes",
        "segment": "B2C",
    },
    {
        "query": "quantos dias demora para receber o estorno na fatura do cartão de crédito?",
        "expected_doc": "politica_reembolso_estorno",
        "segment": "B2C",
    },
    {
        "query": "como cancelar um pedido que já foi despachado em transporte?",
        "expected_doc": "cancelamento_pedidos",
        "segment": "B2C",
    },
    {
        "query": "quantas tentativas de entrega são realizadas antes de retornar para agência?",
        "expected_doc": "prazos_entrega_frete",
        "segment": "B2C",
    },
    {
        "query": "onde consigo emitir a segunda via da nota fiscal eletrônica e DANFE?",
        "expected_doc": "segunda_via_documentos",
        "segment": "B2C",
    },
    {
        "query": "qual é o prazo de garantia legal contra vício de fabricação?",
        "expected_doc": "garantia_defeito_fabricacao",
        "segment": "B2C",
    },
    {
        "query": "o que fazer se a caixa do produto chegar avariada ou com fita violada?",
        "expected_doc": "produto_avariado_ou_violado",
        "segment": "B2C",
    },
    {
        "query": "quais são os tempos de resposta e resolução de incidentes no contrato Enterprise?",
        "expected_doc": "contratos_sla_niveis",
        "segment": "B2B",
    },
    {
        "query": "qual é o dia de fechamento mensal da fatura consolidada e prazo de pagamento?",
        "expected_doc": "faturamento_fatura_consolidada",
        "segment": "B2B",
    },
    {
        "query": "qual é o prazo de resposta da Ouvidoria em caso de insatisfação?",
        "expected_doc": "ouvidoria_escalonamento_final",
        "segment": "GERAL",
    },
]


async def evaluate_chunking_config(config: ChunkingConfig) -> dict[str, float]:
    kb_dir = Path("data/kb")
    chunks = chunk_directory(kb_dir, config)

    embedding_service = DeterministicEmbeddingService(dimension=384)
    chunks_with_emb = [
        chk.model_copy(update={"embedding": embedding_service.embed_text(chk.content)})
        for chk in chunks
    ]

    store = InMemoryVectorStore()
    await store.add_chunks(chunks_with_emb)

    retriever = HybridRetriever(
        vector_store=store, embedding_service=embedding_service, relevance_threshold=0.010
    )

    hits_at_3 = 0
    hits_at_5 = 0
    reciprocal_ranks: list[float] = []

    for test_case in EVAL_DATASET:
        query = test_case["query"]
        expected = test_case["expected_doc"]
        segment = test_case["segment"]

        results = await retriever.retrieve(query=query, segment=segment, limit=5)

        rank_found = 0
        for i, res in enumerate(results):
            if expected in res.chunk.document_id:
                rank_found = i + 1
                break

        if rank_found > 0 and rank_found <= 3:
            hits_at_3 += 1
        if rank_found > 0 and rank_found <= 5:
            hits_at_5 += 1

        reciprocal_ranks.append(1.0 / rank_found if rank_found > 0 else 0.0)

    total = len(EVAL_DATASET)
    return {
        "chunks_count": float(len(chunks)),
        "hit_rate_at_3": round(hits_at_3 / total, 3),
        "hit_rate_at_5": round(hits_at_5 / total, 3),
        "mrr": round(sum(reciprocal_ranks) / total, 3),
    }


@pytest.mark.integration
async def test_compare_three_chunking_configurations() -> None:
    # 3 configurações obrigatórias do ADR-0004
    cfg_a = ChunkingConfig(target_tokens=256, overlap_tokens=30)
    cfg_b = ChunkingConfig(target_tokens=512, overlap_tokens=64)
    cfg_c = ChunkingConfig(target_tokens=1024, overlap_tokens=128)

    metrics_a = await evaluate_chunking_config(cfg_a)
    metrics_b = await evaluate_chunking_config(cfg_b)
    metrics_c = await evaluate_chunking_config(cfg_c)

    print("\nResultados do Benchmark de Chunking:")
    print(f"Config A (256 tokens): {metrics_a}")
    print(f"Config B (512 tokens): {metrics_b}")
    print(f"Config C (1024 tokens): {metrics_c}")

    # Todas as configurações devem atingir Hit Rate@5 >= 0.80 e MRR >= 0.70
    assert metrics_b["hit_rate_at_3"] >= 0.80
    assert metrics_b["hit_rate_at_5"] >= 0.90
    assert metrics_b["mrr"] >= 0.80
