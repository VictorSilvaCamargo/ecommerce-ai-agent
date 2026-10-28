import pytest

from atendente.api.main import app
from atendente.tools.schemas import TOOL_DEFINITIONS


@pytest.mark.contract
def test_contract_tools_parameters_match_openapi() -> None:
    """
    Teste de Contrato estrito:
    Garante que os parâmetros e propriedades declarados para Function Calling do LLM
    coincidem exatamente com os schemas de entrada da especificação OpenAPI do FastAPI.
    Se divergirem, o build falha.
    """
    openapi_schema = app.openapi()
    schemas = openapi_schema.get("components", {}).get("schemas", {})

    mapping = {
        "identificar_cliente": "IdentificarClienteInput",
        "consultar_pedido": "ConsultarPedidoInput",
        "solicitar_reembolso": "SolicitarReembolsoInput",
        "abrir_chamado": "AbrirChamadoInput",
        "consultar_contrato_sla": "ConsultarContratoSLAInput",
        "consultar_fatura": "ConsultarFaturaInput",
        "buscar_base_conhecimento": "BuscarBaseConhecimentoInput",
        "transferir_para_humano": "TransferirParaHumanoInput",
    }

    for tool_name, schema_name in mapping.items():
        assert tool_name in TOOL_DEFINITIONS, f"Tool {tool_name} ausente em TOOL_DEFINITIONS"
        assert schema_name in schemas, f"Schema {schema_name} ausente na documentação OpenAPI"

        tool_params = TOOL_DEFINITIONS[tool_name]["parameters"]
        openapi_properties = schemas[schema_name].get("properties", {})
        tool_properties = tool_params.get("properties", {})

        # As propriedades esperadas devem ser idênticas
        assert set(openapi_properties.keys()) == set(tool_properties.keys()), (
            f"Divergência de contrato na Tool '{tool_name}': "
            f"OpenAPI={set(openapi_properties.keys())} vs Tool={set(tool_properties.keys())}"
        )
