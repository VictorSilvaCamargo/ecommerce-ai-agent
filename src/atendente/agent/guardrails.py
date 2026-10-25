from __future__ import annotations

import re
from collections import defaultdict

from pydantic import BaseModel

from atendente.infra.observability import mask_pii_text

_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"ignore\s+(?:todas\s+as\s+|all\s+)?(?:previous\s+|anteriores\s+)?(?:instru[cç][oõ]es|instructions|regras|rules)",
        re.IGNORECASE,
    ),
    re.compile(r"ignore\s+todas\s+as\s+instru[cç][oõ]es", re.IGNORECASE),
    re.compile(r"\bsystem[_\s]+override\b", re.IGNORECASE),
    re.compile(r"\bmodo\s+dan\b|\bdo\s+anything\s+now\b|\bjailbreak\b", re.IGNORECASE),
    re.compile(
        r"(?:exiba|mostre|print|dump)\s+.*?(?:vari[aá]veis\s+de\s+ambiente|os\.environ|api_key|webhook_secret)",
        re.IGNORECASE,
    ),
    re.compile(r"</\s*contexto_seguro\s*>", re.IGNORECASE),
]

_CREDENTIAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(?:postgresql|postgres|mongodb|redis)(?:\+\w+)?://[^\s\"']+", re.IGNORECASE),
    re.compile(
        r"\b(?:api_key|x-api-key|webhook_secret|password|secret)\s*[:=]\s*[^\s,;\"']+",
        re.IGNORECASE,
    ),
    re.compile(r"\bBearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
]


class GuardrailCheckResult(BaseModel):
    """Resultado de verificação de guardrail de entrada ou limite de ação."""

    allowed: bool
    violation_code: str | None = None
    reason: str | None = None


class OutputSanitizationResult(BaseModel):
    """Resultado de sanitização de saída do agente."""

    sanitized_text: str
    modified: bool


class SecurityGuardrails:
    """Guardrails de entrada (anti-injection e rate limit por thread) e saída (vazamento de segredos e PII)."""

    def __init__(self, max_actions_per_thread: int = 5, max_input_chars: int = 4000) -> None:
        self.max_actions_per_thread = max_actions_per_thread
        self.max_input_chars = max_input_chars
        self._thread_action_counts: dict[str, int] = defaultdict(int)

    def validate_input(self, thread_id: str, text: str) -> GuardrailCheckResult:
        if len(text) > self.max_input_chars:
            return GuardrailCheckResult(
                allowed=False,
                violation_code="INPUT_TOO_LONG",
                reason=f"Mensagem excede o limite de {self.max_input_chars} caracteres.",
            )

        for pattern in _INJECTION_PATTERNS:
            if pattern.search(text):
                return GuardrailCheckResult(
                    allowed=False,
                    violation_code="PROMPT_INJECTION_DETECTED",
                    reason="Tentativa de manipulacao de instrucoes de sistema detectada e bloqueada.",
                )

        return GuardrailCheckResult(allowed=True)

    def check_and_record_action(self, thread_id: str, tool_name: str) -> GuardrailCheckResult:
        current = self._thread_action_counts[thread_id]
        if current >= self.max_actions_per_thread:
            return GuardrailCheckResult(
                allowed=False,
                violation_code="ACTION_RATE_LIMIT_EXCEEDED",
                reason=(
                    f"Limite maximo de {self.max_actions_per_thread} acoes atingido na thread {thread_id} "
                    f"ao tentar executar {tool_name}."
                ),
            )
        self._thread_action_counts[thread_id] = current + 1
        return GuardrailCheckResult(allowed=True)

    def sanitize_output(self, text: str) -> OutputSanitizationResult:
        sanitized = text
        for pattern in _CREDENTIAL_PATTERNS:
            sanitized = pattern.sub("[CREDENTIAL_REDACTED]", sanitized)
        sanitized = mask_pii_text(sanitized)
        return OutputSanitizationResult(
            sanitized_text=sanitized,
            modified=(sanitized != text),
        )
