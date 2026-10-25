from datetime import UTC, date, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from atendente.domain.validators import DocumentType, validate_cnpj, validate_cpf


class CustomerSegment(StrEnum):
    B2C = "B2C"
    B2B = "B2B"


class OrderStatus(StrEnum):
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class RefundStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class TicketPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TicketStatus(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"


class ContractTier(StrEnum):
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"
    ENTERPRISE = "ENTERPRISE"


class InvoiceStatus(StrEnum):
    PAID = "PAID"
    OPEN = "OPEN"
    OVERDUE = "OVERDUE"


class Customer(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: f"cust_{uuid4().hex[:8]}")
    name: str
    doc_type: DocumentType
    doc_number: str
    segment: CustomerSegment
    email: str
    phone: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def validate_doc(self) -> bool:
        if self.doc_type == DocumentType.CPF:
            return validate_cpf(self.doc_number)
        return validate_cnpj(self.doc_number)


class OrderItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    sku: str
    name: str
    quantity: int = Field(ge=1)
    unit_price_cents: int = Field(ge=0)


class Order(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: f"ord_{uuid4().hex[:8]}")
    customer_id: str
    items: list[OrderItem]
    total_cents: int
    status: OrderStatus
    delivery_date: datetime | None = None
    tracking_code: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RefundRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: f"ref_{uuid4().hex[:8]}")
    order_id: str
    customer_id: str
    reason: str
    amount_cents: int
    status: RefundStatus = RefundStatus.PENDING
    eligible: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Ticket(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: f"tkt_{uuid4().hex[:8]}")
    customer_id: str
    title: str
    description: str
    priority: TicketPriority = TicketPriority.MEDIUM
    sla_hours: int = 24
    status: TicketStatus = TicketStatus.OPEN
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ContractSLA(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: f"con_{uuid4().hex[:8]}")
    customer_id: str
    tier: ContractTier
    response_sla_minutes: int
    resolution_sla_hours: int
    account_manager: str
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Invoice(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: f"inv_{uuid4().hex[:8]}")
    customer_id: str
    period: str  # ex: "2026-09"
    amount_cents: int
    status: InvoiceStatus = InvoiceStatus.OPEN
    barcode: str
    due_date: date
    pdf_url: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
