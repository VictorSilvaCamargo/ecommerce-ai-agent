from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class KBChunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: f"chk_{uuid4().hex[:12]}")
    document_id: str
    title: str
    section: str
    breadcrumbs: str
    content: str
    segment: str  # "B2C", "B2B", "GERAL"
    source_file: str
    token_count: int
    embedding: list[float] | None = None


class RetrievedChunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    chunk: KBChunk
    score: float
    retrieval_method: str  # "dense", "sparse", "hybrid_rrf"

    @property
    def citation(self) -> str:
        return f"[{self.chunk.title} - {self.chunk.section}] ({self.chunk.source_file})"
