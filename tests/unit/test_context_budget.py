import pytest
from hypothesis import given
from hypothesis import strategies as st

from atendente.agent.prompts.budget import (
    ContextBudgetManager,
    SectionBudgetConfig,
)
from atendente.tools.schemas import get_tool_definitions


@pytest.mark.unit
def test_context_budget_within_limits_normal_case() -> None:
    config = SectionBudgetConfig(
        system_max=600,
        tools_max=600,
        rag_max=800,
        history_max=1000,
        total_max=3000,
    )
    manager = ContextBudgetManager(config=config)

    result = manager.allocate(
        version="v3.0.0",
        segment="B2C",
        rag_chunks=[
            {
                "content": "O prazo de devolução por arrependimento é de 7 dias corridos.",
                "source_file": "b2c/politica_trocas_devolucoes.md",
                "section": "Prazo CDC",
            }
        ],
        messages=[
            {"role": "user", "content": "Olá, quero saber o prazo de devolução."},
        ],
        tools_schemas=get_tool_definitions(),
    )

    assert result.section_tokens["system"] <= config.system_max
    assert result.section_tokens["tools"] <= config.tools_max
    assert result.section_tokens["rag"] <= config.rag_max
    assert result.section_tokens["history"] <= config.history_max
    assert result.total_tokens <= config.total_max
    assert len(result.prompt_hash) == 64


@pytest.mark.unit
def test_context_budget_never_overflows_under_massive_inputs() -> None:
    config = SectionBudgetConfig(
        system_max=400,
        tools_max=300,
        rag_max=350,
        history_max=450,
        total_max=1500,
    )
    manager = ContextBudgetManager(config=config)

    # Criar chunks gigantescos que estourariam o orçamento de RAG (ex: 5000 tokens)
    huge_chunks = [
        {
            "content": f"Cláusula extensa número {i}: "
            + ("texto repetido de política oficial " * 120),
            "source_file": f"b2c/doc_{i}.md",
            "section": f"Seção {i}",
        }
        for i in range(10)
    ]

    # Criar histórico gigantesco de 60 mensagens longas
    huge_history = [
        {
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"Turno {i}: " + ("conversa longa " * 40),
        }
        for i in range(60)
    ]
    huge_history.append(
        {"role": "user", "content": "Pergunta crítica final que deve ser preservada!"}
    )

    result = manager.allocate(
        version="v3.0.0",
        segment="B2C",
        rag_chunks=huge_chunks,
        messages=huge_history,
        tools_schemas=get_tool_definitions(),
        summary="Resumo acumulado anterior muito longo " * 30,
    )

    assert result.section_tokens["system"] <= config.system_max
    assert result.section_tokens["tools"] <= config.tools_max
    assert result.section_tokens["rag"] <= config.rag_max
    assert result.section_tokens["history"] <= config.history_max
    assert result.total_tokens <= config.total_max
    assert "rag" in result.trimmed_sections
    assert "history" in result.trimmed_sections
    # A última mensagem do usuário (recency) deve estar preservada intacta
    assert (
        result.history_messages[-1]["content"] == "Pergunta crítica final que deve ser preservada!"
    )
    # Delimitadores XML do RAG continuam válidos mesmo após truncamento
    assert result.rag_context.startswith("<contexto_seguro>")
    assert result.rag_context.endswith("</contexto_seguro>")


@pytest.mark.unit
@given(
    num_chunks=st.integers(min_value=0, max_value=8),
    chunk_len=st.integers(min_value=10, max_value=800),
    num_msgs=st.integers(min_value=1, max_value=25),
)
def test_property_budget_invariant_never_exceeds_limits(
    num_chunks: int, chunk_len: int, num_msgs: int
) -> None:
    config = SectionBudgetConfig(
        system_max=500,
        tools_max=400,
        rag_max=400,
        history_max=500,
        total_max=1800,
    )
    manager = ContextBudgetManager(config=config)

    chunks = [
        {"content": "palavra " * (chunk_len // 4), "source_file": "doc.md", "section": "S1"}
        for _ in range(num_chunks)
    ]
    msgs = [{"role": "user", "content": f"msg {i} " + ("teste " * 20)} for i in range(num_msgs)]

    res = manager.allocate(
        version="v3.0.0",
        segment="B2B",
        rag_chunks=chunks,
        messages=msgs,
        tools_schemas=get_tool_definitions(),
    )

    assert res.section_tokens["system"] <= config.system_max
    assert res.section_tokens["tools"] <= config.tools_max
    assert res.section_tokens["rag"] <= config.rag_max
    assert res.section_tokens["history"] <= config.history_max
    assert res.total_tokens <= config.total_max
