import hashlib
import math
import re
from abc import ABC, abstractmethod


class EmbeddingService(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int:
        pass

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Gera embedding denso para um texto individual."""
        pass

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Gera embeddings para múltiplos textos."""
        return [self.embed_text(t) for t in texts]


class DeterministicEmbeddingService(EmbeddingService):
    """
    Gerador determinístico de embeddings densos normalizados em L2.
    Utiliza hash semântico de n-gramas e raízes de palavras para produzir
    representações vetoriais contínuas reprodutíveis sem necessidade de GPU ou chamadas de API externas.
    """

    def __init__(self, dimension: int = 384):
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    def _tokenize(self, text: str) -> list[str]:
        # Normalização simples: minúsculas e divisão em palavras
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        words = [w for w in cleaned.split() if len(w) > 1]
        tokens: list[str] = list(words)
        # Adiciona bi-gramas para capturar contexto local
        for i in range(len(words) - 1):
            tokens.append(f"{words[i]}_{words[i + 1]}")
        return tokens

    def embed_text(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        tokens = self._tokenize(text)
        if not tokens:
            vec[0] = 1.0
            return vec

        for token in tokens:
            # Gera índices determinísticos com SHA-256
            h = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(h[:4], "little") % self._dim
            sign = 1.0 if (h[4] % 2 == 0) else -1.0
            # Peso levemente maior para termos mais longos
            weight = math.log1p(len(token))
            vec[idx] += sign * weight

            # Dispersão para dimensão vizinha
            idx2 = int.from_bytes(h[5:9], "little") % self._dim
            sign2 = 1.0 if (h[9] % 2 == 0) else -1.0
            vec[idx2] += sign2 * (weight * 0.5)

        # Normalização L2
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        else:
            vec[0] = 1.0

        return vec
