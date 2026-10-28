from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import MutableMapping
from datetime import UTC, datetime
from typing import Any, Literal

import structlog
from pydantic import BaseModel, Field

# Regex de mascaramento de PII (CPF, CNPJ, Email, Telefone BR)
_CNPJ_FORMATTED_RE = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")
_CNPJ_RAW_RE = re.compile(r"\b\d{14}\b")
_CPF_FORMATTED_RE = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
_CPF_RAW_RE = re.compile(r"\b\d{11}\b")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"(?:\(\d{2}\)\s*|\b\d{2}\s+)9?\d{4}[-\s]?\d{4}\b")


def mask_pii_text(text: str) -> str:
    """Mascara CPF, CNPJ, e-mails e telefones brasileiros em qualquer string."""
    result = _CNPJ_FORMATTED_RE.sub("**.***.***/****-**", text)
    result = _CNPJ_RAW_RE.sub("**.***.***/****-**", result)
    result = _CPF_FORMATTED_RE.sub("***.***.***-**", result)
    result = _CPF_RAW_RE.sub("***.***.***-**", result)
    result = _EMAIL_RE.sub("***@***", result)
    result = _PHONE_RE.sub("(**) *****-****", result)
    return result


def _sanitize_value(val: Any) -> Any:
    if isinstance(val, str):
        return mask_pii_text(val)
    if isinstance(val, dict):
        return {k: _sanitize_value(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_sanitize_value(item) for item in val]
    return val


def mask_pii_dict(
    logger: Any, method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """Processador structlog que mascara recursivamente PII nos eventos de log."""
    return {k: _sanitize_value(v) for k, v in event_dict.items()}


def configure_structured_logging() -> None:
    """Configura structlog com mascaramento automático de PII e saída JSON."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.add_log_level,
            mask_pii_dict,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.BoundLogger,
        cache_logger_on_first_use=True,
    )


class TraceSpan(BaseModel):
    """Span individual de um nó do LangGraph ou chamada de Tool."""

    name: str = Field(..., min_length=1)
    duration_ms: float = Field(..., ge=0.0)
    status: Literal["ok", "error"] = "ok"
    metadata: dict[str, Any] = Field(default_factory=dict)


class TraceRecord(BaseModel):
    """Registro completo de trace compatível com exportação Langfuse e conversão para eval."""

    trace_id: str = Field(..., min_length=1)
    thread_id: str = Field(..., min_length=1)
    entry_point: str = Field(default="rest_api")
    prompt_version: str = Field(default="v3.0.0")
    prompt_hash: str = Field(default="")
    segment: str | None = None
    intent: str | None = None
    user_message: str = ""
    assistant_response: str = ""
    latency_ms: float = Field(default=0.0, ge=0.0)
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0.0, ge=0.0)
    retrieved_chunks: list[dict[str, Any]] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    spans: list[TraceSpan] = Field(default_factory=list)
    requires_confirmation: bool = False
    handoff_triggered: bool = False
    abstained: bool = False
    feedback_score: Literal[-1, 1] | None = None
    feedback_comment: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class FeedbackInput(BaseModel):
    """Payload de feedback de usuário (thumbs up / thumbs down) vinculado a um trace_id."""

    trace_id: str = Field(..., min_length=1)
    score: Literal[-1, 1] = Field(..., description="1 para positivo (thumbs up), -1 para negativo")
    comment: str | None = Field(default=None, max_length=1000)


class ObservabilityManager:
    """Gerenciador central de traces (Langfuse-compatible) e métricas RED/Negócio (Prometheus)."""

    def __init__(self) -> None:
        self._traces: dict[str, TraceRecord] = {}
        self._http_requests: dict[tuple[str, str, int], int] = defaultdict(int)
        self._http_errors: dict[tuple[str, str], int] = defaultdict(int)
        self._http_duration_sum_ms: dict[tuple[str, str], float] = defaultdict(float)
        self._tool_calls: dict[tuple[str, str], int] = defaultdict(int)
        self._tokens_total: dict[str, int] = defaultdict(int)
        self._handoffs_total: dict[tuple[str, str], int] = defaultdict(int)
        self._feedback_total: dict[str, int] = defaultdict(int)

    def reset(self) -> None:
        self._traces.clear()
        self._http_requests.clear()
        self._http_errors.clear()
        self._http_duration_sum_ms.clear()
        self._tool_calls.clear()
        self._tokens_total.clear()
        self._handoffs_total.clear()
        self._feedback_total.clear()

    def record_trace(self, trace: TraceRecord) -> None:
        self._traces[trace.trace_id] = trace
        self._tokens_total["prompt"] += trace.prompt_tokens
        self._tokens_total["completion"] += trace.completion_tokens
        for tc in trace.tool_calls:
            t_name = str(tc.get("tool_name", "unknown"))
            t_status = str(tc.get("status", "success"))
            self._tool_calls[(t_name, t_status)] += 1

    def get_trace(self, trace_id: str) -> TraceRecord | None:
        return self._traces.get(trace_id)

    def list_traces(self) -> list[TraceRecord]:
        return list(self._traces.values())

    def record_http_request(
        self, method: str, path: str, status_code: int, duration_ms: float
    ) -> None:
        self._http_requests[(method, path, status_code)] += 1
        self._http_duration_sum_ms[(method, path)] += duration_ms
        if status_code >= 400:
            self._http_errors[(method, path)] += 1

    def record_tool_call(self, tool_name: str, success: bool) -> None:
        status_str = "success" if success else "error"
        self._tool_calls[(tool_name, status_str)] += 1

    def record_handoff(self, segment: str, reason: str) -> None:
        self._handoffs_total[(segment, reason)] += 1

    def record_feedback(
        self, trace_id: str, score: Literal[-1, 1], comment: str | None = None
    ) -> bool:
        polarity = "positive" if score == 1 else "negative"
        self._feedback_total[polarity] += 1
        trace = self._traces.get(trace_id)
        if trace is not None:
            trace.feedback_score = score
            trace.feedback_comment = comment
            return True
        return False

    def render_prometheus_metrics(self) -> str:
        """Renderiza todas as métricas acumuladas no formato de texto Prometheus 0.0.4."""
        lines: list[str] = [
            "# HELP atendente_http_requests_total Total de requisicoes HTTP recebidas",
            "# TYPE atendente_http_requests_total counter",
        ]
        for (method, path, status_code), count in sorted(self._http_requests.items()):
            lines.append(
                f'atendente_http_requests_total{{method="{method}",path="{path}",status="{status_code}"}} {count}'
            )

        lines.extend(
            [
                "# HELP atendente_http_errors_total Total de requisicoes HTTP com erro (>=400)",
                "# TYPE atendente_http_errors_total counter",
            ]
        )
        for (method, path), count in sorted(self._http_errors.items()):
            lines.append(f'atendente_http_errors_total{{method="{method}",path="{path}"}} {count}')

        lines.extend(
            [
                "# HELP atendente_http_request_duration_ms_sum Soma da latencia HTTP em ms",
                "# TYPE atendente_http_request_duration_ms_sum counter",
            ]
        )
        for (method, path), total_ms in sorted(self._http_duration_sum_ms.items()):
            lines.append(
                f'atendente_http_request_duration_ms_sum{{method="{method}",path="{path}"}} {total_ms:.2f}'
            )

        lines.extend(
            [
                "# HELP atendente_tool_calls_total Total de execucoes de Tools por nome e status",
                "# TYPE atendente_tool_calls_total counter",
            ]
        )
        for (tool_name, status_str), count in sorted(self._tool_calls.items()):
            lines.append(
                f'atendente_tool_calls_total{{tool_name="{tool_name}",status="{status_str}"}} {count}'
            )

        lines.extend(
            [
                "# HELP atendente_tokens_total Total de tokens consumidos por tipo",
                "# TYPE atendente_tokens_total counter",
            ]
        )
        for token_type, count in sorted(self._tokens_total.items()):
            lines.append(f'atendente_tokens_total{{type="{token_type}"}} {count}')

        lines.extend(
            [
                "# HELP atendente_handoffs_total Total de escalacoes humanas por segmento e motivo",
                "# TYPE atendente_handoffs_total counter",
            ]
        )
        for (segment, reason), count in sorted(self._handoffs_total.items()):
            lines.append(
                f'atendente_handoffs_total{{segment="{segment}",reason="{reason}"}} {count}'
            )

        lines.extend(
            [
                "# HELP atendente_user_feedback_total Total de feedbacks de usuario por polaridade",
                "# TYPE atendente_user_feedback_total counter",
            ]
        )
        for polarity in ("positive", "negative"):
            count = self._feedback_total.get(polarity, 0)
            lines.append(f'atendente_user_feedback_total{{polarity="{polarity}"}} {count}')

        return "\n".join(lines) + "\n"
