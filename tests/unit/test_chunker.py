import pytest

from atendente.rag.chunker import ChunkingConfig, chunk_markdown_document, estimate_tokens


@pytest.mark.unit
def test_estimate_tokens() -> None:
    text = "A NovaLoja é líder em comércio eletrônico."
    tokens = estimate_tokens(text)
    assert tokens > 0
    assert tokens < len(text)


@pytest.mark.unit
def test_chunk_markdown_document_basic() -> None:
    markdown_content = """# Política de Devoluções

## 1. Prazo Legal
O consumidor tem 7 dias corridos para devolução. O frete é pago pela NovaLoja.

## 2. Condições do Produto
O produto deve estar lacrado na embalagem original sem sinais de uso indevido.
"""
    config = ChunkingConfig(target_tokens=256, overlap_tokens=30)
    chunks = chunk_markdown_document(
        content=markdown_content, file_path="data/kb/b2c/politica_trocas.md", config=config
    )

    assert len(chunks) >= 2
    assert chunks[0].title == "Política de Devoluções"
    assert chunks[0].section == "1. Prazo Legal"
    assert "Política de Devoluções > 1. Prazo Legal" in chunks[0].breadcrumbs
    assert chunks[0].segment == "B2C"
    assert "7 dias corridos" in chunks[0].content


@pytest.mark.unit
def test_chunk_markdown_document_segment_detection() -> None:
    sample = "# Titulo\n## Secao\nConteudo qualquer"
    c_b2c = chunk_markdown_document(sample, "data/kb/b2c/doc.md")
    assert c_b2c[0].segment == "B2C"

    c_b2b = chunk_markdown_document(sample, "data/kb/b2b/doc.md")
    assert c_b2b[0].segment == "B2B"

    c_geral = chunk_markdown_document(sample, "data/kb/geral/doc.md")
    assert c_geral[0].segment == "GERAL"


@pytest.mark.unit
def test_chunking_configurations_granularity() -> None:
    # Cria parágrafos de tamanho controlado para testar as 3 configurações
    paragraphs = [
        f"Parágrafo {i}: regras contratuais de atendimento e políticas corporativas da NovaLoja."
        for i in range(30)
    ]
    content = "# Documento Longo\n## Seção Única\n\n" + "\n\n".join(paragraphs)

    cfg_a = ChunkingConfig(target_tokens=64, overlap_tokens=10)
    cfg_b = ChunkingConfig(target_tokens=160, overlap_tokens=30)
    cfg_c = ChunkingConfig(target_tokens=400, overlap_tokens=50)

    chunks_a = chunk_markdown_document(content, "data/kb/b2c/longo.md", config=cfg_a)
    chunks_b = chunk_markdown_document(content, "data/kb/b2c/longo.md", config=cfg_b)
    chunks_c = chunk_markdown_document(content, "data/kb/b2c/longo.md", config=cfg_c)

    # Configuração com menor target_tokens deve gerar estritamente mais chunks
    assert len(chunks_a) > len(chunks_b) > len(chunks_c)
