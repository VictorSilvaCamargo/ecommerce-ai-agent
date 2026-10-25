from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4
from atendente.domain.models import (
    CustomerSegment,
    Order,
    OrderStatus,
    RefundRequest,
    RefundStatus,
    TicketPriority,
    ContractSLA,
    ContractTier
)


class DomainError(Exception):
    """Exceção base para regras de negócio do domínio."""


class IneligibleRefundError(DomainError):
    """Lançada quando um pedido não é elegível para reembolso."""


class ConfirmationRequiredError(DomainError):
    """Lançada quando uma ação sensível requer confirmação explícita prévia."""


class RefundService:
    """
    Serviço de domínio responsável por aplicar as regras de negócio
    de devolução e reembolso da NovaLoja (Art. 49 do Código de Defesa do Consumidor).
    """

    MAX_REFUND_DAYS = 7

    def check_eligibility(
        self,
        order: Order,
        current_time: Optional[datetime] = None
    ) -> tuple[bool, str]:
        """
        Verifica se o pedido pode ser reembolsado.
        Regra:
        1. Pedido precisa estar com status DELIVERED.
        2. Data de entrega não pode ser superior a 7 dias corridos.
        """
        now = current_time or datetime.now(timezone.utc)

        if order.status != OrderStatus.DELIVERED:
            return False, f"Pedido {order.id} não foi entregue (status atual: {order.status.value})."

        if not order.delivery_date:
            return False, f"Pedido {order.id} não possui data de entrega registrada."

        delivery = order.delivery_date
        if delivery.tzinfo is None:
            delivery = delivery.replace(tzinfo=timezone.utc)

        days_since_delivery = (now - delivery).days
        if days_since_delivery > self.MAX_REFUND_DAYS:
            return (
                False,
                f"Prazo legal de {self.MAX_REFUND_DAYS} dias para devolução/arrependimento "
                f"expirado (entregue há {days_since_delivery} dias)."
            )

        return True, "Pedido elegível para devolução e reembolso integral."

    def create_refund(
        self,
        order: Order,
        reason: str,
        confirmed: bool,
        current_time: Optional[datetime] = None
    ) -> RefundRequest:
        """
        Cria a solicitação de reembolso.
        Exige elegibilidade estrita e confirmação explícita (ação sensível).
        """
        now = current_time or datetime.now(timezone.utc)
        eligible, eligibility_reason = self.check_eligibility(order, now)

        if not eligible:
            raise IneligibleRefundError(eligibility_reason)

        if not confirmed:
            raise ConfirmationRequiredError(
                f"Confirmação explícita pendente para o reembolso do pedido {order.id} "
                f"no valor de R$ {order.total_cents / 100:.2f}."
            )

        return RefundRequest(
            id=f"ref_{uuid4().hex[:8]}",
            order_id=order.id,
            customer_id=order.customer_id,
            reason=reason,
            amount_cents=order.total_cents,
            status=RefundStatus.APPROVED,
            eligible=True,
            created_at=now
        )


class TicketService:
    """
    Serviço de domínio responsável por aplicar as regras de SLA
    de abertura de chamados técnicos para clientes B2C e B2B.
    """

    B2B_SLA_MATRIX: dict[ContractTier, dict[TicketPriority, int]] = {
        ContractTier.ENTERPRISE: {
            TicketPriority.CRITICAL: 1,
            TicketPriority.HIGH: 2,
            TicketPriority.MEDIUM: 4,
            TicketPriority.LOW: 8,
        },
        ContractTier.PLATINUM: {
            TicketPriority.CRITICAL: 2,
            TicketPriority.HIGH: 4,
            TicketPriority.MEDIUM: 8,
            TicketPriority.LOW: 12,
        },
        ContractTier.GOLD: {
            TicketPriority.CRITICAL: 4,
            TicketPriority.HIGH: 8,
            TicketPriority.MEDIUM: 12,
            TicketPriority.LOW: 24,
        },
    }

    B2C_SLA_MATRIX: dict[TicketPriority, int] = {
        TicketPriority.CRITICAL: 12,
        TicketPriority.HIGH: 24,
        TicketPriority.MEDIUM: 48,
        TicketPriority.LOW: 72,
    }

    def calculate_sla(
        self,
        segment: CustomerSegment,
        priority: TicketPriority,
        contract: Optional[ContractSLA] = None
    ) -> int:
        """Calcula o SLA em horas baseado no segmento e contrato do cliente."""
        if segment == CustomerSegment.B2B and contract and contract.active:
            tier_matrix = self.B2B_SLA_MATRIX.get(contract.tier, self.B2B_SLA_MATRIX[ContractTier.GOLD])
            return tier_matrix.get(priority, 24)

        return self.B2C_SLA_MATRIX.get(priority, 48)
