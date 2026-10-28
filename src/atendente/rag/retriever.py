from atendente.rag.embeddings import EmbeddingService
from atendente.rag.models import KBChunk, RetrievedChunk
from atendente.rag.store import VectorStore


class HybridRetriever:
    """
    Retriever híbrido combinando busca vetorial (densa) e busca textual (esparsa)
    através de Reciprocal Rank Fusion (RRF).
    Aplica isolamento por segmento e limiar de abstenção por relevância.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        relevance_threshold: float = 0.012,
        rrf_k: int = 60,
    ):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.relevance_threshold = relevance_threshold
        self.rrf_k = rrf_k

    async def retrieve(
        self, query: str, segment: str | None = None, limit: int = 5
    ) -> list[RetrievedChunk]:
        """
        Executa a busca híbrida:
        1. Gera embedding da query e realiza busca vetorial
        2. Realiza busca léxica por termos
        3. Funde os rankings usando Reciprocal Rank Fusion (RRF)
        4. Filtra por limiar de relevância mínima (abstenção)
        """
        query_emb = self.embedding_service.embed_text(query)

        # Busca com margem ampliada para a fusão
        candidate_limit = limit * 3
        dense_results = await self.vector_store.similarity_search(
            query_embedding=query_emb, segment=segment, limit=candidate_limit
        )
        sparse_results = await self.vector_store.text_search(
            query_text=query, segment=segment, limit=candidate_limit
        )

        rrf_scores: dict[str, float] = {}
        chunk_map: dict[str, KBChunk] = {}

        # Pontuação RRF para busca densa
        for rank, (chk, _) in enumerate(dense_results):
            chunk_map[chk.id] = chk
            rrf_scores[chk.id] = rrf_scores.get(chk.id, 0.0) + (1.0 / (self.rrf_k + (rank + 1)))

        # Pontuação RRF para busca esparsa
        for rank, (chk, _) in enumerate(sparse_results):
            chunk_map[chk.id] = chk
            rrf_scores[chk.id] = rrf_scores.get(chk.id, 0.0) + (1.0 / (self.rrf_k + (rank + 1)))

        sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        results: list[RetrievedChunk] = []
        for chk_id, score in sorted_chunks[:limit]:
            # Limiar de abstenção: se o score for muito baixo, descarta
            if score < self.relevance_threshold:
                continue

            results.append(
                RetrievedChunk(
                    chunk=chunk_map[chk_id], score=round(score, 5), retrieval_method="hybrid_rrf"
                )
            )

        return results
