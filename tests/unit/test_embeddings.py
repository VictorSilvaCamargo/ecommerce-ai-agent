import math

import pytest

from atendente.rag.embeddings import DeterministicEmbeddingService


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2, strict=True))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


@pytest.mark.unit
def test_deterministic_embedding_dimension_and_normalization() -> None:
    service = DeterministicEmbeddingService(dimension=384)
    emb = service.embed_text("Política de devolução e reembolso da NovaLoja")
    assert len(emb) == 384
    norm = math.sqrt(sum(x * x for x in emb))
    assert pytest.approx(norm, abs=1e-4) == 1.0


@pytest.mark.unit
def test_deterministic_embedding_similarity() -> None:
    service = DeterministicEmbeddingService(dimension=384)

    t1 = "Qual é o prazo para devolução e reembolso de produto entregue?"
    t2 = "Prazo legal de 7 dias para devolução de produto entregue com reembolso."
    t3 = "Contrato corporativo B2B com SLA de 1 hora para chamados críticos Enterprise."

    emb1 = service.embed_text(t1)
    emb2 = service.embed_text(t2)
    emb3 = service.embed_text(t3)

    sim_related = cosine_similarity(emb1, emb2)
    sim_unrelated = cosine_similarity(emb1, emb3)

    # Textos correlatos de reembolso devem ter similaridade expressivamente maior que texto de contrato B2B
    assert sim_related > sim_unrelated
    assert sim_related > 0.50
    assert sim_unrelated < 0.20


@pytest.mark.unit
def test_batch_embeddings() -> None:
    service = DeterministicEmbeddingService(dimension=384)
    texts = ["Texto um", "Texto dois", "Texto três"]
    batch = service.embed_batch(texts)
    assert len(batch) == 3
    assert all(len(v) == 384 for v in batch)
