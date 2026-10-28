# Relatório de Auditoria e Prontidão de Lançamento (`/ship`) — Atendente IA (NovaLoja)

**Data da Auditoria:** 2026-10-25
**Versão Avaliada:** `v1.0.0` (Branch `fase-6-mcp-seguranca-ship`)
**Parecer Final:** **GO (APROVADO PARA PRODUÇÃO)**

Este documento consolida a revisão tripla exigida pelo comando `/ship` (**Code Reviewer**, **Security Auditor** e **Test & Performance Engineer**), além da verificação integral do **Definition of Done (DoD)** do projeto.

---

## 1. Parecer do Code Reviewer (`code-review-and-quality` + `code-simplification`)

### 1.1 Arquitetura e Fronteiras de Camadas
- **Arquitetura Hexagonal Imposta por Contrato (`.importlinter`):**
  - `Domain layer must not import from any outer layers`: **KEPT**
  - `Tools layer must not import from api or agent`: **KEPT**
  - `RAG layer must not import from api or agent`: **KEPT**
- **Verificação Topológica (`graphify path "domain" "infra"`):** Nenhuma dependência do núcleo de domínio (`src/atendente/domain/`) para camadas externas (`infra`, `api`, `agent`, `tools`).
- **Tipagem Estrita (`uv run mypy --strict src`):** `Success: no issues found in 48 source files`.
- **Qualidade Estática e Formatação (`uv run ruff check .` & `ruff format --check .`):** `All checks passed! 138 files already formatted`.
- **Simplificação (`/code-simplify`):**
  - Extraído helper `_dump_tool_result` em `src/atendente/mcp_server/server.py` eliminando duplicação de serialização JSON nas 8 Tools do servidor MCP.
  - Despacho determinístico por chaves estruturadas no nó `respond` (`src/atendente/agent/nodes.py`), evitando inspeções frágeis em strings.

---

## 2. Parecer do Security Auditor (`security-and-hardening` + `doubt-driven-development`)

| Vetor de Ameaça / Controle | Implementação Verificada | Evidência de Teste | Status |
|---|---|---|---|
| **Autenticação de Endpoints REST** | Header `X-API-Key` validado via dependência `verify_api_key` em todas as rotas de Tools, DLQ e Feedback | `tests/integration/test_api_tools.py` | **APROVADO** |
| **Autenticação e Anti-Replay de Webhooks** | `verify_webhook_hmac` com `hmac.compare_digest` (tempo constante) + janela de 300s em `X-Webhook-Timestamp` | `tests/unit/test_workers_and_webhooks.py` | **APROVADO** |
| **Idempotência de Mensagens** | `IdempotencyStore` (`SET message_id NX EX 86400`) descartando replays com `200 OK (duplicate_ignored)` | `tests/unit/test_workers_and_webhooks.py` | **APROVADO** |
| **Prevenção de IDOR (Posse de Pedido)** | `consultar_pedido` e `solicitar_reembolso` validam `order.customer_id == customer_id` antes de exibir ou alterar dados | `tests/unit/test_tools.py` | **APROVADO** |
| **Gatekeeper de Ação Sensível (`solicitar_reembolso`)** | Bloqueio estrito no nó `confirm_action` (`requires_confirmation=True`) + reset de `action_confirmed=False` a cada nova decisão de Tool | `tests/integration/test_agent_graph.py` & `test_evals_suite.py` (0% violação em 85 casos) | **APROVADO** |
| **Defesa contra Direct & Indirect Prompt Injection** | `SecurityGuardrails.validate_input` (`guardrails.py`) + delimitação XML `<contexto_seguro>` e sanitização em `rag_delimiters.py` | `tests/security/test_security_guardrails.py` & `tests/unit/test_prompts_and_budget.py` | **APROVADO** |
| **Prevenção de Vazamento de Credenciais e PII** | `SecurityGuardrails.sanitize_output` + processador `mask_pii_dict` no `structlog` mascarando CPF, CNPJ, e-mail, telefone e URIs de banco | `tests/security/test_security_guardrails.py` & `tests/unit/test_observability.py` | **APROVADO** |
| **Rate Limit de Ações por Thread** | `SecurityGuardrails.check_and_record_action` bloqueia execuções excessivas de Tools na mesma sessão (`ACTION_RATE_LIMIT_EXCEEDED`) | `tests/security/test_security_guardrails.py` | **APROVADO** |

---

## 3. Parecer do Test & Performance Engineer (`test-driven-development` + Load Test)

- **Suíte Automatizada Completa:** **101 testes aprovados** (unitários, propriedade Hypothesis, contrato OpenAPI, integração RAG/LangGraph/MCP, suíte de 85 evals, segurança e benchmark de latência).
- **Cobertura de Código (`pytest --cov=src/atendente`):** **88% de cobertura global** (`100%` em `mcp_server/server.py`, `guardrails.py`, `chunker.py`, `models.py`, `classifier.py`, `evaluator.py`, `rag_delimiters.py`; `97%` em `domain/models.py`, `domain/services.py`, `graph.py`, `observability.py`, `monitor.py`, `retriever.py`).
- **Benchmark de Latência da API (`tests/integration/test_api_latency_benchmark.py` & `tests/load/locustfile.py`):**
  - 100 requisições sequenciais e concorrentes nas rotas `/health`, `/tools/schemas`, `/webhook/messages` (com validação HMAC-SHA256 e idempotência) e `/metrics`.
  - **Resultado Empírico:** `p50 < 20 ms`, `p95 < 50 ms` (muito abaixo do teto de **300 ms** exigido pela especificação).

---

## 4. Checklist Final — Definition of Done (DoD)

- [x] **1. Repositório estruturado com `uv`, Docker Compose, Alembic e CI:** `pyproject.toml`, `docker-compose.yml` (Postgres/pgvector, MongoDB, Redis, Langfuse, Prometheus, Grafana), `alembic/` e `.github/workflows/ci.yml`.
- [x] **2. Arquitetura em camadas verificada por `import-linter` e `graphify`:** 3/3 contratos mantidos no `lint-imports` e ausência de caminho `domain -> infra` comprovada no `graphify`.
- [x] **3. API FastAPI com 8 Tools B2C/B2B, validação Pydantic v2 e auditoria MongoDB:** Implementada em `src/atendente/tools/` e `src/atendente/api/main.py`.
- [x] **4. Pipeline RAG Híbrido (Vetorial + BM25 RRF) sobre base B2C/B2B com citações e abstenção:** 30 documentos em `data/kb/`, benchmark de chunking documentado no ADR-0004 (Config B 512/64, Hit Rate@3 = 0.90, MRR = 0.90).
- [x] **5. Agente LangGraph com estado tipado, persistência, sumarização, gatekeeper de ação sensível e handoff humano:** Implementado em `src/atendente/agent/`.
- [x] **6. Engenharia de Prompts versionada (`v1.0.0`, `v2.0.0`, `v3.0.0`) com orçamento de tokens e proteção contra injection:** Implementada em `src/atendente/agent/prompts/` e avaliada em `docs/EVALS.md`.
- [x] **7. Webhooks assíncronos com HMAC-SHA256, anti-replay, idempotência Redis, Celery backoff e DLQ:** Implementados em `src/atendente/workers/`.
- [x] **8. Observabilidade completa (Langfuse, Prometheus `/metrics`, Grafana dashboard, PII masking, `/feedback`):** Implementada em `src/atendente/infra/observability.py` e `infra/`.
- [x] **9. Suíte de >= 80 casos de Evals (85 casos) + LLM-as-a-Judge calibrado + `make trace-to-test` + `DEBUG_PLAYBOOK.md` com 3 bugs reais:** Implementados em `evals/` e `docs/DEBUG_PLAYBOOK.md`.
- [x] **10. Servidor MCP oficial em Python, Guardrails de Segurança, Load Test Locust (`p95 < 300ms`) e documentação final:** Implementados em `src/atendente/mcp_server/server.py`, `src/atendente/agent/guardrails.py`, `tests/load/locustfile.py` e `README.md`.
