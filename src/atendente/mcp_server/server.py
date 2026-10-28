from __future__ import annotations

import json
from typing import Any, Literal

from mcp.server.mcpserver import MCPServer

from atendente.tools.base import ToolResult
from atendente.tools.service import (
    AbrirChamadoInput,
    BuscarBaseConhecimentoInput,
    ConsultarContratoSLAInput,
    ConsultarFaturaInput,
    ConsultarPedidoInput,
    IdentificarClienteInput,
    NovaLojaToolsService,
    SolicitarReembolsoInput,
    TransferirParaHumanoInput,
)


def _dump_tool_result(res: ToolResult[Any]) -> str:
    return json.dumps(res.model_dump(mode="json"), ensure_ascii=False)


def create_novaloja_mcp_server(service: NovaLojaToolsService) -> MCPServer:
    """Cria e configura o servidor oficial MCP expondo as 8 Tools da NovaLoja."""
    mcp = MCPServer(
        name="novaloja-atendente-mcp",
        title="NovaLoja Atendente IA — MCP Server",
        description="Servidor Model Context Protocol oficial expondo as 8 Tools de atendimento B2C e B2B da NovaLoja.",
        version="1.0.0",
    )

    @mcp.tool(
        name="identificar_cliente",
        description="Identifica um cliente B2C (CPF) ou B2B (CNPJ) validando dígitos verificadores.",
    )
    async def mcp_identificar_cliente(doc_number: str, verification_code: str = "123456") -> str:
        res = await service.identificar_cliente(
            IdentificarClienteInput(doc_number=doc_number, verification_code=verification_code)
        )
        return _dump_tool_result(res)

    @mcp.tool(
        name="consultar_pedido",
        description="Consulta o status, valor e rastreio de um pedido validando a titularidade do cliente.",
    )
    async def mcp_consultar_pedido(order_id: str, customer_id: str) -> str:
        res = await service.consultar_pedido(
            ConsultarPedidoInput(order_id=order_id, customer_id=customer_id)
        )
        return _dump_tool_result(res)

    @mcp.tool(
        name="solicitar_reembolso",
        description="Ação sensível: solicita estorno de pedido entregue dentro da janela de 7 dias corridos.",
    )
    async def mcp_solicitar_reembolso(
        order_id: str, customer_id: str, motivo: str, confirmado: bool = False
    ) -> str:
        res = await service.solicitar_reembolso(
            SolicitarReembolsoInput(
                order_id=order_id,
                customer_id=customer_id,
                motivo=motivo,
                confirmado=confirmado,
            )
        )
        return _dump_tool_result(res)

    @mcp.tool(
        name="abrir_chamado",
        description="Abre um chamado de suporte técnico ou operacional calculando o SLA conforme segmento.",
    )
    async def mcp_abrir_chamado(
        customer_id: str,
        titulo: str,
        descricao: str,
        prioridade: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM",
    ) -> str:
        res = await service.abrir_chamado(
            AbrirChamadoInput(
                customer_id=customer_id,
                titulo=titulo,
                descricao=descricao,
                prioridade=prioridade,
            )
        )
        return _dump_tool_result(res)

    @mcp.tool(
        name="consultar_contrato_sla",
        description="Consulta parâmetros de SLA, uptime e gerente de conta de um contrato corporativo B2B.",
    )
    async def mcp_consultar_contrato_sla(customer_id: str) -> str:
        res = await service.consultar_contrato_sla(
            ConsultarContratoSLAInput(customer_id=customer_id)
        )
        return _dump_tool_result(res)

    @mcp.tool(
        name="consultar_fatura",
        description="Lista faturas consolidadas de um cliente B2B com filtro opcional por período (AAAA-MM).",
    )
    async def mcp_consultar_fatura(
        customer_id: str,
        periodo: str | None = None,
    ) -> str:
        res = await service.consultar_fatura(
            ConsultarFaturaInput(customer_id=customer_id, periodo=periodo)
        )
        return _dump_tool_result(res)

    @mcp.tool(
        name="buscar_base_conhecimento",
        description="Executa busca híbrida (vetorial + BM25 RRF) na base de conhecimento da NovaLoja.",
    )
    async def mcp_buscar_base_conhecimento(
        query: str,
        segmento: Literal["B2C", "B2B"] | None = None,
        limit: int = 3,
    ) -> str:
        res = await service.buscar_base_conhecimento(
            BuscarBaseConhecimentoInput(query=query, segmento=segmento, limit=limit)
        )
        return _dump_tool_result(res)

    @mcp.tool(
        name="transferir_para_humano",
        description="Transfere o atendimento para fila humana com contexto estruturado da conversa.",
    )
    async def mcp_transferir_para_humano(
        customer_id: str, motivo: str, resumo_conversa: str
    ) -> str:
        res = await service.transferir_para_humano(
            TransferirParaHumanoInput(
                customer_id=customer_id, motivo=motivo, resumo_conversa=resumo_conversa
            )
        )
        return _dump_tool_result(res)

    return mcp
