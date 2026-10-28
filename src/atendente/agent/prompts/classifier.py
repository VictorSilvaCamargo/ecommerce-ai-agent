from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from atendente.agent.prompts.system import PromptVersion

IntentType = Literal[
    "consultar_pedido",
    "solicitar_reembolso",
    "consultar_fatura",
    "consultar_contrato_sla",
    "abrir_chamado",
    "duvida_geral",
    "falar_com_atendente",
    "confirmar_acao",
    "cancelar_acao",
]


class IntentClassificationOutput(BaseModel):
    """Schema Pydantic para saída estruturada obrigatória do classificador de intenção."""

    model_config = ConfigDict(extra="forbid")

    intent: IntentType = Field(
        description="Intenção canônica classificada para a mensagem do cliente"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Grau de confiança da classificação entre 0.0 e 1.0"
    )
    frustration_detected: bool = Field(
        default=False,
        description="True se houver linguagem hostil, ameaça de PROCON ou frustração intensa",
    )
    extracted_order_id: str | None = Field(
        default=None, description="ID do pedido extraído quando mencionado (ex: ord_b2c_recent)"
    )
    reasoning: str = Field(
        description="Justificativa curta e determinística para a intenção escolhida"
    )


CLASSIFIER_PROMPT_V3 = PromptVersion(
    version="v3.0.0",
    name="novaloja_intent_classifier_few_shot",
    description="Classificador de intenções com exemplos Few-Shot por intenção e schema estruturado.",
    template=(
        "Você é o Classificador de Intenções da NovaLoja. Analise a mensagem do cliente e retorne "
        "EXCLUSIVAMENTE um objeto JSON aderente ao schema `IntentClassificationOutput`.\n\n"
        "# EXEMPLOS FEW-SHOT POR INTENÇÃO\n"
        "- Cliente (B2C): 'Onde está meu pedido ord_b2c_recent? Quero o código de rastreio.'\n"
        '  -> {"intent": "consultar_pedido", "confidence": 0.99, "frustration_detected": false, '
        '"extracted_order_id": "ord_b2c_recent", "reasoning": "Consulta de status e rastreio de pedido."}\n\n'
        "- Cliente (B2C): 'O produto veio quebrado, quero meu dinheiro de volta do pedido ord_b2c_recent!'\n"
        '  -> {"intent": "solicitar_reembolso", "confidence": 0.98, "frustration_detected": false, '
        '"extracted_order_id": "ord_b2c_recent", "reasoning": "Solicitação explícita de estorno/reembolso."}\n\n'
        "- Cliente (B2B): 'Preciso da segunda via dos boletos e faturas consolidadas de outubro.'\n"
        '  -> {"intent": "consultar_fatura", "confidence": 0.97, "frustration_detected": false, '
        '"extracted_order_id": null, "reasoning": "Consulta financeira de faturas B2B."}\n\n'
        "- Cliente (B2B): 'Qual é o tempo de resolução no nosso contrato SLA Platinum?'\n"
        '  -> {"intent": "consultar_contrato_sla", "confidence": 0.96, "frustration_detected": false, '
        '"extracted_order_id": null, "reasoning": "Consulta de parâmetros contratuais de SLA."}\n\n'
        "- Cliente (B2B): 'Nosso servidor dedicado parou tudo! Abram um chamado crítico imediatamente!'\n"
        '  -> {"intent": "abrir_chamado", "confidence": 0.95, "frustration_detected": true, '
        '"extracted_order_id": null, "reasoning": "Abertura de ticket técnico de emergência."}\n\n'
        "- Cliente (Geral): 'Qual é o prazo legal de arrependimento segundo o CDC?'\n"
        '  -> {"intent": "duvida_geral", "confidence": 0.95, "frustration_detected": false, '
        '"extracted_order_id": null, "reasoning": "Dúvida conceitual sobre política para busca no RAG."}\n\n'
        "- Cliente (Geral): 'Isso é um absurdo! Quero falar com um atendente humano agora mesmo!'\n"
        '  -> {"intent": "falar_com_atendente", "confidence": 0.99, "frustration_detected": true, '
        '"extracted_order_id": null, "reasoning": "Pedido explícito de transbordo humano com frustração."}\n'
    ),
)


def build_classifier_prompt(user_message: str, segment: str = "INDEFINIDO") -> str:
    """Constrói o prompt completo de classificação injetando segmento e mensagem."""
    return (
        f"{CLASSIFIER_PROMPT_V3.template}\n"
        f"# ENTRADA ATUAL\n"
        f"Segmento Identificado: {segment}\n"
        f"Mensagem do Cliente: {user_message}\n"
    )
