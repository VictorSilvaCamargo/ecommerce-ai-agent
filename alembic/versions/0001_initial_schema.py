"""Initial schema for NovaLoja Atendente IA (Expand/Contract foundation)

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-25 15:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Tabela de Clientes
    op.create_table(
        "customers",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("doc_type", sa.String(length=10), nullable=False),
        sa.Column("doc_number", sa.String(length=20), nullable=False),
        sa.Column("segment", sa.String(length=10), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_customers_doc_number"), "customers", ["doc_number"], unique=True)

    # 2. Tabela de Pedidos
    op.create_table(
        "orders",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("customer_id", sa.String(length=50), nullable=False),
        sa.Column("total_cents", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("delivery_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tracking_code", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_orders_customer_id"), "orders", ["customer_id"], unique=False)

    # 3. Tabela de Itens do Pedido
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.String(length=50), nullable=False),
        sa.Column("sku", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_items_order_id"), "order_items", ["order_id"], unique=False)

    # 4. Tabela de Solicitações de Reembolso
    op.create_table(
        "refund_requests",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("order_id", sa.String(length=50), nullable=False),
        sa.Column("customer_id", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("eligible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_refund_requests_customer_id"), "refund_requests", ["customer_id"], unique=False
    )
    op.create_index(
        op.f("ix_refund_requests_order_id"), "refund_requests", ["order_id"], unique=False
    )

    # 5. Tabela de Tickets / Chamados
    op.create_table(
        "tickets",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("customer_id", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=30), nullable=False),
        sa.Column("sla_hours", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tickets_customer_id"), "tickets", ["customer_id"], unique=False)

    # 6. Tabela de Contratos e SLAs Corporativos
    op.create_table(
        "contracts_sla",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("customer_id", sa.String(length=50), nullable=False),
        sa.Column("tier", sa.String(length=30), nullable=False),
        sa.Column("response_sla_minutes", sa.Integer(), nullable=False),
        sa.Column("resolution_sla_hours", sa.Integer(), nullable=False),
        sa.Column("account_manager", sa.String(length=255), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("customer_id"),
    )

    # 7. Tabela de Faturas
    op.create_table(
        "invoices",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("customer_id", sa.String(length=50), nullable=False),
        sa.Column("period", sa.String(length=10), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("barcode", sa.String(length=100), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("pdf_url", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_invoices_customer_id"), "invoices", ["customer_id"], unique=False)


def downgrade() -> None:
    op.drop_table("invoices")
    op.drop_table("contracts_sla")
    op.drop_table("tickets")
    op.drop_table("refund_requests")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("customers")
