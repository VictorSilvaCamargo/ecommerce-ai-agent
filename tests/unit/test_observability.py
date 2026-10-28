from fastapi.testclient import TestClient

from atendente.api.main import app, observability_manager
from atendente.infra.config import settings
from atendente.infra.observability import (
    ObservabilityManager,
    TraceRecord,
    TraceSpan,
    mask_pii_dict,
    mask_pii_text,
)


def test_mask_pii_text_masks_cpf_cnpj_email_phone() -> None:
    raw = (
        "Cliente CPF 529.982.247-25, sem pontos 52998224725, "
        "CNPJ 11.222.333/0001-81, email joao.silva@empresa.com.br "
        "e telefone (11) 98765-4321."
    )
    masked = mask_pii_text(raw)
    assert "529.982.247-25" not in masked
    assert "52998224725" not in masked
    assert "11.222.333/0001-81" not in masked
    assert "joao.silva@empresa.com.br" not in masked
    assert "98765-4321" not in masked
    assert "***.***.***-**" in masked
    assert "**.***.***/****-**" in masked
    assert "***@***" in masked


def test_mask_pii_dict_recursively_masks_nested_structures() -> None:
    event_dict = {
        "event": "identificar_cliente_executed",
        "doc": "529.982.247-25",
        "nested": {
            "email": "maria@teste.com",
            "items": ["CNPJ 11222333000181"],
        },
    }
    sanitized = mask_pii_dict(None, "info", event_dict)
    assert sanitized["doc"] == "***.***.***-**"
    assert sanitized["nested"]["email"] == "***@***"
    assert "**.***.***/****-**" in sanitized["nested"]["items"][0]


def test_observability_manager_records_trace_and_renders_prometheus() -> None:
    mgr = ObservabilityManager()
    trace = TraceRecord(
        trace_id="trc-1001",
        thread_id="thr-001",
        entry_point="webhook",
        prompt_version="v3.0.0",
        prompt_hash="abc123def456",
        segment="B2C",
        intent="solicitar_reembolso",
        user_message="Quero estorno do pedido PED-1001",
        assistant_response="Confirma o estorno do pedido PED-1001?",
        latency_ms=42.5,
        prompt_tokens=320,
        completion_tokens=48,
        cost_usd=0.0012,
        retrieved_chunks=[{"chunk_id": "chk-01", "source": "politica_reembolso.md", "score": 0.91}],
        tool_calls=[{"tool_name": "consultar_pedido", "status": "success"}],
        spans=[
            TraceSpan(name="identify", duration_ms=5.1),
            TraceSpan(name="classify_intent", duration_ms=11.4),
            TraceSpan(name="decide_tool", duration_ms=16.0),
            TraceSpan(name="respond", duration_ms=10.0),
        ],
    )
    mgr.record_trace(trace)
    mgr.record_http_request(
        method="POST", path="/webhook/messages", status_code=202, duration_ms=12.3
    )
    mgr.record_tool_call(tool_name="consultar_pedido", success=True)
    mgr.record_handoff(segment="B2C", reason="frustration")
    mgr.record_feedback(trace_id="trc-1001", score=1, comment="Excelente atendimento!")

    stored = mgr.get_trace("trc-1001")
    assert stored is not None
    assert stored.feedback_score == 1
    assert stored.feedback_comment == "Excelente atendimento!"
    assert stored.total_tokens == 368

    metrics_text = mgr.render_prometheus_metrics()
    assert "atendente_http_requests_total" in metrics_text
    assert 'path="/webhook/messages"' in metrics_text
    assert "atendente_tool_calls_total" in metrics_text
    assert 'tool_name="consultar_pedido"' in metrics_text
    assert "atendente_tokens_total" in metrics_text
    assert "atendente_handoffs_total" in metrics_text
    assert "atendente_user_feedback_total" in metrics_text


def test_metrics_and_feedback_endpoints_in_fastapi() -> None:
    observability_manager.reset()
    observability_manager.record_trace(
        TraceRecord(
            trace_id="trc-api-01",
            thread_id="thr-api-01",
            entry_point="rest_api",
            prompt_version="v3.0.0",
            prompt_hash="hash999",
            segment="B2B",
            intent="consultar_fatura",
            user_message="Qual o status da fatura?",
            assistant_response="Sua fatura INV-2001 está aberta.",
            latency_ms=25.0,
            prompt_tokens=200,
            completion_tokens=30,
            cost_usd=0.0005,
        )
    )

    client = TestClient(app)

    # POST /feedback
    resp_fb = client.post(
        "/feedback",
        headers={"X-API-Key": settings.api_key},
        json={
            "trace_id": "trc-api-01",
            "score": -1,
            "comment": "Demorou para localizar o boleto",
        },
    )
    assert resp_fb.status_code == 200
    body = resp_fb.json()
    assert body["status"] == "recorded"
    assert body["trace_id"] == "trc-api-01"
    assert body["score"] == -1

    # GET /metrics
    resp_metrics = client.get("/metrics")
    assert resp_metrics.status_code == 200
    assert "atendente_user_feedback_total" in resp_metrics.text
    assert 'atendente_user_feedback_total{polarity="negative"} 1' in resp_metrics.text
