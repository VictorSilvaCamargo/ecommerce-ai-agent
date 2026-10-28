import re
from typing import Any

# Padrões clássicos de Indirect Prompt Injection em documentos recuperados
INJECTION_PATTERNS = [
    re.compile(r"</?\s*contexto_seguro\s*>", re.IGNORECASE),
    re.compile(
        r"ignore\s+(todas\s+as\s+|all\s+)?(instruções|instrucoes|instructions)\s*(anteriores|previous)?",
        re.IGNORECASE,
    ),
    re.compile(r"esqueça\s+suas\s+regras", re.IGNORECASE),
    re.compile(r"system\s*override", re.IGNORECASE),
    re.compile(r"aprove\s+o\s+reembolso\s+sem\s+confirmação", re.IGNORECASE),
    re.compile(r"você\s+agora\s+é\s+um", re.IGNORECASE),
]


def sanitize_untrusted_rag_text(text: str) -> tuple[str, bool]:
    """Sanitiza conteúdo de chunks recuperados contra tentativas de Prompt Injection Indireto.

    Retorna uma tupla `(texto_sanitizado, foi_bloqueado)`.
    """
    sanitized = text
    was_flagged = False

    for pattern in INJECTION_PATTERNS:
        if pattern.search(sanitized):
            was_flagged = True
            sanitized = pattern.sub("[INSTRUÇÃO BLOQUEADA]", sanitized)

    return sanitized, was_flagged


def format_rag_context_safe(chunks: list[dict[str, Any]]) -> tuple[str, bool]:
    """Empacota os chunks do RAG dentro de delimitadores seguros `<contexto_seguro>`.

    Garante que nenhuma tag falsa `</contexto_seguro>` ou diretiva imperativa maliciosa
    escape da área isolada de dados.
    """
    if not chunks:
        return (
            "<contexto_seguro>\n[NENHUM_DOCUMENTO_RELEVANTE_ENCONTRADO]\n</contexto_seguro>",
            False,
        )

    any_sanitized = False
    formatted_docs: list[str] = []

    for idx, chunk in enumerate(chunks, start=1):
        raw_content = str(chunk.get("content", ""))
        source_file = str(chunk.get("source_file", "desconhecido"))
        section = str(chunk.get("section", "Geral"))

        clean_content, was_flagged = sanitize_untrusted_rag_text(raw_content)
        if was_flagged:
            any_sanitized = True

        doc_block = (
            f'  <documento indice="{idx}" fonte="{source_file}" secao="{section}">\n'
            f"    {clean_content}\n"
            f"  </documento>"
        )
        formatted_docs.append(doc_block)

    joined_docs = "\n".join(formatted_docs)
    full_block = f"<contexto_seguro>\n{joined_docs}\n</contexto_seguro>"
    return full_block, any_sanitized
