import math
import re
from pathlib import Path

from pydantic import BaseModel, Field

from atendente.rag.models import KBChunk


class ChunkingConfig(BaseModel):
    target_tokens: int = Field(default=512, ge=64, le=2048)
    overlap_tokens: int = Field(default=64, ge=0, le=512)


def estimate_tokens(text: str) -> int:
    """Estimativa rápida e determinística de tokens (~4 caracteres por token em pt-BR)."""
    return max(1, math.ceil(len(text) / 4))


def detect_segment_from_path(file_path: str) -> str:
    path_lower = file_path.lower().replace("\\", "/")
    if "/b2c/" in path_lower:
        return "B2C"
    if "/b2b/" in path_lower:
        return "B2B"
    return "GERAL"


def chunk_markdown_document(
    content: str, file_path: str, config: ChunkingConfig = ChunkingConfig()
) -> list[KBChunk]:
    """
    Particiona um documento Markdown semanticamente preservando cabeçalhos e hierarquia de seções.
    Garante breadcrumbs no formato: Documento > Seção > Subseção.
    Aplica sobreposição controlada de tokens se a seção for subdividida.
    """
    segment = detect_segment_from_path(file_path)
    document_id = Path(file_path).stem

    lines = content.splitlines()
    document_title = "Documento Sem Título"
    current_section = "Introdução"
    breadcrumbs = document_title

    # Primeiro identifica o título do documento
    for line in lines:
        if line.startswith("# "):
            document_title = line[2:].strip()
            breadcrumbs = document_title
            break

    # Divide por seções (## ou ###)
    sections: list[tuple[str, str, list[str]]] = []
    current_lines: list[str] = []

    for line in lines:
        if line.startswith("# ") and not sections:
            continue
        if line.startswith("## ") or line.startswith("### "):
            if current_lines:
                sections.append((current_section, breadcrumbs, current_lines))
                current_lines = []
            heading_text = line.lstrip("#").strip()
            current_section = heading_text
            breadcrumbs = f"{document_title} > {heading_text}"
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_section, breadcrumbs, current_lines))

    chunks: list[KBChunk] = []

    for section_name, section_crumbs, sec_lines in sections:
        section_text = "\n".join(sec_lines).strip()
        if not section_text:
            continue

        token_est = estimate_tokens(section_text)

        # Se a seção couber no limite alvo, cria um único chunk
        if token_est <= config.target_tokens:
            chunk_content = f"### {section_name}\n\n{section_text}"
            chunks.append(
                KBChunk(
                    id=f"{document_id}_{len(chunks):03d}",
                    document_id=document_id,
                    title=document_title,
                    section=section_name,
                    breadcrumbs=section_crumbs,
                    content=chunk_content,
                    segment=segment,
                    source_file=file_path,
                    token_count=estimate_tokens(chunk_content),
                )
            )
        else:
            # Subdivide a seção preservando sobreposição de parágrafos
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", section_text) if p.strip()]
            sub_chunks: list[str] = []
            current_slice: list[str] = []
            current_slice_tokens = 0

            for p in paragraphs:
                p_tokens = estimate_tokens(p)
                if current_slice_tokens + p_tokens > config.target_tokens and current_slice:
                    slice_text = "\n\n".join(current_slice)
                    sub_chunks.append(slice_text)

                    # Calcula sobreposição a partir do final do slice atual
                    overlap_slice: list[str] = []
                    accumulated = 0
                    for prev_p in reversed(current_slice):
                        prev_tokens = estimate_tokens(prev_p)
                        if accumulated + prev_tokens <= config.overlap_tokens:
                            overlap_slice.insert(0, prev_p)
                            accumulated += prev_tokens
                        else:
                            break

                    current_slice = overlap_slice + [p]
                    current_slice_tokens = sum(estimate_tokens(x) for x in current_slice)
                else:
                    current_slice.append(p)
                    current_slice_tokens += p_tokens

            if current_slice:
                sub_chunks.append("\n\n".join(current_slice))

            for idx, sub_text in enumerate(sub_chunks):
                chunk_content = f"### {section_name} (Parte {idx + 1})\n\n{sub_text}"
                chunks.append(
                    KBChunk(
                        id=f"{document_id}_{len(chunks):03d}",
                        document_id=document_id,
                        title=document_title,
                        section=f"{section_name} (Parte {idx + 1})",
                        breadcrumbs=f"{section_crumbs} (Parte {idx + 1})",
                        content=chunk_content,
                        segment=segment,
                        source_file=file_path,
                        token_count=estimate_tokens(chunk_content),
                    )
                )

    return chunks


def chunk_directory(
    directory_path: Path, config: ChunkingConfig = ChunkingConfig()
) -> list[KBChunk]:
    all_chunks: list[KBChunk] = []
    for md_file in sorted(directory_path.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        rel_path = md_file.as_posix()
        chunks = chunk_markdown_document(content, rel_path, config)
        all_chunks.extend(chunks)
    return all_chunks
