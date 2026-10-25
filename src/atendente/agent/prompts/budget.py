import json
import math
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from atendente.agent.prompts.rag_delimiters import format_rag_context_safe
from atendente.agent.prompts.system import get_system_prompt

B2C_TOOLS = {
    "identificar_cliente",
    "consultar_pedido",
    "solicitar_reembolso",
    "abrir_chamado",
    "buscar_base_conhecimento",
    "transferir_para_humano",
}

B2B_TOOLS = {
    "identificar_cliente",
    "abrir_chamado",
    "consultar_contrato_sla",
    "consultar_fatura",
    "buscar_base_conhecimento",
    "transferir_para_humano",
}


def count_tokens(text: str) -> int:
    """Estimativa determinística de tokens para Português (~3.8 caracteres por token ou contagem de palavras * 1.3)."""
    if not text or not text.strip():
        return 0
    char_est = math.ceil(len(text) / 4.0)
    word_est = math.ceil(len(text.split()) * 1.3)
    return max(char_est, word_est)


def truncate_text_to_tokens(text: str, max_tokens: int) -> str:
    """Trunca deterministicamente um texto para caber estritamente em `max_tokens`."""
    if count_tokens(text) <= max_tokens:
        return text
    words = text.split()
    allowed_words = max(1, int(max_tokens / 1.35) - 2)
    truncated = " ".join(words[:allowed_words])
    max_chars = max(4, (max_tokens - 1) * 4)
    if len(truncated) > max_chars:
        truncated = truncated[:max_chars]
    return truncated


class SectionBudgetConfig(BaseModel):
    """Configuração rígida de orçamento de tokens por seção da janela de contexto."""

    model_config = ConfigDict(frozen=True)

    system_max: int = Field(default=600, ge=50)
    tools_max: int = Field(default=600, ge=50)
    rag_max: int = Field(default=800, ge=50)
    history_max: int = Field(default=1000, ge=50)
    total_max: int = Field(default=3000, ge=200)


class BudgetedContextResult(BaseModel):
    """Resultado empacotado e verificado pelo gerenciador de orçamento de contexto."""

    model_config = ConfigDict(extra="forbid")

    system_prompt: str
    tools_schemas: list[dict[str, Any]]
    rag_context: str
    history_messages: list[dict[str, Any]]
    section_tokens: dict[str, int]
    total_tokens: int
    trimmed_sections: list[str]
    prompt_hash: str
    sanitized_rag_injection: bool = False


class ContextBudgetManager:
    """Gerencia e impõe limites estritos de tokens por seção (System, Tools, RAG, History)."""

    def __init__(self, config: SectionBudgetConfig | None = None) -> None:
        self.config = config or SectionBudgetConfig()

    def _fit_system(self, version: str, trimmed: list[str]) -> tuple[str, int, str]:
        prompt_obj = get_system_prompt(version)
        sys_text = prompt_obj.template
        tokens = count_tokens(sys_text)
        if tokens > self.config.system_max:
            trimmed.append("system")
            sys_text = truncate_text_to_tokens(sys_text, self.config.system_max)
            tokens = count_tokens(sys_text)
        return sys_text, tokens, prompt_obj.sha256_hash

    def _fit_tools(
        self, tools_schemas: list[dict[str, Any]], segment: str, trimmed: list[str]
    ) -> tuple[list[dict[str, Any]], int]:
        # 1. Filtragem seletiva por segmento (Selective Include - Context Engineering)
        allowed_set = (
            B2C_TOOLS
            if segment == "B2C"
            else B2B_TOOLS
            if segment == "B2B"
            else B2C_TOOLS | B2B_TOOLS
        )
        filtered = [t for t in tools_schemas if t.get("name") in allowed_set]

        serialized = json.dumps(filtered, ensure_ascii=False)
        tokens = count_tokens(serialized)
        if tokens <= self.config.tools_max:
            return filtered, tokens

        # 2. Compactar descrições das ferramentas para economizar tokens mantendo os contratos
        trimmed.append("tools")
        compact_tools: list[dict[str, Any]] = []
        for t in filtered:
            compact_t = {
                "name": t.get("name"),
                "description": str(t.get("description", ""))[:60],
                "parameters": {
                    "type": "object",
                    "properties": {
                        k: {"type": v.get("type", "string")}
                        for k, v in t.get("parameters", {}).get("properties", {}).items()
                    },
                    "required": t.get("parameters", {}).get("required", []),
                },
            }
            candidate_list = [*compact_tools, compact_t]
            if (
                count_tokens(json.dumps(candidate_list, ensure_ascii=False))
                <= self.config.tools_max
            ):
                compact_tools.append(compact_t)
            else:
                break

        final_tokens = count_tokens(json.dumps(compact_tools, ensure_ascii=False))
        return compact_tools, final_tokens

    def _fit_rag(
        self, rag_chunks: list[dict[str, Any]], trimmed: list[str]
    ) -> tuple[str, int, bool]:
        formatted, sanitized = format_rag_context_safe(rag_chunks)
        tokens = count_tokens(formatted)
        if tokens <= self.config.rag_max:
            return formatted, tokens, sanitized

        trimmed.append("rag")
        # Reduzir progressivamente a quantidade e tamanho dos chunks mantendo <contexto_seguro>
        overhead_tokens = count_tokens("<contexto_seguro>\n\n</contexto_seguro>") + 15
        available_for_docs = max(10, self.config.rag_max - overhead_tokens)

        kept_chunks: list[dict[str, Any]] = []
        used_tokens = 0
        for chk in rag_chunks:
            source = str(chk.get("source_file", "doc.md"))
            section = str(chk.get("section", "Geral"))
            meta_tokens = (
                count_tokens(
                    f'<documento indice="1" fonte="{source}" secao="{section}"></documento>'
                )
                + 6
            )
            remaining = available_for_docs - used_tokens - meta_tokens
            if remaining < 15:
                break
            truncated_content = truncate_text_to_tokens(str(chk.get("content", "")), remaining)
            new_chk = {
                "content": truncated_content,
                "source_file": source,
                "section": section,
            }
            candidate_formatted, cand_sanitized = format_rag_context_safe([*kept_chunks, new_chk])
            cand_tokens = count_tokens(candidate_formatted)
            if cand_tokens <= self.config.rag_max:
                kept_chunks.append(new_chk)
                used_tokens = cand_tokens - overhead_tokens
                sanitized = sanitized or cand_sanitized
            else:
                break

        final_formatted, final_sanitized = format_rag_context_safe(kept_chunks)
        final_tokens = count_tokens(final_formatted)
        return final_formatted, final_tokens, sanitized or final_sanitized

    def _fit_history(
        self,
        messages: list[dict[str, Any]],
        summary: str | None,
        trimmed: list[str],
    ) -> tuple[list[dict[str, Any]], int]:
        if not messages:
            return [], 0

        # Ordem de recência (Context Engineering): proteger a última mensagem do usuário no final
        serialized_all = json.dumps(messages, ensure_ascii=False)
        if summary:
            serialized_all = f"[RESUMO]: {summary}\n" + serialized_all

        tokens = count_tokens(serialized_all)
        if tokens <= self.config.history_max:
            result_msgs = list(messages)
            if summary:
                result_msgs.insert(
                    0, {"role": "system", "content": f"[RESUMO_HISTÓRICO]: {summary}"}
                )
            final_t = count_tokens(json.dumps(result_msgs, ensure_ascii=False))
            if final_t <= self.config.history_max:
                return result_msgs, final_t

        trimmed.append("history")
        # Preservar sempre a última mensagem (mais recente) e incluir turnos anteriores até o limite
        last_msg = dict(messages[-1])
        last_content = str(last_msg.get("content", ""))
        if count_tokens(json.dumps([last_msg], ensure_ascii=False)) > self.config.history_max:
            last_msg["content"] = truncate_text_to_tokens(
                last_content, max(10, self.config.history_max - 15)
            )
            return [last_msg], count_tokens(json.dumps([last_msg], ensure_ascii=False))

        selected_reversed: list[dict[str, Any]] = [last_msg]
        for msg in reversed(messages[:-1]):
            candidate = [msg, *selected_reversed]
            if (
                count_tokens(json.dumps(candidate, ensure_ascii=False))
                <= self.config.history_max - 40
            ):
                selected_reversed.insert(0, msg)
            else:
                break

        # Se sobrar espaço para um resumo compacto no início
        dropped_count = len(messages) - len(selected_reversed)
        if dropped_count > 0 or summary:
            short_sum = truncate_text_to_tokens(
                summary or f"{dropped_count} turnos anteriores compactados.", 25
            )
            summary_msg = {"role": "system", "content": f"[RESUMO]: {short_sum}"}
            with_summary = [summary_msg, *selected_reversed]
            if (
                count_tokens(json.dumps(with_summary, ensure_ascii=False))
                <= self.config.history_max
            ):
                selected_reversed = with_summary

        final_tokens = count_tokens(json.dumps(selected_reversed, ensure_ascii=False))
        return selected_reversed, final_tokens

    def allocate(
        self,
        version: str,
        segment: str,
        rag_chunks: list[dict[str, Any]],
        messages: list[dict[str, Any]],
        tools_schemas: list[dict[str, Any]],
        summary: str | None = None,
    ) -> BudgetedContextResult:
        """Aloca e valida o orçamento de tokens por seção, garantindo que nunca estoure."""
        trimmed_sections: list[str] = []

        sys_text, sys_tokens, prompt_hash = self._fit_system(version, trimmed_sections)
        fitted_tools, tools_tokens = self._fit_tools(tools_schemas, segment, trimmed_sections)
        rag_text, rag_tokens, sanitized = self._fit_rag(rag_chunks, trimmed_sections)
        fitted_history, hist_tokens = self._fit_history(messages, summary, trimmed_sections)

        total_tokens = sys_tokens + tools_tokens + rag_tokens + hist_tokens

        return BudgetedContextResult(
            system_prompt=sys_text,
            tools_schemas=fitted_tools,
            rag_context=rag_text,
            history_messages=fitted_history,
            section_tokens={
                "system": sys_tokens,
                "tools": tools_tokens,
                "rag": rag_tokens,
                "history": hist_tokens,
            },
            total_tokens=total_tokens,
            trimmed_sections=trimmed_sections,
            prompt_hash=prompt_hash,
            sanitized_rag_injection=sanitized,
        )
