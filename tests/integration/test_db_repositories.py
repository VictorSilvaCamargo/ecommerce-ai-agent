import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from atendente.domain.models import CustomerSegment, OrderStatus
from atendente.infra.db.database import DatabaseManager
from atendente.infra.db.models import Base
from atendente.infra.db.repositories import (
    ContractRepository,
    CustomerRepository,
    InvoiceRepository,
    OrderRepository,
)
from atendente.infra.db.seed import seed_data


@pytest.fixture
async def test_db_session() -> AsyncSession:
    db = DatabaseManager(db_url="sqlite+aiosqlite:///:memory:")
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with db.session_factory() as session:
        await seed_data(session)
        yield session

    await db.engine.dispose()


@pytest.mark.integration
async def test_customer_repository(test_db_session: AsyncSession) -> None:
    repo = CustomerRepository(test_db_session)
    customer = await repo.find_by_doc("52998224725")
    assert customer is not None
    assert customer.name == "Maria Silva"
    assert customer.segment == CustomerSegment.B2C

    customer_b2b = await repo.find_by_doc("11222333000181")
    assert customer_b2b is not None
    assert customer_b2b.segment == CustomerSegment.B2B


@pytest.mark.integration
async def test_order_repository_with_items(test_db_session: AsyncSession) -> None:
    repo = OrderRepository(test_db_session)
    order = await repo.find_by_id("ord_b2c_recent")
    assert order is not None
    assert order.status == OrderStatus.DELIVERED
    assert len(order.items) == 1
    assert order.items[0].sku == "SKU-WATCH-01"
    assert order.total_cents == 49900


@pytest.mark.integration
async def test_contract_and_invoices_repository(test_db_session: AsyncSession) -> None:
    contract_repo = ContractRepository(test_db_session)
    invoice_repo = InvoiceRepository(test_db_session)

    contract = await contract_repo.find_by_customer_id("cust_b2b_xpto")
    assert contract is not None
    assert contract.tier.value == "PLATINUM"
    assert contract.resolution_sla_hours == 4

    invoices = await invoice_repo.list_by_customer("cust_b2b_xpto")
    assert len(invoices) == 2
