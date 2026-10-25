from collections.abc import Sequence
from datetime import date
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from atendente.domain.models import (
    Customer,
    CustomerSegment,
    Order,
    OrderItem,
    OrderStatus,
    RefundRequest,
    RefundStatus,
    Ticket,
    TicketPriority,
    TicketStatus,
    ContractSLA,
    ContractTier,
    Invoice,
    InvoiceStatus
)
from atendente.domain.validators import DocumentType
from atendente.infra.db.models import (
    CustomerORM,
    OrderORM,
    RefundRequestORM,
    TicketORM,
    ContractSLAORM,
    InvoiceORM
)


class PostgresRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


class CustomerRepository(PostgresRepository):
    async def find_by_doc(self, doc_number: str) -> Optional[Customer]:
        stmt = select(CustomerORM).where(CustomerORM.doc_number == doc_number)
        result = await self.session.execute(stmt)
        orm = result.scalar_one_or_none()
        if not orm:
            return None
        return Customer(
            id=orm.id,
            name=orm.name,
            doc_type=DocumentType(orm.doc_type),
            doc_number=orm.doc_number,
            segment=CustomerSegment(orm.segment),
            email=orm.email,
            phone=orm.phone,
            created_at=orm.created_at
        )

    async def find_by_id(self, customer_id: str) -> Optional[Customer]:
        stmt = select(CustomerORM).where(CustomerORM.id == customer_id)
        result = await self.session.execute(stmt)
        orm = result.scalar_one_or_none()
        if not orm:
            return None
        return Customer(
            id=orm.id,
            name=orm.name,
            doc_type=DocumentType(orm.doc_type),
            doc_number=orm.doc_number,
            segment=CustomerSegment(orm.segment),
            email=orm.email,
            phone=orm.phone,
            created_at=orm.created_at
        )


class OrderRepository(PostgresRepository):
    async def find_by_id(self, order_id: str) -> Optional[Order]:
        stmt = (
            select(OrderORM)
            .options(selectinload(OrderORM.items))
            .where(OrderORM.id == order_id)
        )
        result = await self.session.execute(stmt)
        orm = result.scalar_one_or_none()
        if not orm:
            return None

        items = [
            OrderItem(
                sku=it.sku,
                name=it.name,
                quantity=it.quantity,
                unit_price_cents=it.unit_price_cents
            )
            for it in orm.items
        ]

        return Order(
            id=orm.id,
            customer_id=orm.customer_id,
            items=items,
            total_cents=orm.total_cents,
            status=OrderStatus(orm.status),
            delivery_date=orm.delivery_date,
            tracking_code=orm.tracking_code,
            created_at=orm.created_at
        )


class RefundRepository(PostgresRepository):
    async def save(self, refund: RefundRequest) -> RefundRequest:
        orm = RefundRequestORM(
            id=refund.id,
            order_id=refund.order_id,
            customer_id=refund.customer_id,
            reason=refund.reason,
            amount_cents=refund.amount_cents,
            status=refund.status.value,
            eligible=refund.eligible,
            created_at=refund.created_at
        )
        self.session.add(orm)
        await self.session.flush()
        return refund

    async def find_by_id(self, refund_id: str) -> Optional[RefundRequest]:
        stmt = select(RefundRequestORM).where(RefundRequestORM.id == refund_id)
        result = await self.session.execute(stmt)
        orm = result.scalar_one_or_none()
        if not orm:
            return None
        return RefundRequest(
            id=orm.id,
            order_id=orm.order_id,
            customer_id=orm.customer_id,
            reason=orm.reason,
            amount_cents=orm.amount_cents,
            status=RefundStatus(orm.status),
            eligible=orm.eligible,
            created_at=orm.created_at
        )


class TicketRepository(PostgresRepository):
    async def save(self, ticket: Ticket) -> Ticket:
        orm = TicketORM(
            id=ticket.id,
            customer_id=ticket.customer_id,
            title=ticket.title,
            description=ticket.description,
            priority=ticket.priority.value,
            sla_hours=ticket.sla_hours,
            status=ticket.status.value,
            created_at=ticket.created_at
        )
        self.session.add(orm)
        await self.session.flush()
        return ticket


class ContractRepository(PostgresRepository):
    async def find_by_customer_id(self, customer_id: str) -> Optional[ContractSLA]:
        stmt = select(ContractSLAORM).where(ContractSLAORM.customer_id == customer_id)
        result = await self.session.execute(stmt)
        orm = result.scalar_one_or_none()
        if not orm:
            return None
        return ContractSLA(
            id=orm.id,
            customer_id=orm.customer_id,
            tier=ContractTier(orm.tier),
            response_sla_minutes=orm.response_sla_minutes,
            resolution_sla_hours=orm.resolution_sla_hours,
            account_manager=orm.account_manager,
            active=orm.active,
            created_at=orm.created_at
        )


class InvoiceRepository(PostgresRepository):
    async def list_by_customer(
        self,
        customer_id: str,
        period: Optional[str] = None
    ) -> Sequence[Invoice]:
        stmt = select(InvoiceORM).where(InvoiceORM.customer_id == customer_id)
        if period:
            stmt = stmt.where(InvoiceORM.period == period)
        result = await self.session.execute(stmt)
        orms = result.scalars().all()
        return [
            Invoice(
                id=orm.id,
                customer_id=orm.customer_id,
                period=orm.period,
                amount_cents=orm.amount_cents,
                status=InvoiceStatus(orm.status),
                barcode=orm.barcode,
                due_date=orm.due_date,
                pdf_url=orm.pdf_url,
                created_at=orm.created_at
            )
            for orm in orms
        ]
