# Insights do Grafo de Conhecimento (Graphify)

Registro evolutivo das métricas topológicas, nós centrais, acoplamentos e nós isolados por fase do projeto.

---

### Fase 0: Descoberta e Especificação
- **Nós Centrais:** `Atendente IA Platform` (4 arestas, alta centralidade de intermediação), `Orquestrador LangGraph` (3 arestas) e `Motor RAG Híbrido` (3 arestas), consolidando o núcleo arquitetural.
- **Acoplamentos e Conexões:** Conexões interdocumentais documentadas entre os 5 ADRs e seus respectivos módulos na Arquitetura Hexagonal, com 100% de precisão de extração.
- **Módulos Órfãos / Fracos:** 6 nós periféricos identificados (`Jornada B2B`, `Ação Sensível (Reembolso)`, `ConversationState Tipado`, `Servidor MCP Oficial`, `Stack Langfuse + Prometheus`), normais para a fase de especificação conceitual.
- **Ajustes e Correções:** Estruturação formal do grafo conceitual inicial, garantindo alinhamento bidirecional entre SPEC, ADRs, ROADMAP e regras de camadas antes de qualquer código ser escrito.

---

### Fase 1: Fundação e API de Tools
- **Nós Centrais:** `domain/models.py` (hub com múltiplos tipos e contratos Pydantic), `tools/service.py` (`NovaLojaToolsService` com 8 métodos e 8 inputs tipados) e `infra/db/models.py` (tabelas SQLAlchemy ORM).
- **Acoplamentos e Conexões:** Validação formal de isolamento de camadas; `infra/db/repositories.py` depende unidirecionalmente de `domain/models.py`. O comando `graphify path "domain" "infra"` comprovou ausência total de caminhos direcionados do núcleo para fora.
- **Módulos Órfãos / Fracos:** Subpacotes `agent/`, `rag/`, `mcp_server/` e `workers/` ainda possuem apenas `__init__.py`, aguardando implementação nas fases 2, 3, 4 e 6.
- **Ajustes e Correções:** Contratos de camadas validados no `import-linter` (3 contratos preservados, 0 violações) e suíte de 41 testes com 88% de cobertura no domínio e tools.

---

### Fase 2: Pipeline de RAG
- **Nós Centrais:** `KBChunk` (19 arestas, modelo unificado de chunk e metadados) e `HybridRetriever` (18 arestas, orquestrador RRF vetorial + BM25) consolidaram-se como novas abstrações centrais de RAG ao lado de `NovaLojaToolsService`.
- **Acoplamentos e Conexões:** Camada `rag/` permanece estritamente isolada de `api/` e `agent/` (contrato comprovado no `import-linter`). `NovaLojaToolsService.buscar_base_conhecimento` consome `HybridRetriever` via injeção de dependência opcional sem acoplamento reverso.
- **Módulos Órfãos / Fracos:** Subpastas `agent/`, `mcp_server/` e `workers/` continuam apenas com esqueletos, preparando a transição para a orquestração com LangGraph na Fase 3.
- **Ajustes e Correções:** Adicionados filtro de stopwords em português e limiares de corte (cosseno >= 0.30, léxico >= 0.50) no `InMemoryVectorStore`/`HybridRetriever`, assegurando abstenção perfeita em perguntas fora de domínio com retorno de erro seguro `NO_RELEVANT_KNOWLEDGE` (`abstained=True`). Benchmark comprovou Configuração B (512 tokens / 64 overlap) com Hit Rate@3 = 0.90 e MRR = 0.90.

---

### Fase 3: Grafo de Conversação com LangGraph
- **Nós Centrais:** `AgentNodeHandler` (29 arestas, despachante dos 8 nós funcionais) e `ConversationState` (27 arestas, estado unificado tipado) emergiram como God Nodes centrais da camada conversacional, conectando-se a `NovaLojaToolsService` (72 arestas).
- **Acoplamentos e Conexões:** `agent` consome `tools` e `rag` respeitando a arquitetura hexagonal (3/3 contratos do `import-linter` rigorosamente preservados). Camada `infra/llm` disponibiliza abstração unificada `LLMClient` permitindo testes 100% determinísticos via `MockLLMClient`.
- **Módulos Órfãos / Fracos:** Apenas `workers/` (Fase 4) e `mcp_server/` (Fase 6) permanecem com `__init__.py`.
- **Ajustes e Correções:** Ciclo de `doubt-driven-development` identificou e neutralizou risco crítico de vazamento de confirmação (`action_confirmed` herdado entre turnos); gatekeeper agora exige estado estritamente pendente e intenção afirmativa no turno subsequente. Sumarização periódica e checkpointing no `MemorySaver` garantiram estabilidade e preservação contextual em conversas de 10+ turnos. Suíte ampliada para 71 testes com 91% de cobertura.

---

### Fase 3b: Engenharia de Prompts e Janela de Contexto
- **Nós Centrais:** `ContextBudgetManager` (`budget.py`), `PromptVersion` (`system.py`) e `format_rag_context_safe` (`rag_delimiters.py`) surgiram como sub-hubs na comunidade do agente, expandindo o grafo para 631 nós e 1619 arestas em 30 comunidades.
- **Acoplamentos e Conexões:** O subpacote `src/atendente/agent/prompts/` foi integrado de forma unidirecional ao `AgentNodeHandler` e `ConversationState` sem introduzir dependências circulares ou violar os 3 contratos do `import-linter`.
- **Módulos Órfãos / Fracos:** Apenas `workers/` (Fase 4) e `mcp_server/` (Fase 6) aguardam implementação.
- **Ajustes e Correções:** Implementada alocação estrita de orçamento de tokens por seção (`system`, `tools`, `rag`, `history`) validada via Hypothesis, sanitização de *indirect prompt injection* com tags XML `<contexto_seguro>` e avaliação comparativa de 3 versões (`v1.0.0`, `v2.0.0`, `v3.0.0`), elevando o score global de 0.00 para 1.00 em `docs/EVALS.md`.

---

### Fase 4: Assincronismo e Webhooks
- **Nós Centrais:** `MessageWorkerProcessor`, `WebhookMessagePayload`, `IdempotencyStore` e `DLQStore` conectaram a camada `workers/` à API FastAPI (`main.py`), expandindo o grafo para 704 nós, 1812 arestas e 38 comunidades.
- **Acoplamentos e Conexões:** A camada `api/` consome unidirecionalmente `workers/security.py`, `workers/idempotency.py` e `workers/tasks.py`. Os 3 contratos do `import-linter` permanecem 100% preservados.
- **Módulos Órfãos / Fracos:** O nó `workers/__init__.py` dejó de ser órfão; apenas `mcp_server/` aguarda implementação na Fase 6.
- **Ajustes e Correções:** Aplicada modelagem de ameaças STRIDE (`security-and-hardening`) na fronteira `/webhook/messages`: verificação HMAC-SHA256 em tempo constante (`hmac.compare_digest`), janela anti-replay de 300s no header `X-Webhook-Timestamp`, desduplicação `SETNX` e roteamento automático para `dlq_unhandled_messages` após 3 falhas com backoff exponencial.

---

### Fase 5: Observabilidade, Evals e Ciclo de Debug
- **Nós Centrais:** `ObservabilityManager` (`observability.py`), `TraceRecord`, `RetrievalMonitor` (`monitor.py`), `LLMJudge` (`rubrics.py`) e `run_full_eval_suite` (`run_evals.py`) consolidaram o subsistema de observabilidade e avaliação contínua, expandindo o grafo para 870 nós, 2077 arestas e 49 comunidades.
- **Acoplamentos e Conexões:** `api/main.py` integra o middleware HTTP RED e os endpoints `/metrics` e `/feedback` consumindo `infra/observability.py`, enquanto `rag/monitor.py` permanece desacoplado de `api` e `agent` (3/3 contratos do `import-linter` preservados).
- **Módulos Órfãos / Fracos:** Apenas `src/atendente/mcp_server/__init__.py` permanece aguardando a Fase 6 (servidor MCP e guardrails finais).
- **Ajustes e Correções:** Implementado mascaramento recursivo de PII (`mask_pii_text` e `mask_pii_dict` no `structlog`), conversor `make trace-to-test`, dataset de 85 casos rotulados (`novaloja_eval_dataset.json`) com 100% de aprovação nos gates determinísticos e de LLM-as-a-Judge calibrado, e documentação de 3 bugs reais em `docs/DEBUG_PLAYBOOK.md`.
