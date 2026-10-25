from __future__ import annotations

from collections import Counter

from pydantic import BaseModel, Field


class RetrievalMonitorReport(BaseModel):
    """Relatório consolidado de saúde do Retrieval RAG."""

    total_queries: int
    zero_result_queries: list[str] = Field(default_factory=list)
    low_relevance_queries: list[str] = Field(default_factory=list)
    orphan_chunk_ids: list[str] = Field(default_factory=list)
    chunk_hit_counts: dict[str, int] = Field(default_factory=dict)
    tuning_recommendations: list[str] = Field(default_factory=list)


class RetrievalMonitor:
    """Monitora consultas RAG em produção para detectar abstenções, baixa relevância e chunks órfãos."""

    def __init__(
        self,
        registered_chunk_ids: list[str] | None = None,
        low_relevance_threshold: float = 0.45,
    ) -> None:
        self._registered_chunks: set[str] = set(registered_chunk_ids or [])
        self._low_relevance_threshold = low_relevance_threshold
        self._total_queries = 0
        self._zero_result_queries: list[str] = []
        self._low_relevance_queries: list[str] = []
        self._chunk_hits: Counter[str] = Counter()

    def register_chunks(self, chunk_ids: list[str]) -> None:
        self._registered_chunks.update(chunk_ids)

    def record_query(
        self,
        query: str,
        segment: str | None,
        retrieved_chunk_ids: list[str],
        top_score: float,
        abstained: bool,
    ) -> None:
        self._total_queries += 1
        if abstained or not retrieved_chunk_ids:
            self._zero_result_queries.append(query)
            return

        for cid in retrieved_chunk_ids:
            self._chunk_hits[cid] += 1

        if top_score < self._low_relevance_threshold:
            self._low_relevance_queries.append(query)

    def generate_report(self) -> RetrievalMonitorReport:
        orphan_ids = sorted(self._registered_chunks - set(self._chunk_hits.keys()))
        recommendations: list[str] = []

        if self._zero_result_queries:
            recommendations.append(
                f"Foram detectadas {len(self._zero_result_queries)} consultas sem resultados/abstencao. "
                "Avalie expandir a base de conhecimento para cobrir os topicos consultados ou ajustar sinonimos no BM25."
            )
        if self._low_relevance_queries:
            recommendations.append(
                f"Foram detectadas {len(self._low_relevance_queries)} consultas com score abaixo de "
                f"{self._low_relevance_threshold:.2f}. Considere revisar o tamanho de chunk ou re-rankear top-k."
            )
        if orphan_ids:
            recommendations.append(
                f"Existem {len(orphan_ids)} chunks orfaos nunca recuperados ({', '.join(orphan_ids[:5])}). "
                "Verifique se possuem cabecalhos claros e metadados de segmento adequados."
            )

        return RetrievalMonitorReport(
            total_queries=self._total_queries,
            zero_result_queries=list(self._zero_result_queries),
            low_relevance_queries=list(self._low_relevance_queries),
            orphan_chunk_ids=orphan_ids,
            chunk_hit_counts=dict(self._chunk_hits),
            tuning_recommendations=recommendations,
        )
