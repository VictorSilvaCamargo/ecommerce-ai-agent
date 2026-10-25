from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from atendente.agent.nodes import AgentNodeHandler
from atendente.agent.state import ConversationState


def route_after_classify(state: ConversationState) -> str:
    """Roteia o fluxo a partir da intenção classificada e condições de contorno."""
    # 1. Condições de transbordo humano
    if (
        state.active_intent == "falar_com_atendente"
        or state.consecutive_unresolved_turns >= 3
        or state.frustration_detected
    ):
        return "evaluate_handoff"

    # 2. Execução de ferramentas e ações pendentes/confirmação
    if (
        state.active_intent
        in (
            "consultar_pedido",
            "solicitar_reembolso",
            "consultar_fatura",
            "consultar_contrato_sla",
            "abrir_chamado",
            "confirmar_acao",
            "cancelar_acao",
        )
        or state.pending_action is not None
    ):
        return "decide_tool"

    # 3. Consulta à base de conhecimento RAG
    if state.active_intent == "duvida_geral":
        return "retrieve_context"

    # 4. Resposta conversacional direta
    return "respond"


def build_conversation_graph(handler: AgentNodeHandler, checkpointer: Any = None) -> Any:
    """Constrói e compila o grafo de atendimento inteligente da NovaLoja com LangGraph."""
    builder = StateGraph(ConversationState)

    # 1. Registro dos nós funcionais
    builder.add_node("summarize_history", handler.summarize_history)
    builder.add_node("identify", handler.identify)
    builder.add_node("classify_intent", handler.classify_intent)
    builder.add_node("evaluate_handoff", handler.evaluate_handoff)
    builder.add_node("decide_tool", handler.decide_tool)
    builder.add_node("confirm_action", handler.confirm_action)
    builder.add_node("retrieve_context", handler.retrieve_context)
    builder.add_node("respond", handler.respond)

    # 2. Transições sequenciais e de entrada
    builder.add_edge(START, "summarize_history")
    builder.add_edge("summarize_history", "identify")
    builder.add_edge("identify", "classify_intent")

    # 3. Arestas condicionais após classificação
    builder.add_conditional_edges(
        "classify_intent",
        route_after_classify,
        {
            "evaluate_handoff": "evaluate_handoff",
            "decide_tool": "decide_tool",
            "retrieve_context": "retrieve_context",
            "respond": "respond",
        },
    )

    # 4. Transições das ramificações para a resposta e término
    builder.add_edge("decide_tool", "confirm_action")
    builder.add_edge("confirm_action", "respond")
    builder.add_edge("retrieve_context", "respond")
    builder.add_edge("respond", END)
    builder.add_edge("evaluate_handoff", END)

    saver = checkpointer if checkpointer is not None else MemorySaver()
    return builder.compile(checkpointer=saver)
