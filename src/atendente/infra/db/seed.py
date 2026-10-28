import asyncio
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from atendente.infra.db.database import DatabaseManager
from atendente.infra.db.models import (
    ContractSLAORM,
    CustomerORM,
    InvoiceORM,
    OrderItemORM,
    OrderORM,
)


async def seed_data(session: AsyncSession) -> None:
    now = datetime.now(UTC)

    # 1. Clientes B2C e B2B
    c1 = CustomerORM(
        id="cust_b2c_maria",
        name="Maria Silva",
        doc_type="CPF",
        doc_number="52998224725",
        segment="B2C",
        email="maria.silva@exemplo.com",
        phone="11988887777",
        created_at=now - timedelta(days=90),
    )

    c2 = CustomerORM(
        id="cust_b2c_joao",
        name="João Souza",
        doc_type="CPF",
        doc_number="00000000191",
        segment="B2C",
        email="joao.souza@exemplo.com",
        phone="21977776666",
        created_at=now - timedelta(days=60),
    )

    c3 = CustomerORM(
        id="cust_b2b_xpto",
        name="XPTO Indústria e Comércio S.A.",
        doc_type="CNPJ",
        doc_number="11222333000181",
        segment="B2B",
        email="financeiro@xpto.com.br",
        phone="1133334444",
        created_at=now - timedelta(days=365),
    )

    c4 = CustomerORM(
        id="cust_b2b_tech",
        name="Tech Solutions Ltda",
        doc_type="CNPJ",
        doc_number="00000000000191",
        segment="B2B",
        email="operacoes@techsolutions.com",
        phone="1144445555",
        created_at=now - timedelta(days=180),
    )

    session.add_all([c1, c2, c3, c4])
    await session.flush()

    # 2. Pedidos para Maria Silva (B2C)
    # Pedido recente entregue há 2 dias (Elegível para devolução/reembolso)
    ord1 = OrderORM(
        id="ord_b2c_recent",
        customer_id=c1.id,
        total_cents=49900,
        status="DELIVERED",
        delivery_date=now - timedelta(days=2),
        tracking_code="NL887766554BR",
        created_at=now - timedelta(days=5),
    )
    item1 = OrderItemORM(
        order_id=ord1.id,
        sku="SKU-WATCH-01",
        name="Smartwatch Pro NovaLoja",
        quantity=1,
        unit_price_cents=49900,
    )

    # Pedido antigo entregue há 20 dias (Inelegível para reembolso)
    ord2 = OrderORM(
        id="ord_b2c_old",
        customer_id=c1.id,
        total_cents=89900,
        status="DELIVERED",
        delivery_date=now - timedelta(days=20),
        tracking_code="NL112233445BR",
        created_at=now - timedelta(days=25),
    )
    item2 = OrderItemORM(
        order_id=ord2.id,
        sku="SKU-CHAIR-02",
        name="Cadeira Gamer Ergonomica",
        quantity=1,
        unit_price_cents=89900,
    )

    # Pedido em trânsito
    ord3 = OrderORM(
        id="ord_b2c_transit",
        customer_id=c1.id,
        total_cents=12990,
        status="SHIPPED",
        delivery_date=None,
        tracking_code="NL998877665BR",
        created_at=now - timedelta(days=1),
    )
    item3 = OrderItemORM(
        order_id=ord3.id,
        sku="SKU-MOUSE-03",
        name="Mouse Sem Fio Ultra",
        quantity=1,
        unit_price_cents=12990,
    )

    session.add_all([ord1, item1, ord2, item2, ord3, item3])

    # 3. Contratos corporativos SLA (B2B)
    con1 = ContractSLAORM(
        id="con_xpto_plat",
        customer_id=c3.id,
        tier="PLATINUM",
        response_sla_minutes=60,
        resolution_sla_hours=4,
        account_manager="Roberto Santos",
        active=True,
        created_at=now - timedelta(days=365),
    )

    con2 = ContractSLAORM(
        id="con_tech_gold",
        customer_id=c4.id,
        tier="GOLD",
        response_sla_minutes=120,
        resolution_sla_hours=8,
        account_manager="Aline Moreira",
        active=True,
        created_at=now - timedelta(days=180),
    )

    session.add_all([con1, con2])

    # 4. Faturas Corporativas B2B
    inv1 = InvoiceORM(
        id="inv_xpto_2026_09",
        customer_id=c3.id,
        period="2026-09",
        amount_cents=1500000,
        status="PAID",
        barcode="34191790010104351004791020150008899880000150000",
        due_date=date(2026, 9, 30),
        pdf_url="https://faturas.novaloja.com.br/xpto-2026-09.pdf",
        created_at=now - timedelta(days=40),
    )

    inv2 = InvoiceORM(
        id="inv_xpto_2026_10",
        customer_id=c3.id,
        period="2026-10",
        amount_cents=1500000,
        status="OPEN",
        barcode="34191790010104351004791020150008899880000150000",
        due_date=date(2026, 10, 30),
        pdf_url="https://faturas.novaloja.com.br/xpto-2026-10.pdf",
        created_at=now - timedelta(days=10),
    )

    session.add_all([inv1, inv2])
    await session.commit()
    print("Seed data successfully injected!")


async def run_seed() -> None:
    db = DatabaseManager()
    async with db.session_factory() as session:
        await seed_data(session)


if __name__ == "__main__":
    asyncio.run(run_seed())
