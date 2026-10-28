import pytest

from atendente.infra.llm.client import (
    LLMMessage,
    LLMResponse,
    LLMToolCall,
    MockLLMClient,
)


@pytest.mark.asyncio
async def test_mock_llm_client_fifo_queue() -> None:
    client = MockLLMClient()
    resp1 = LLMResponse(content="Olá, como posso ajudar?")
    resp2 = LLMResponse(
        content=None,
        tool_calls=[
            LLMToolCall(id="call_1", name="consultar_pedido", arguments={"order_id": "ped-123"})
        ],
    )
    client.enqueue_response(resp1)
    client.enqueue_response(resp2)

    res1 = await client.generate(messages=[LLMMessage(role="user", content="Oi")])
    assert res1.content == "Olá, como posso ajudar?"
    assert len(res1.tool_calls) == 0

    res2 = await client.generate(
        messages=[LLMMessage(role="user", content="Ver meu pedido ped-123")]
    )
    assert res2.content is None
    assert len(res2.tool_calls) == 1
    assert res2.tool_calls[0].name == "consultar_pedido"
    assert res2.tool_calls[0].arguments["order_id"] == "ped-123"


@pytest.mark.asyncio
async def test_mock_llm_client_default_fallback() -> None:
    client = MockLLMClient(default_response="Resposta padrão determinística")
    res = await client.generate(messages=[LLMMessage(role="user", content="qualquer coisa")])
    assert res.content == "Resposta padrão determinística"
    assert res.usage["total_tokens"] > 0
