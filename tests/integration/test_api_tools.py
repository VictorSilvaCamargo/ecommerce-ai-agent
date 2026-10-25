from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from atendente.api.main import app, get_tools_service
from atendente.infra.audit import InMemoryAuditRepository
from atendente.infra.config import settings
from atendente.infra.db.database import DatabaseManager
from atendente.infra.db.models import Base
from atendente.infra.db.repositories import (
    ContractRepository,
    CustomerRepository,
    InvoiceRepository,
    OrderRepository,
    RefundRepository,
    TicketRepository,
)
from atendente.infra.db.seed import seed_data
from atendente.tools.service import NovaLojaToolsService


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    test_db = DatabaseManager(db_url="sqlite+aiosqlite:///:memory:")
    async with test_db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_db.session_factory() as session:
        await seed_data(session)

        audit_repo = InMemoryAuditRepository()

        async def override_get_tools_service() -> NovaLojaToolsService:
            return NovaLojaToolsService(
                customer_repo=CustomerRepository(session),
                order_repo=OrderRepository(session),
                refund_repo=RefundRepository(session),
                ticket_repo=TicketRepository(session),
                contract_repo=ContractRepository(session),
                invoice_repo=InvoiceRepository(session),
                audit_repo=audit_repo,
            )

        app.dependency_overrides[get_tools_service] = override_get_tools_service

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

        app.dependency_overrides.clear()

    await test_db.engine.dispose()


@pytest.mark.integration
async def test_health_check(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.integration
async def test_api_auth_failure_without_header(client: AsyncClient) -> None:
    resp = await client.post(
        "/tools/identificar-cliente",
        json={"doc_number": "52998224725", "verification_code": "123456"},
    )
    assert resp.status_code == 422  # Missing header validation error


@pytest.mark.integration
async def test_api_auth_failure_with_wrong_key(client: AsyncClient) -> None:
    resp = await client.post(
        "/tools/identificar-cliente",
        headers={"X-API-Key": "wrong-key"},
        json={"doc_number": "52998224725", "verification_code": "123456"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "HTTP_ERROR"


@pytest.mark.integration
async def test_api_identificar_cliente_success(client: AsyncClient) -> None:
    resp = await client.post(
        "/tools/identificar-cliente",
        headers={"X-API-Key": settings.api_key},
        json={"doc_number": "529.982.247-25", "verification_code": "123456"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Maria Silva"


@pytest.mark.integration
async def test_api_solicitar_reembolso_sensitive_requires_confirmation(client: AsyncClient) -> None:
    resp = await client.post(
        "/tools/solicitar-reembolso",
        headers={"X-API-Key": settings.api_key},
        json={
            "order_id": "ord_b2c_recent",
            "customer_id": "cust_b2c_maria",
            "motivo": "Arrependimento dentro do prazo",
            "confirmado": False,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "CONFIRMATION_REQUIRED"
    assert data["error"]["details"]["eligible"] is True


@pytest.mark.integration
async def test_api_solicitar_reembolso_sensitive_confirmed_success(client: AsyncClient) -> None:
    resp = await client.post(
        "/tools/solicitar-reembolso",
        headers={"X-API-Key": settings.api_key},
        json={
            "order_id": "ord_b2c_recent",
            "customer_id": "cust_b2c_maria",
            "motivo": "Arrependimento dentro do prazo",
            "confirmado": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["status"] == "APPROVED"
    assert data["data"]["amount_cents"] == 49900
