import time
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

from atendente.domain.models import (
    ContractSLA,
    Customer,
    CustomerSegment,
    Invoice,
    Order,
    RefundRequest,
    Ticket,
    TicketPriority
)
from atendente.domain.services import (
    ConfirmationRequiredError,
    IneligibleRefundError,
    RefundService,
    TicketService
)
from atendente.domain.validators import clean_digits, validate_document
from atendente.infra.audit import AuditRepository, ToolAuditEntry
from atendente.infra.db.repositories import (
    ContractRepository,
    CustomerRepository,
    InvoiceRepository,
    OrderRepository,
    RefundRepository,
    TicketRepository
)
from atendente.tools.base import ToolResult


# --- Schemas de Entrada das Tools ---

class IdentificarClienteInput(BaseModel):
    doc_number: str = Field(description="Número de CPF (11 dígitos) ou CNPJ (14 dígitos), com ou sem pontuação")
    verification_code: str = Field(description="Código numérico de verificação simulado de 6 dígitos (ex: '123456')")


class ConsultarPedidoInput(BaseModel):
    order_id: str = Field(description="Identificador único do pedido (ex: 'ord_b2c_recent')")
    customer_id: str = Field(description="ID do cliente solicitante para validação de posse")


class SolicitarReembolsoInput(BaseModel):
    order_id: str = Field(description="ID do pedido entregue para devolução/estorno")
    customer_id: str = Field(description="ID do cliente solicitante")
    motivo: str = Field(description="Motivo detalhado da devolução ou arrependimento")
    confirmado: bool = Field(default=False, description="Flag explícita de confirmação da ação sensível")


class AbrirChamadoInput(BaseModel):
    customer_id: str = Field(description="ID do cliente solicitante")
    titulo: str = Field(description="Título objetivo do chamado técnico ou solicitação")
    descricao: str = Field(description="Descrição detalhada do problema ou dúvida")
    prioridade: Optional[str] = Field(default="MEDIUM", description="Nível de prioridade: LOW, MEDIUM, HIGH, CRITICAL")


class ConsultarContratoSLAInput(BaseModel):
    customer_id: str = Field(description="ID da empresa cliente B2B")


class ConsultarFaturaInput(BaseModel):
    customer_id: str = Field(description="ID do cliente B2B")
    periodo: Optional[str] = Field(default=None, description="Período da fatura no formato AAAA-MM (ex: '2026-10')")


class BuscarBaseConhecimentoInput(BaseModel):
    query: str = Field(description="Pergunta ou termo de pesquisa para a base de conhecimento")
    segmento: Optional[str] = Field(default=None, description="Filtro opcional de segmento: 'B2C' ou 'B2B'")
    limit: int = Field(default=3, ge=1, le=10, description="Número máximo de artigos ou seções a recuperar")


class TransferirParaHumanoInput(BaseModel):
    customer_id: str = Field(description="ID do cliente a ser transferido")
    motivo: str = Field(description="Motivo do transbordo humano")
    resumo_conversa: str = Field(description="Resumo contextual dos turnos anteriores")


# --- Classe Central de Execução das Tools ---

class NovaLojaToolsService:
    def __init__(
        self,
        customer_repo: CustomerRepository,
        order_repo: OrderRepository,
        refund_repo: RefundRepository,
        ticket_repo: TicketRepository,
        contract_repo: ContractRepository,
        invoice_repo: InvoiceRepository,
        audit_repo: AuditRepository,
        refund_service: Optional[RefundService] = None,
        ticket_service: Optional[TicketService] = None,
    ):
        self.customer_repo = customer_repo
        self.order_repo = order_repo
        self.refund_repo = refund_repo
        self.ticket_repo = ticket_repo
        self.contract_repo = contract_repo
        self.invoice_repo = invoice_repo
        self.audit_repo = audit_repo
        self.refund_service = refund_service or RefundService()
        self.ticket_service = ticket_service or TicketService()

    def _serialize_data(self, data: Any) -> Any:
        if data is None:
            return None
        if hasattr(data, "model_dump"):
            return data.model_dump()
        if isinstance(data, list):
            return [self._serialize_data(item) for item in data]
        if isinstance(data, dict):
            return {k: self._serialize_data(v) for k, v in data.items()}
        return data

    async def _audit(
        self,
        tool_name: str,
        customer_id: Optional[str],
        input_payload: dict[str, Any],
        start_time: float,
        result: ToolResult[Any]
    ) -> None:
        latency = (time.perf_counter() - start_time) * 1000
        output_payload = self._serialize_data(result.data)
        error_payload = result.error.model_dump() if result.error else None

        entry = ToolAuditEntry(
            tool_name=tool_name,
            customer_id=customer_id,
            input_payload=input_payload,
            output_payload=output_payload,
            error=error_payload,
            latency_ms=round(latency, 2),
            timestamp=datetime.now(timezone.utc)
        )
        await self.audit_repo.log_tool_execution(entry)

    # 1. identificar_cliente
    async def identificar_cliente(self, payload: IdentificarClienteInput) -> ToolResult[Customer]:
        start = time.perf_counter()
        try:
            _, clean_doc = validate_document(payload.doc_number)
        except ValueError:
            res = ToolResult.fail("INVALID_DOCUMENT", "CPF ou CNPJ inválido.", retryable=True)
            await self._audit("identificar_cliente", None, payload.model_dump(), start, res)
            return res

        # Validação do código de verificação simulado
        clean_code = clean_digits(payload.verification_code)
        if len(clean_code) != 6:
            res = ToolResult.fail("INVALID_VERIFICATION_CODE", "O código de verificação deve ter 6 dígitos numéricos.", retryable=True)
            await self._audit("identificar_cliente", None, payload.model_dump(), start, res)
            return res

        customer = await self.customer_repo.find_by_doc(clean_doc)
        if not customer:
            res = ToolResult.fail("CUSTOMER_NOT_FOUND", "Nenhum cliente cadastrado foi encontrado com esse documento.", retryable=False)
            await self._audit("identificar_cliente", None, payload.model_dump(), start, res)
            return res

        res = ToolResult.ok(customer)
        await self._audit("identificar_cliente", customer.id, payload.model_dump(), start, res)
        return res

    # 2. consultar_pedido
    async def consultar_pedido(self, payload: ConsultarPedidoInput) -> ToolResult[Order]:
        start = time.perf_counter()
        order = await self.order_repo.find_by_id(payload.order_id)
        if not order:
            res = ToolResult.fail("ORDER_NOT_FOUND", f"Pedido {payload.order_id} não encontrado.", retryable=False)
            await self._audit("consultar_pedido", payload.customer_id, payload.model_dump(), start, res)
            return res

        if order.customer_id != payload.customer_id:
            res = ToolResult.fail("UNAUTHORIZED_ACCESS", "O pedido informado não pertence ao cliente autenticado.", retryable=False)
            await self._audit("consultar_pedido", payload.customer_id, payload.model_dump(), start, res)
            return res

        res = ToolResult.ok(order)
        await self._audit("consultar_pedido", payload.customer_id, payload.model_dump(), start, res)
        return res

    # 3. solicitar_reembolso (Ação Sensível)
    async def solicitar_reembolso(self, payload: SolicitarReembolsoInput) -> ToolResult[RefundRequest]:
        start = time.perf_counter()
        order = await self.order_repo.find_by_id(payload.order_id)
        if not order:
            res = ToolResult.fail("ORDER_NOT_FOUND", f"Pedido {payload.order_id} não encontrado.", retryable=False)
            await self._audit("solicitar_reembolso", payload.customer_id, payload.model_dump(), start, res)
            return res

        if order.customer_id != payload.customer_id:
            res = ToolResult.fail("UNAUTHORIZED_ACCESS", "O pedido informado não pertence ao cliente autenticado.", retryable=False)
            await self._audit("solicitar_reembolso", payload.customer_id, payload.model_dump(), start, res)
            return res

        try:
            refund = self.refund_service.create_refund(
                order=order,
                reason=payload.motivo,
                confirmed=payload.confirmado
            )
            saved_refund = await self.refund_repo.save(refund)
            res = ToolResult.ok(saved_refund)
            await self._audit("solicitar_reembolso", payload.customer_id, payload.model_dump(), start, res)
            return res
        except ConfirmationRequiredError as e:
            res = ToolResult.fail(
                code="CONFIRMATION_REQUIRED",
                message=str(e),
                retryable=True,
                details={
                    "order_id": order.id,
                    "amount_cents": order.total_cents,
                    "reason": payload.motivo,
                    "eligible": True
                }
            )
            await self._audit("solicitar_reembolso", payload.customer_id, payload.model_dump(), start, res)
            return res
        except IneligibleRefundError as e:
            res = ToolResult.fail(
                code="INELIGIBLE_REFUND",
                message=str(e),
                retryable=False,
                details={"order_id": order.id, "eligible": False}
            )
            await self._audit("solicitar_reembolso", payload.customer_id, payload.model_dump(), start, res)
            return res

    # 4. abrir_chamado
    async def abrir_chamado(self, payload: AbrirChamadoInput) -> ToolResult[Ticket]:
        start = time.perf_counter()
        customer = await self.customer_repo.find_by_id(payload.customer_id)
        if not customer:
            res = ToolResult.fail("CUSTOMER_NOT_FOUND", "Cliente não identificado para abertura de chamado.", retryable=False)
            await self._audit("abrir_chamado", payload.customer_id, payload.model_dump(), start, res)
            return res

        try:
            priority = TicketPriority(payload.prioridade.upper() if payload.prioridade else "MEDIUM")
        except ValueError:
            res = ToolResult.fail("INVALID_PRIORITY", "Prioridade inválida. Utilize LOW, MEDIUM, HIGH ou CRITICAL.", retryable=True)
            await self._audit("abrir_chamado", payload.customer_id, payload.model_dump(), start, res)
            return res

        contract = await self.contract_repo.find_by_customer_id(customer.id)
        sla_hours = self.ticket_service.calculate_sla(customer.segment, priority, contract)

        ticket = Ticket(
            id=f"tkt_{uuid4().hex[:8]}",
            customer_id=customer.id,
            title=payload.titulo,
            description=payload.descricao,
            priority=priority,
            sla_hours=sla_hours
        )
        saved_ticket = await self.ticket_repo.save(ticket)
        res = ToolResult.ok(saved_ticket)
        await self._audit("abrir_chamado", customer.id, payload.model_dump(), start, res)
        return res

    # 5. consultar_contrato_sla
    async def consultar_contrato_sla(self, payload: ConsultarContratoSLAInput) -> ToolResult[ContractSLA]:
        start = time.perf_counter()
        customer = await self.customer_repo.find_by_id(payload.customer_id)
        if not customer:
            res = ToolResult.fail("CUSTOMER_NOT_FOUND", "Cliente não encontrado.", retryable=False)
            await self._audit("consultar_contrato_sla", payload.customer_id, payload.model_dump(), start, res)
            return res

        if customer.segment != CustomerSegment.B2B:
            res = ToolResult.fail("NOT_B2B_CUSTOMER", "Consulta de contrato e SLA disponível exclusivamente para clientes corporativos (B2B).", retryable=False)
            await self._audit("consultar_contrato_sla", payload.customer_id, payload.model_dump(), start, res)
            return res

        contract = await self.contract_repo.find_by_customer_id(customer.id)
        if not contract:
            res = ToolResult.fail("CONTRACT_NOT_FOUND", "Nenhum contrato SLA ativo encontrado para este cliente.", retryable=False)
            await self._audit("consultar_contrato_sla", payload.customer_id, payload.model_dump(), start, res)
            return res

        res = ToolResult.ok(contract)
        await self._audit("consultar_contrato_sla", payload.customer_id, payload.model_dump(), start, res)
        return res

    # 6. consultar_fatura
    async def consultar_fatura(self, payload: ConsultarFaturaInput) -> ToolResult[list[Invoice]]:
        start = time.perf_counter()
        invoices = await self.invoice_repo.list_by_customer(payload.customer_id, payload.periodo)
        if not invoices:
            res = ToolResult.fail("INVOICE_NOT_FOUND", "Nenhuma fatura encontrada para o período informado.", retryable=True)
            await self._audit("consultar_fatura", payload.customer_id, payload.model_dump(), start, res)
            return res

        res = ToolResult.ok(list(invoices))
        await self._audit("consultar_fatura", payload.customer_id, payload.model_dump(), start, res)
        return res

    # 7. buscar_base_conhecimento
    async def buscar_base_conhecimento(self, payload: BuscarBaseConhecimentoInput) -> ToolResult[list[dict[str, Any]]]:
        start = time.perf_counter()
        # Interface padrão da Tool: integrada com RAG na Fase 2
        mock_results = [
            {
                "title": "Política de Trocas e Devoluções",
                "content": "O cliente pode solicitar devolução por arrependimento em até 7 dias corridos após a entrega do produto.",
                "source": "manual_politicas_b2c.md",
                "score": 0.95
            }
        ]
        res = ToolResult.ok(mock_results)
        await self._audit("buscar_base_conhecimento", None, payload.model_dump(), start, res)
        return res

    # 8. transferir_para_humano
    async def transferir_para_humano(self, payload: TransferirParaHumanoInput) -> ToolResult[dict[str, Any]]:
        start = time.perf_counter()
        handoff_data = {
            "protocolo": f"HND-{uuid4().hex[:8].upper()}",
            "customer_id": payload.customer_id,
            "motivo": payload.motivo,
            "resumo": payload.resumo_conversa,
            "status": "TRANSFERRED",
            "fila": "Atendimento Humano Especializado N2",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        res = ToolResult.ok(handoff_data)
        await self._audit("transferir_para_humano", payload.customer_id, payload.model_dump(), start, res)
        return res
