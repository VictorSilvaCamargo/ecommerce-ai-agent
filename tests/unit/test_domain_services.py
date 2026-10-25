from datetime import datetime, timedelta, timezone
import pytest
from atendente.domain.models import (
    Customer,
    CustomerSegment,
    Order,
    OrderItem,
    OrderStatus,
    TicketPriority,
    ContractSLA,
    ContractTier,
    RefundStatus
)
from atendente.domain.validators import DocumentType
from atendente.domain.services import (
    RefundService,
    TicketService,
    IneligibleRefundError,
    ConfirmationRequiredError
)


@pytest.fixture
def sample_customer_b2c() -> Customer:
    return Customer(
        id="cust_b2c_1",
        name="Maria Silva",
        doc_type=DocumentType.CPF,
        doc_number="52998224725",
        segment=CustomerSegment.B2C,
        email="maria@exemplo.com",
        phone="11999998888"
    )


@pytest.fixture
def sample_customer_b2b() -> Customer:
    return Customer(
        id="cust_b2b_1",
        name="Empresa XPTO Ltda",
        doc_type=DocumentType.CNPJ,
        doc_number="11222333000181",
        segment=CustomerSegment.B2B,
        email="contato@xpto.com.br",
        phone="1133334444"
    )


@pytest.mark.unit
def test_refund_eligibility_delivered_within_7_days(sample_customer_b2c: Customer) -> None:
    service = RefundService()
    now = datetime.now(timezone.utc)
    order = Order(
        id="ord_1",
        customer_id=sample_customer_b2c.id,
        items=[OrderItem(sku="SKU-1", name="Teclado", quantity=1, unit_price_cents=15000)],
        total_cents=15000,
        status=OrderStatus.DELIVERED,
        delivery_date=now - timedelta(days=3)
    )

    eligible, reason = service.check_eligibility(order, now)
    assert eligible is True
    assert "elegível" in reason.lower()


@pytest.mark.unit
def test_refund_eligibility_delivered_past_7_days(sample_customer_b2c: Customer) -> None:
    service = RefundService()
    now = datetime.now(timezone.utc)
    order = Order(
        id="ord_2",
        customer_id=sample_customer_b2c.id,
        items=[OrderItem(sku="SKU-2", name="Monitor", quantity=1, unit_price_cents=120000)],
        total_cents=120000,
        status=OrderStatus.DELIVERED,
        delivery_date=now - timedelta(days=8)
    )

    eligible, reason = service.check_eligibility(order, now)
    assert eligible is False
    assert "expirado" in reason.lower()


@pytest.mark.unit
def test_refund_eligibility_not_delivered(sample_customer_b2c: Customer) -> None:
    service = RefundService()
    now = datetime.now(timezone.utc)
    order = Order(
        id="ord_3",
        customer_id=sample_customer_b2c.id,
        items=[OrderItem(sku="SKU-3", name="Mouse", quantity=1, unit_price_cents=5000)],
        total_cents=5000,
        status=OrderStatus.SHIPPED,
        delivery_date=None
    )

    eligible, reason = service.check_eligibility(order, now)
    assert eligible is False
    assert "não foi entregue" in reason.lower()


@pytest.mark.unit
def test_create_refund_requires_confirmation(sample_customer_b2c: Customer) -> None:
    service = RefundService()
    now = datetime.now(timezone.utc)
    order = Order(
        id="ord_4",
        customer_id=sample_customer_b2c.id,
        items=[OrderItem(sku="SKU-4", name="Headset", quantity=1, unit_price_cents=30000)],
        total_cents=30000,
        status=OrderStatus.DELIVERED,
        delivery_date=now - timedelta(days=2)
    )

    with pytest.raises(ConfirmationRequiredError):
        service.create_refund(order, reason="Defeito de fábrica", confirmed=False, current_time=now)


@pytest.mark.unit
def test_create_refund_success_when_confirmed(sample_customer_b2c: Customer) -> None:
    service = RefundService()
    now = datetime.now(timezone.utc)
    order = Order(
        id="ord_5",
        customer_id=sample_customer_b2c.id,
        items=[OrderItem(sku="SKU-5", name="Cadeira", quantity=1, unit_price_cents=80000)],
        total_cents=80000,
        status=OrderStatus.DELIVERED,
        delivery_date=now - timedelta(days=2)
    )

    refund = service.create_refund(order, reason="Arrependimento", confirmed=True, current_time=now)
    assert refund.status == RefundStatus.APPROVED
    assert refund.eligible is True
    assert refund.amount_cents == 80000


@pytest.mark.unit
def test_ticket_service_b2b_sla_calculation(sample_customer_b2b: Customer) -> None:
    service = TicketService()
    contract_platinum = ContractSLA(
        id="con_1",
        customer_id=sample_customer_b2b.id,
        tier=ContractTier.PLATINUM,
        response_sla_minutes=60,
        resolution_sla_hours=4,
        account_manager="Carlos Gerente",
        active=True
    )

    sla_hours = service.calculate_sla(
        segment=CustomerSegment.B2B,
        priority=TicketPriority.CRITICAL,
        contract=contract_platinum
    )
    assert sla_hours == 2

    sla_hours_low = service.calculate_sla(
        segment=CustomerSegment.B2B,
        priority=TicketPriority.LOW,
        contract=contract_platinum
    )
    assert sla_hours_low == 12


@pytest.mark.unit
def test_ticket_service_b2c_sla_calculation() -> None:
    service = TicketService()
    sla_hours_critical = service.calculate_sla(
        segment=CustomerSegment.B2C,
        priority=TicketPriority.CRITICAL,
        contract=None
    )
    assert sla_hours_critical == 12

    sla_hours_low = service.calculate_sla(
        segment=CustomerSegment.B2C,
        priority=TicketPriority.LOW,
        contract=None
    )
    assert sla_hours_low == 72
