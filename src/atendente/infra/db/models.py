from datetime import UTC, date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CustomerORM(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(10), nullable=False)
    doc_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    segment: Mapped[str] = mapped_column(String(10), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    orders: Mapped[list["OrderORM"]] = relationship("OrderORM", back_populates="customer")
    tickets: Mapped[list["TicketORM"]] = relationship("TicketORM", back_populates="customer")
    contract: Mapped[Optional["ContractSLAORM"]] = relationship(
        "ContractSLAORM", back_populates="customer", uselist=False
    )
    invoices: Mapped[list["InvoiceORM"]] = relationship("InvoiceORM", back_populates="customer")


class OrderORM(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("customers.id"), nullable=False, index=True
    )
    total_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    delivery_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tracking_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    customer: Mapped["CustomerORM"] = relationship("CustomerORM", back_populates="orders")
    items: Mapped[list["OrderItemORM"]] = relationship(
        "OrderItemORM", back_populates="order", cascade="all, delete-orphan"
    )
    refunds: Mapped[list["RefundRequestORM"]] = relationship(
        "RefundRequestORM", back_populates="order"
    )


class OrderItemORM(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("orders.id"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped["OrderORM"] = relationship("OrderORM", back_populates="items")


class RefundRequestORM(Base):
    __tablename__ = "refund_requests"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    order_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("orders.id"), nullable=False, index=True
    )
    customer_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("customers.id"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    eligible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    order: Mapped["OrderORM"] = relationship("OrderORM", back_populates="refunds")


class TicketORM(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("customers.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(30), nullable=False)
    sla_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    customer: Mapped["CustomerORM"] = relationship("CustomerORM", back_populates="tickets")


class ContractSLAORM(Base):
    __tablename__ = "contracts_sla"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("customers.id"), unique=True, nullable=False
    )
    tier: Mapped[str] = mapped_column(String(30), nullable=False)
    response_sla_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    resolution_sla_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    account_manager: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    customer: Mapped["CustomerORM"] = relationship("CustomerORM", back_populates="contract")


class InvoiceORM(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("customers.id"), nullable=False, index=True
    )
    period: Mapped[str] = mapped_column(String(10), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    barcode: Mapped[str] = mapped_column(String(100), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    pdf_url: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    customer: Mapped["CustomerORM"] = relationship("CustomerORM", back_populates="invoices")
