from typing import Any

from atendente.tools.service import (
    AbrirChamadoInput,
    BuscarBaseConhecimentoInput,
    ConsultarContratoSLAInput,
    ConsultarFaturaInput,
    ConsultarPedidoInput,
    IdentificarClienteInput,
    SolicitarReembolsoInput,
    TransferirParaHumanoInput,
)

TOOL_DEFINITIONS: dict[str, dict[str, Any]] = {
    "identificar_cliente": {
        "name": "identificar_cliente",
        "description": "Identifica e valida o cliente NovaLoja através do CPF ou CNPJ e código numérico de 6 dígitos.",
        "parameters": IdentificarClienteInput.model_json_schema(),
    },
    "consultar_pedido": {
        "name": "consultar_pedido",
        "description": "Consulta o status detalhado, lista de itens e código de rastreamento de um pedido B2C.",
        "parameters": ConsultarPedidoInput.model_json_schema(),
    },
    "solicitar_reembolso": {
        "name": "solicitar_reembolso",
        "description": "AÇÃO SENSÍVEL: Solicita devolução e reembolso integral de um pedido entregue há no máximo 7 dias. Exige confirmado=true.",
        "parameters": SolicitarReembolsoInput.model_json_schema(),
    },
    "abrir_chamado": {
        "name": "abrir_chamado",
        "description": "Abre um chamado técnico com priorização e cálculo automático de SLA corporativo.",
        "parameters": AbrirChamadoInput.model_json_schema(),
    },
    "consultar_contrato_sla": {
        "name": "consultar_contrato_sla",
        "description": "Consulta os termos contratuais, nível de serviço (SLA) e gerente de conta de clientes B2B.",
        "parameters": ConsultarContratoSLAInput.model_json_schema(),
    },
    "consultar_fatura": {
        "name": "consultar_fatura",
        "description": "Consulta faturas e boletos consolidados para clientes corporativos B2B por período.",
        "parameters": ConsultarFaturaInput.model_json_schema(),
    },
    "buscar_base_conhecimento": {
        "name": "buscar_base_conhecimento",
        "description": "Pesquisa artigos de políticas, manuais e regulamentos internos na base de conhecimento NovaLoja.",
        "parameters": BuscarBaseConhecimentoInput.model_json_schema(),
    },
    "transferir_para_humano": {
        "name": "transferir_para_humano",
        "description": "Transfere o atendimento para um operador humano quando a solicitação excede a autonomia do agente.",
        "parameters": TransferirParaHumanoInput.model_json_schema(),
    },
}


def get_tool_definitions() -> list[dict[str, Any]]:
    """Retorna a lista canônica de definições de function calling para orquestradores de LLM."""
    return list(TOOL_DEFINITIONS.values())
