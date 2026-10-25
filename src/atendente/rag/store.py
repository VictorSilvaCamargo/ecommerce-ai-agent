import math
import re
from abc import ABC, abstractmethod

from atendente.rag.models import KBChunk

PORTUGUESE_STOPWORDS = {
    "a",
    "ao",
    "aos",
    "aquela",
    "aquelas",
    "aquele",
    "aqueles",
    "aquilo",
    "as",
    "até",
    "com",
    "como",
    "da",
    "das",
    "de",
    "dela",
    "delas",
    "dele",
    "deles",
    "depois",
    "do",
    "dos",
    "e",
    "é",
    "ela",
    "elas",
    "ele",
    "eles",
    "em",
    "entre",
    "era",
    "eram",
    "éramos",
    "essa",
    "essas",
    "esse",
    "esses",
    "esta",
    "estas",
    "este",
    "estes",
    "eu",
    "foi",
    "fomos",
    "foram",
    "isso",
    "isto",
    "já",
    "lhe",
    "lhes",
    "mais",
    "mas",
    "me",
    "mesmo",
    "meu",
    "meus",
    "minha",
    "minhas",
    "muito",
    "na",
    "nas",
    "não",
    "no",
    "nos",
    "nossa",
    "nossas",
    "nosso",
    "nossos",
    "num",
    "numa",
    "o",
    "os",
    "ou",
    "para",
    "pela",
    "pelas",
    "pelo",
    "pelos",
    "por",
    "qual",
    "quando",
    "que",
    "quem",
    "se",
    "seja",
    "sem",
    "ser",
    "seu",
    "seus",
    "só",
    "sua",
    "suas",
    "também",
    "te",
    "tem",
    "têm",
    "temos",
    "tenho",
    "ter",
    "teu",
    "teus",
    "tua",
    "tuas",
    "um",
    "uma",
    "você",
    "vocês",
}


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2, strict=True))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


class VectorStore(ABC):
    @abstractmethod
    async def add_chunks(self, chunks: list[KBChunk]) -> None:
        pass

    @abstractmethod
    async def similarity_search(
        self,
        query_embedding: list[float],
        segment: str | None = None,
        limit: int = 5,
        min_similarity: float = 0.30,
    ) -> list[tuple[KBChunk, float]]:
        pass

    @abstractmethod
    async def text_search(
        self, query_text: str, segment: str | None = None, limit: int = 5, min_score: float = 0.5
    ) -> list[tuple[KBChunk, float]]:
        pass


class InMemoryVectorStore(VectorStore):
    """
    Armazenamento vetorial e de busca textual em memória para testes,
    benchmarking de chunking e execução local.
    """

    def __init__(self) -> None:
        self.chunks: list[KBChunk] = []

    async def add_chunks(self, chunks: list[KBChunk]) -> None:
        self.chunks.extend(chunks)

    def _matches_segment(self, chunk_segment: str, query_segment: str | None) -> bool:
        if not query_segment:
            return True
        query_seg = query_segment.upper()
        # Chunks GERAL são visíveis para ambos os segmentos
        if chunk_segment.upper() == "GERAL":
            return True
        return chunk_segment.upper() == query_seg

    async def similarity_search(
        self,
        query_embedding: list[float],
        segment: str | None = None,
        limit: int = 5,
        min_similarity: float = 0.30,
    ) -> list[tuple[KBChunk, float]]:
        scored: list[tuple[KBChunk, float]] = []
        for chk in self.chunks:
            if not self._matches_segment(chk.segment, segment):
                continue
            if not chk.embedding:
                continue
            sim = cosine_similarity(query_embedding, chk.embedding)
            if sim >= min_similarity:
                scored.append((chk, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]

    async def text_search(
        self, query_text: str, segment: str | None = None, limit: int = 5, min_score: float = 0.5
    ) -> list[tuple[KBChunk, float]]:
        # Extração de termos significativos sem stopwords
        raw_words = re.sub(r"[^\w\s]", " ", query_text.lower()).split()
        terms = [w for w in raw_words if len(w) > 2 and w not in PORTUGUESE_STOPWORDS]
        if not terms:
            return []

        scored: list[tuple[KBChunk, float]] = []
        for chk in self.chunks:
            if not self._matches_segment(chk.segment, segment):
                continue

            content_lower = chk.content.lower()
            title_lower = chk.title.lower()
            section_lower = chk.section.lower()

            content_matches = 0
            header_matches = 0

            for t in terms:
                # Radical de 4 letras para acomodar flexões (ex: devoluç -> devolução, devoluções)
                stem = t[:5] if len(t) >= 5 else t
                if stem in content_lower:
                    content_matches += content_lower.count(stem)
                if stem in title_lower or stem in section_lower:
                    header_matches += title_lower.count(stem) + section_lower.count(stem)

            total_weighted_matches = content_matches + (header_matches * 4)
            if total_weighted_matches > 0:
                score = total_weighted_matches / (1.0 + math.log1p(len(chk.content)))
                if score >= min_score:
                    scored.append((chk, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]
