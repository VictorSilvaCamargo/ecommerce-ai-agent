# Playbook de Depuração em Produção e Ciclo Trace-to-Test — Atendente IA

Este documento estabelece o protocolo operacional de investigação de falhas do **Atendente IA da NovaLoja**, alinhado às práticas da skill `debugging-and-error-recovery` (Reproduzir → Localizar → Reduzir → Corrigir → Blindar) e integrado ao pipeline de observabilidade (Langfuse + Prometheus + `make trace-to-test`).

---

## 1. Fluxo de Diagnóstico em 5 Passos

Quando um alerta dispara no Grafana/Prometheus ou um cliente envia feedback negativo (`POST /feedback` com `score: -1`), o engenheiro de plantão deve seguir estritamente esta sequência:

1. **Abrir o Trace Completo (`trace_id`):**
   - Localizar o `trace_id` no Langfuse (`http://localhost:3000`) ou via `observability_manager.get_trace(trace_id)`.
   - Verificar metadados de entrada: `thread_id`, `entry_point` (`webhook` vs `rest_api`), `segment` (`B2C` vs `B2B`), `prompt_version` e `prompt_hash`.
2. **Identificar o Nó e Span do Grafo (`spans`):**
   - Inspecionar a sequência de spans (`identify` → `classify_intent` → `retrieve_context` → `decide_tool` → `confirm_action` → `execute_tool` → `respond` → `evaluate_handoff`).
   - Identificar em qual nó o estado divergiu do esperado ou onde houve pico de latência (`duration_ms`).
3. **Inspecionar os Chunks Recuperados (`retrieved_chunks`) e Monitor de Retrieval:**
   - Verificar quais `chunk_id`s foram retornados pelo `HybridRetriever`, seus scores de similaridade vetorial/BM25 e se houve filtragem correta por `segment`.
   - Conferir no `RetrievalMonitor` se a consulta caiu em `zero_result_queries` ou `low_relevance_queries`.
4. **Inspecionar o Prompt Montado e os Argumentos da Tool (`tool_calls`):**
   - Verificar se o orçamento de contexto (`ContextBudgetManager`) truncou alguma informação crítica e se os argumentos gerados para a Tool respeitam o contrato Pydantic v2.
5. **Classificar a Causa-Raiz e Converter em Teste (`make trace-to-test`):**
   - Classificar a falha em uma das 4 categorias:
     - **(A) Falha de Retrieval / Base de Conhecimento** (chunk ausente, stopword ruidosa, limiar inadequado);
     - **(B) Falha de Engenharia de Prompt / Classificação** (intenção ambígua, falta de instrução de recência);
     - **(C) Falha de Estado / Orquestração LangGraph** (vazamento de variável entre turnos no `ConversationState`);
     - **(D) Falha de Contrato de Tool / Domínio** (divergência de nome de campo ou fuso horário).
   - Executar `make trace-to-test TRACE_ID=<id>` para converter o trace em caso permanente na suíte de regressão antes de aplicar a correção.

---

## 2. Três Casos Reais Investigados e Resolvidos no Projeto

Abaixo estão documentados **3 bugs reais** detectados, diagnosticados e blindados com testes durante a construção do Atendente IA.

---

### Caso Real 1: Vazamento de `action_confirmed=True` Entre Turnos Após Tool Não-Sensível (Fase 3)

- **Sintoma Observado:**
  - Em uma conversa multi-turno com `MemorySaver`, o cliente primeiro consultava um pedido no Turno 1 (`"Qual o status do pedido PED-1001?"`) e, no Turno 2, solicitava o reembolso (`"Quero o reembolso do pedido PED-1001 por defeito"`). Em vez de pausar no nó `confirm_action` e exigir confirmação explícita, o grafo executava `solicitar_reembolso` imediatamente no Turno 2!
- **Diagnóstico Passo a Passo:**
  1. **Reprodução:** Teste de integração `test_sensitive_refund_requires_confirmation_and_executes_on_yes` em `tests/integration/test_agent_graph.py`.
  2. **Inspeção dos Nós (`decide_tool` e `confirm_action`):** No Turno 1, a Tool `consultar_pedido` (não-sensível) passava pelo nó `confirm_action`, que retornava `{"action_confirmed": True, "awaiting_confirmation": False}` para liberar a aresta condicional rumo ao nó `execute_tool`.
  3. **Localização da Causa-Raiz (Categoria C — Estado LangGraph):** No Turno 2, quando `decide_tool` criava uma nova `pending_action` para `solicitar_reembolso` (`requires_confirmation=True`), o campo `action_confirmed` no checkpoint do `MemorySaver` continuava `True` do Turno 1! Quando `confirm_action` inspecionava o estado, via `action_confirmed == True` e pulava o pedido de confirmação.
- **Correção Aplicada (`src/atendente/agent/nodes.py`):**
  - Em `decide_tool`: sempre que uma nova `pending_action` é instanciada, `action_confirmed` é explicitamente resetado para `False`.
  - Em `confirm_action`: Tools que não exigem confirmação (`requires_confirmation=False`) não marcam `action_confirmed=True`; a aresta condicional `_route_after_confirm` em `src/atendente/agent/graph.py` verifica `not pending.get("requires_confirmation") or state.get("action_confirmed")`.
- **Blindagem (Teste de Regressão):**
  - Coberto por `test_sensitive_refund_requires_confirmation_and_executes_on_yes` e pela métrica `unconfirmed_sensitive_action_violation_rate == 0.0` nos 85 casos da suíte de evals.

---

### Caso Real 2: Colisão de Substring `"sla_hours"` com `ContractSLA.resolution_sla_hours` no Nó `respond` (Fase 3)

- **Sintoma Observado:**
  - Quando um cliente B2B perguntava `"Qual o SLA contratado da minha empresa?"`, a Tool `consultar_contrato_sla` era executada com sucesso e retornava `ContractSLA(plan_name="Enterprise", uptime_target=99.9, response_sla_minutes=15, resolution_sla_hours=4)`. Porém, o nó `respond` respondia: *"Chamado registrado com sucesso! Protocolo: N/A, Prioridade: N/A"*.
- **Diagnóstico Passo a Passo:**
  1. **Reprodução:** Teste `test_b2b_sla_and_ticket_opening_flow` em `tests/integration/test_agent_graph.py`.
  2. **Inspeção do Span `respond` (`src/atendente/agent/nodes.py`):** O formatador de resposta verificava o tipo de retorno da Tool usando inspeção ingênua de string: `elif "sla_hours" in str(data):` para identificar um `Ticket` (que possui o campo `sla_hours`).
  3. **Localização da Causa-Raiz (Categoria D — Contrato / Despacho de Resposta):** Como o modelo `ContractSLA` possui o atributo `resolution_sla_hours`, a substring `"sla_hours"` estava contida em `"resolution_sla_hours"`, fazendo com que o retorno de `consultar_contrato_sla` caísse acidentalmente na ramificação de formatação de `Ticket`!
- **Correção Aplicada (`src/atendente/agent/nodes.py`):**
  - Substituída a verificação frágil por substring em `str(data)` por inspeção estruturada de chaves exclusivas do dicionário serializado:
    - Pedido (`Order`): `"tracking_code" in data`
    - Reembolso (`RefundRequest`): `"reason" in data and "order_id" in data`
    - Contrato (`ContractSLA`): `"uptime_target" in data`
    - Chamado (`Ticket`): `"titulo" in data`
- **Blindagem (Teste de Regressão):**
  - Validado em `test_b2b_sla_and_ticket_opening_flow` e nos 10 casos de `governanca_sla_b2b` da suíte `evals/datasets/novaloja_eval_dataset.json`.

---

### Caso Real 3: Falso Positivo de RRF no RAG Híbrido Causado pela Stopword `"com"` em Consultas Fora de Domínio (Fase 2)

- **Sintoma Observado:**
  - Ao testar uma pergunta totalmente fora do escopo da NovaLoja (`"Me passe uma receita de bolo de cenoura com cobertura de chocolate"`), o `HybridRetriever` deveria se abster (`abstained=True`). Em vez disso, retornava `abstained=False` trazendo documentos corporativos da NovaLoja!
- **Diagnóstico Passo a Passo:**
  1. **Reprodução:** Teste `test_abstention_on_out_of_domain_query` em `tests/integration/test_rag_pipeline.py`.
  2. **Inspeção dos Chunks Recuperados (`src/atendente/rag/store.py` e `retriever.py`):** O tokenizador BM25 dividia a consulta em tokens com `len >= 3`. A preposição `"com"` (3 letras) aparecia na consulta (`"com cobertura"`) e também em praticamente todos os 30 documentos da base (`"entre em contato com o suporte"`, `"produto com defeito"`).
  3. **Localização da Causa-Raiz (Categoria A — Retrieval / Fusão Híbrida):** Mesmo com o filtro vetorial rejeitando a consulta por baixa similaridade de cosseno (`< 0.30`), o buscador léxico BM25 pontuava documentos que continham a palavra `"com"` com score `> 0.0`, e o Reciprocal Rank Fusion (`RRF`) promovia esses chunks para a resposta final sem verificar se o score léxico tinha significância real.
- **Correção Aplicada (`src/atendente/rag/store.py`):**
  - Adicionado dicionário de stopwords em português (`PORTUGUESE_STOPWORDS` contendo `"com"`, `"para"`, `"como"`, `"que"`, `"dos"`, `"das"`, `"uma"`, `"por"`, etc.) na função `_tokenize_pt`.
  - Adicionado limiar mínimo de relevância léxica (`min_score: float = 0.50`) em `InMemoryVectorStore.lexical_search` combinado ao limiar vetorial (`min_similarity: float = 0.30`).
- **Blindagem (Teste de Regressão):**
  - Coberto por `test_abstention_on_out_of_domain_query` e pelos 7 casos de `abstencao_e_seguranca` na suíte de 85 evals (`abstention_accuracy = 1.00`).
