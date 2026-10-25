import asyncio
from pathlib import Path

from atendente.rag.chunker import ChunkingConfig, chunk_directory
from atendente.rag.embeddings import DeterministicEmbeddingService, EmbeddingService
from atendente.rag.models import KBChunk
from atendente.rag.store import VectorStore


class IngestionPipeline:
    """Pipeline de ingestão e indexação de documentos na base vetorial NovaLoja."""

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        config: ChunkingConfig = ChunkingConfig(target_tokens=512, overlap_tokens=64),
    ):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.config = config

    async def ingest_directory(self, directory_path: Path) -> list[KBChunk]:
        """Carrega arquivos Markdown, particiona semanticamente e indexa embeddings."""
        chunks = chunk_directory(directory_path, self.config)
        if not chunks:
            return []

        # Gera embeddings para todos os chunks
        chunks_with_emb: list[KBChunk] = []
        for chk in chunks:
            emb = self.embedding_service.embed_text(chk.content)
            chunks_with_emb.append(chk.model_copy(update={"embedding": emb}))

        await self.vector_store.add_chunks(chunks_with_emb)
        return chunks_with_emb


async def run_ingestion(data_dir: str = "data/kb") -> None:
    from atendente.rag.store import InMemoryVectorStore

    store = InMemoryVectorStore()
    emb_service = DeterministicEmbeddingService()
    pipeline = IngestionPipeline(vector_store=store, embedding_service=emb_service)
    chunks = await pipeline.ingest_directory(Path(data_dir))
    print(f"Ingested {len(chunks)} chunks into vector store successfully!")


if __name__ == "__main__":
    asyncio.run(run_ingestion())
