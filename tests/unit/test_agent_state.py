import pytest

from atendente.agent.state import ConversationState


@pytest.mark.unit
def test_conversation_state_defaults() -> None:
    state = ConversationState()
    assert state.customer_id is None
    assert state.customer_document is None
    assert state.customer_segment == "INDEFINIDO"
    assert state.authenticated is False
    assert state.channel == "web"
    assert state.messages == []
    assert state.active_intent is None
    assert state.pending_action is None
    assert state.action_confirmed is False
    assert state.retrieved_docs == []
    assert state.handoff_requested is False
    assert state.handoff_reason is None
    assert state.consecutive_unresolved_turns == 0
    assert state.frustration_detected is False
    assert state.summary is None
    assert state.last_tool_result is None
    assert state.last_response is None


@pytest.mark.unit
def test_conversation_state_custom_values() -> None:
    state = ConversationState(
        customer_id="cust-123",
        customer_document="11144477735",
        customer_segment="B2C",
        authenticated=True,
        channel="whatsapp",
        active_intent="consultar_pedido",
        action_confirmed=True,
    )
    assert state.customer_id == "cust-123"
    assert state.customer_document == "11144477735"
    assert state.customer_segment == "B2C"
    assert state.authenticated is True
    assert state.channel == "whatsapp"
    assert state.active_intent == "consultar_pedido"
    assert state.action_confirmed is True


@pytest.mark.unit
def test_conversation_state_serialization() -> None:
    state = ConversationState(
        customer_id="cust-b2b",
        customer_segment="B2B",
        messages=[{"role": "user", "content": "olá"}],
    )
    dumped = state.model_dump()
    assert dumped["customer_id"] == "cust-b2b"
    assert dumped["customer_segment"] == "B2B"
    assert len(dumped["messages"]) == 1

    restored = ConversationState.model_validate(dumped)
    assert restored.customer_id == state.customer_id
    assert restored.customer_segment == state.customer_segment
    assert restored.messages == state.messages
