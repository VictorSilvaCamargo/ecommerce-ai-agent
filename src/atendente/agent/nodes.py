import re
from typing import Any

from atendente.agent.state import ConversationState
from atendente.domain.validators import validate_cnpj, validate_cpf
from atendente.infra.llm.client import LLMClient
from atendente.rag.retriever import HybridRetriever
from atendente.tools.base import ToolResult
from atendente.tools.service import (
    AbrirChamadoInput,
    ConsultarContratoSLAInput,
    ConsultarFaturaInput,
    ConsultarPedidoInput,
    IdentificarClienteInput,
    NovaLojaToolsService,
    SolicitarReembolsoInput,
    TransferirParaHumanoInput,
)

SENSITIVE_TOOLS = {"solicitar_reembolso"}


class AgentNodeHandler:
    """Implementação dos nós de decisão e orquestração do Grafo LangGraph."""

    def __init__(
        self,
        tools_service: NovaLojaToolsService,
        retriever: HybridRetriever | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.tools_service = tools_service
        self.retriever = retriever
        self.llm_client = llm_client

    def _get_last_user_message(self, state: ConversationState) -> str:
        for msg in reversed(state.messages):
            if msg.get("role") == "user":
                return str(msg.get("content", ""))
        return ""

    async def identify(self, state: ConversationState) -> dict[str, Any]:
        """Identifica e autentica o cliente a partir do CPF/CNPJ."""
        if state.authenticated and state.customer_id:
            return {}

        text = self._get_last_user_message(state)
        # Buscar sequências de dígitos (CPF = 11, CNPJ = 14)
        digits_seq = re.findall(r"\d+", text)
        full_digits = "".join(digits_seq)

        target_doc = None
        for candidate in digits_seq:
            if len(candidate) == 11 and validate_cpf(candidate):
                target_doc = candidate
                segment = "B2C"
                break
            elif len(candidate) == 14 and validate_cnpj(candidate):
                target_doc = candidate
                segment = "B2B"
                break

        if not target_doc and (len(full_digits) == 11 and validate_cpf(full_digits)):
            target_doc = full_digits
            segment = "B2C"
        elif not target_doc and (len(full_digits) == 14 and validate_cnpj(full_digits)):
            target_doc = full_digits
            segment = "B2B"

        if target_doc:
            ident_res = await self.tools_service.identificar_cliente(
                IdentificarClienteInput(doc_number=target_doc, verification_code="123456")
            )
            if ident_res.success and ident_res.data:
                customer = ident_res.data
                return {
                    "customer_id": customer.id,
                    "customer_document": customer.doc_number,
                    "customer_segment": customer.segment.value,
                    "authenticated": True,
                }
            return {
                "customer_document": target_doc,
                "customer_segment": segment,
                "authenticated": True,
                "customer_id": f"cust-{target_doc[:6]}",
            }

        return {}

    async def classify_intent(self, state: ConversationState) -> dict[str, Any]:
        """Classifica a intenção do cliente e detecta sinais de frustração."""
        text = self._get_last_user_message(state).lower()

        # Detecção de frustração
        frustration_terms = [
            "absurdo",
            "péssimo",
            "pessimo",
            "incompetência",
            "incompetencia",
            "horrível",
            "horrivel",
            "palhaçada",
            "palhacada",
            "esperando há dias",
            "processo",
            "procon",
        ]
        frustration_detected = any(term in text for term in frustration_terms)

        # Se houver ação pendente aguardando confirmação
        if state.pending_action:
            if any(w in text for w in ["sim", "confirmo", "pode prosseguir", "autorizo", "ok"]):
                return {
                    "active_intent": "confirmar_acao",
                    "frustration_detected": frustration_detected,
                }
            if any(w in text for w in ["não", "nao", "cancela", "não quero", "desisto"]):
                return {
                    "active_intent": "cancelar_acao",
                    "frustration_detected": frustration_detected,
                }

        # Pedido explícito de atendimento humano
        if any(w in text for w in ["atendente", "humano", "pessoa", "falar com alguém"]):
            return {
                "active_intent": "falar_com_atendente",
                "frustration_detected": frustration_detected,
            }

        # Intenções de negócio
        if any(w in text for w in ["reembolso", "estorno", "devolução do dinheiro", "devolver"]):
            intent = "solicitar_reembolso"
        elif any(w in text for w in ["pedido", "rastreio", "entrega", "ped-"]):
            intent = "consultar_pedido"
        elif any(w in text for w in ["fatura", "boleto", "segunda via", "fat-"]):
            intent = "consultar_fatura"
        elif any(w in text for w in ["contrato", "sla", "ctr-"]):
            intent = "consultar_contrato_sla"
        elif any(w in text for w in ["chamado", "ticket", "problema técnico", "defeito"]):
            intent = "abrir_chamado"
        elif any(
            w in text for w in ["política", "politica", "prazo", "como funciona", "cdc", "troca"]
        ):
            intent = "duvida_geral"
        else:
            intent = "duvida_geral"

        return {
            "active_intent": intent,
            "frustration_detected": frustration_detected,
        }

    async def retrieve_context(self, state: ConversationState) -> dict[str, Any]:
        """Recupera trechos da base de conhecimento RAG para dúvidas gerais."""
        if not self.retriever:
            return {"retrieved_docs": []}

        query = self._get_last_user_message(state)
        segment = state.customer_segment if state.customer_segment != "INDEFINIDO" else None
        chunks = await self.retriever.retrieve(query=query, segment=segment, limit=3)

        return {"retrieved_docs": [c.model_dump() for c in chunks]}

    async def decide_tool(self, state: ConversationState) -> dict[str, Any]:
        """Mapeia a intenção e parâmetros em uma ação de ferramenta pendente."""
        text = self._get_last_user_message(state)
        intent = state.active_intent

        if intent in ("confirmar_acao", "cancelar_acao") and state.pending_action:
            return {"pending_action": state.pending_action}

        pending_action: dict[str, Any] | None = None
        customer_id = state.customer_id or "cust-simulado"

        if intent == "consultar_pedido":
            order_match = re.search(r"(?:ord|ped)[-_]\w+", text, re.IGNORECASE)
            order_id = order_match.group(0).lower() if order_match else "ord_b2c_recent"
            pending_action = {
                "tool_name": "consultar_pedido",
                "parameters": {"order_id": order_id, "customer_id": customer_id},
            }
        elif intent == "solicitar_reembolso":
            order_match = re.search(r"(?:ord|ped)[-_]\w+", text, re.IGNORECASE)
            order_id = order_match.group(0).lower() if order_match else "ord_b2c_recent"
            pending_action = {
                "tool_name": "solicitar_reembolso",
                "parameters": {
                    "order_id": order_id,
                    "customer_id": customer_id,
                    "reason": text,
                },
            }
        elif intent == "consultar_fatura":
            pending_action = {
                "tool_name": "consultar_fatura",
                "parameters": {"customer_id": customer_id},
            }
        elif intent == "consultar_contrato_sla":
            contract_match = re.search(r"ctr-\w+", text, re.IGNORECASE)
            contract_id = contract_match.group(0).upper() if contract_match else "CTR-GOLD-01"
            pending_action = {
                "tool_name": "consultar_contrato_sla",
                "parameters": {"contract_id": contract_id, "customer_id": customer_id},
            }
        elif intent == "abrir_chamado":
            priority = (
                "P1"
                if any(
                    w in text.lower() for w in ["crítico", "critico", "parou tudo", "emergência"]
                )
                else "P3"
            )
            pending_action = {
                "tool_name": "abrir_chamado",
                "parameters": {
                    "customer_id": customer_id,
                    "title": "Solicitação de Suporte via Atendente IA",
                    "description": text,
                    "priority": priority,
                },
            }

        return {"pending_action": pending_action, "action_confirmed": False}

    async def confirm_action(self, state: ConversationState) -> dict[str, Any]:
        """Gatekeeper de ações sensíveis: bloqueia a execução se não confirmada."""
        pending = state.pending_action
        if not pending:
            return {}

        tool_name = str(pending.get("tool_name", ""))
        params: dict[str, Any] = pending.get("parameters", {})
        is_sensitive = tool_name in SENSITIVE_TOOLS or (
            tool_name == "abrir_chamado" and params.get("priority") == "P1"
        )

        if is_sensitive:
            if state.active_intent == "confirmar_acao":
                confirmed = True
            elif state.active_intent == "cancelar_acao":
                return {
                    "pending_action": None,
                    "action_confirmed": False,
                    "last_response": "Solicitação cancelada com sucesso a seu pedido.",
                    "last_tool_result": None,
                }
            else:
                # Bloqueia e solicita confirmação explícita
                order_ref = params.get("order_id", "informado")
                msg = (
                    f"⚠️ Confirmação Necessária: Identifiquei uma solicitação de {tool_name.replace('_', ' ')} "
                    f"para a referência '{order_ref}'. Para sua segurança, confirme digitando 'SIM' para autorizar "
                    f"ou 'NÃO' para cancelar."
                )
                return {
                    "pending_action": pending,
                    "action_confirmed": False,
                    "last_response": msg,
                    "last_tool_result": None,
                }
        else:
            confirmed = False

        # Execução da ferramenta via NovaLojaToolsService
        result_data = None
        consecutive_failures = state.consecutive_unresolved_turns
        res: ToolResult[Any]

        if tool_name == "consultar_pedido":
            res = await self.tools_service.consultar_pedido(
                ConsultarPedidoInput(order_id=params["order_id"], customer_id=params["customer_id"])
            )
            result_data = res.model_dump()
            consecutive_failures = 0 if res.success else consecutive_failures + 1
        elif tool_name == "solicitar_reembolso":
            res = await self.tools_service.solicitar_reembolso(
                SolicitarReembolsoInput(
                    order_id=params["order_id"],
                    customer_id=params["customer_id"],
                    motivo=params.get("reason", "Solicitação do cliente"),
                    confirmado=True,
                )
            )
            result_data = res.model_dump()
            consecutive_failures = 0 if res.success else consecutive_failures + 1
        elif tool_name == "consultar_fatura":
            res = await self.tools_service.consultar_fatura(
                ConsultarFaturaInput(customer_id=params["customer_id"])
            )
            result_data = res.model_dump()
            consecutive_failures = 0 if res.success else consecutive_failures + 1
        elif tool_name == "consultar_contrato_sla":
            res = await self.tools_service.consultar_contrato_sla(
                ConsultarContratoSLAInput(customer_id=params["customer_id"])
            )
            result_data = res.model_dump()
            consecutive_failures = 0 if res.success else consecutive_failures + 1
        elif tool_name == "abrir_chamado":
            res = await self.tools_service.abrir_chamado(
                AbrirChamadoInput(
                    customer_id=params["customer_id"],
                    titulo=params.get("title", "Chamado Suporte"),
                    descricao=params.get("description", "Descrição do chamado"),
                    prioridade=params.get("priority", "MEDIUM"),
                )
            )
            result_data = res.model_dump()
            consecutive_failures = 0 if res.success else consecutive_failures + 1

        return {
            "pending_action": None,
            "action_confirmed": confirmed,
            "last_tool_result": result_data,
            "consecutive_unresolved_turns": consecutive_failures,
        }

    async def respond(self, state: ConversationState) -> dict[str, Any]:
        """Gera a mensagem resolutiva para o cliente em português."""
        if state.last_response and not state.last_tool_result:
            response_text = state.last_response
        elif state.last_tool_result:
            res = state.last_tool_result
            if res.get("success"):
                data = res.get("data")
                if isinstance(data, dict):
                    if "tracking_code" in data or "total_cents" in data:
                        response_text = (
                            f"Encontrei seu pedido! Status atual: {data.get('status', 'Em processamento')}. "
                            f"Código de rastreio: {data.get('tracking_code', 'N/A')}."
                        )
                    elif "uptime_target" in data or "tier" in data:
                        response_text = (
                            f"Dados do seu contrato {data.get('id', '')}: Plano {data.get('tier', '')}, "
                            f"Uptime garantido de {data.get('uptime_target', 99.5)}%."
                        )
                    elif "amount_cents" in data or ("reason" in data and "order_id" in data):
                        response_text = (
                            f"Solicitação de reembolso processada com sucesso! "
                            f"Protocolo registrado com status: {data.get('status', 'PENDING')}."
                        )
                    elif "titulo" in data or "prioridade" in data:
                        response_text = (
                            f"Chamado aberto com sucesso! Número do ticket: {data.get('id', 'N/A')}. "
                            f"Prioridade: {data.get('prioridade', 'MEDIUM')}."
                        )
                    else:
                        response_text = "Operação realizada com sucesso na NovaLoja."
                elif isinstance(data, list):
                    response_text = (
                        f"Foram localizados {len(data)} registros para sua solicitação na NovaLoja."
                    )
                else:
                    response_text = "Operação realizada com sucesso na NovaLoja."
            else:
                err = res.get("error", {})
                response_text = (
                    f"Não foi possível concluir a ação: {err.get('message', 'Erro desconhecido')}."
                )
        elif state.retrieved_docs:
            top_doc = state.retrieved_docs[0]
            content = top_doc.get("content", "")
            source = top_doc.get("source_file", "Base NovaLoja")
            response_text = (
                f"De acordo com nossas políticas oficiais ({source}): {content[:300]}..."
            )
        else:
            response_text = (
                "Olá! Sou o Atendente Virtual da NovaLoja. Como posso ajudar você hoje com seus pedidos, "
                "faturas, contratos ou dúvidas?"
            )

        updated_messages = list(state.messages)
        updated_messages.append({"role": "assistant", "content": response_text})
        return {"messages": updated_messages, "last_response": response_text}

    async def evaluate_handoff(self, state: ConversationState) -> dict[str, Any]:
        """Avalia condições de transbordo e transfere para atendente humano."""
        reason = None
        if state.active_intent == "falar_com_atendente":
            reason = "Solicitação explícita do cliente por atendimento humano."
        elif state.consecutive_unresolved_turns >= 3:
            reason = "Limite de 3 tentativas consecutivas sem resolução atingido."
        elif state.frustration_detected:
            reason = "Sinais de frustração detectados no atendimento automatizado."

        if reason:
            customer_id = state.customer_id or "cust-simulado"
            summary = state.summary or f"Conversa com {len(state.messages)} mensagens."
            await self.tools_service.transferir_para_humano(
                TransferirParaHumanoInput(
                    customer_id=customer_id,
                    motivo=reason,
                    resumo_conversa=summary,
                )
            )
            msg = (
                f"Estou transferindo seu atendimento para nossa equipe de especialistas humanos. "
                f"Motivo do transbordo: {reason}. Um momento, por favor!"
            )
            updated_messages = list(state.messages)
            updated_messages.append({"role": "assistant", "content": msg})
            return {
                "handoff_requested": True,
                "handoff_reason": reason,
                "messages": updated_messages,
                "last_response": msg,
            }

        return {}

    async def summarize_history(self, state: ConversationState) -> dict[str, Any]:
        """Sumariza mensagens antigas preservando contexto essencial para caber no token budget."""
        if len(state.messages) <= 8:
            return {}

        older_messages = state.messages[:-4]
        recent_messages = state.messages[-4:]

        summary_lines = []
        for m in older_messages:
            content_str = str(m.get("content") or "")[:80]
            summary_lines.append(f"{m.get('role')}: {content_str}")

        new_summary_chunk = " | ".join(summary_lines)
        existing_summary = state.summary or ""
        total_summary = f"{existing_summary} [Sumarizado]: {new_summary_chunk}".strip()

        return {"messages": recent_messages, "summary": total_summary}
