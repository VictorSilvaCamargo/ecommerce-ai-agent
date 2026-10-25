# Graph Report - atendente-ia  (2026-10-25)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 870 nodes · 2077 edges · 49 communities (32 shown, 17 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 392 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `379e14cd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- KBChunk
- NovaLojaToolsService
- Customer
- src_atendente_infra_db_repositories
- mongodb
- pytest
- test_tools.py
- ToolAuditEntry
- steps
- typing
- Atendente IA Platform
- http_exception_handler
- repos
- Motor RAG H?brido
- Dom?nio Central (Domain)
- atendente/__init__.py
- Stack Langfuse + Prometheus
- atendente-ia
- agent/__init__.py
- api/__init__.py
- domain/__init__.py
- infra/__init__.py
- mcp_server/__init__.py
- rag/__init__.py
- tools/__init__.py
- workers/__init__.py
- rag/__init__.py
- tools/__init__.py
- workers/__init__.py
- workers/__init__.py
- api/__init__.py
- domain/__init__.py
- infra/__init__.py
- workers/__init__.py
- atendente-ia

## God Nodes (most connected - your core abstractions)
1. `NovaLojaToolsService` - 73 edges
2. `AgentNodeHandler` - 28 edges
3. `ConversationState` - 27 edges
4. `ToolResult` - 25 edges
5. `Customer` - 21 edges
6. `HybridRetriever` - 21 edges
7. `CustomerRepository` - 19 edges
8. `KBChunk` - 19 edges
9. `OrderRepository` - 18 edges
10. `Order` - 18 edges

## Surprising Connections (you probably didn't know these)
- `client()` --uses--> `InMemoryAuditRepository`  [INFERRED]
  tests/integration/test_api_tools.py → src/atendente/infra/audit.py
- `client()` --uses--> `NovaLojaToolsService`  [INFERRED]
  tests/integration/test_api_tools.py → src/atendente/tools/service.py
- `tools_service()` --calls--> `InMemoryAuditRepository`  [INFERRED]
  tests/unit/test_agent_nodes.py → src/atendente/infra/audit.py
- `tools_service()` --uses--> `InMemoryAuditRepository`  [INFERRED]
  tests/unit/test_tools.py → src/atendente/infra/audit.py
- `tools_service()` --uses--> `NovaLojaToolsService`  [INFERRED]
  tests/unit/test_tools.py → src/atendente/tools/service.py

## Import Cycles
- None detected.

## Communities (49 total, 17 thin omitted)

### Community 0 - "KBChunk"
Cohesion: 0.06
Nodes (53): get_tools_service(), ContractSLA, ContractTier, Customer, CustomerSegment, Invoice, InvoiceStatus, Order (+45 more)

### Community 1 - "NovaLojaToolsService"
Cohesion: 0.07
Nodes (46): api_abrir_chamado(), api_buscar_base_conhecimento(), api_consultar_contrato_sla(), api_consultar_fatura(), api_consultar_pedido(), api_identificar_cliente(), api_solicitar_reembolso(), api_transferir_para_humano() (+38 more)

### Community 2 - "Customer"
Cohesion: 0.06
Nodes (31): chunk_directory(), chunk_markdown_document(), ChunkingConfig, detect_segment_from_path(), estimate_tokens(), DeterministicEmbeddingService, EmbeddingService, IngestionPipeline (+23 more)

### Community 3 - "src_atendente_infra_db_repositories"
Cohesion: 0.06
Nodes (22): BudgetedContextResult, ContextBudgetManager, count_tokens(), SectionBudgetConfig, truncate_text_to_tokens(), build_classifier_prompt(), IntentClassificationOutput, PromptEvaluationReport (+14 more)

### Community 4 - "mongodb"
Cohesion: 0.07
Nodes (20): build_conversation_graph(), route_after_classify(), AgentNodeHandler, ConversationState, test_b2b_journey_sla_contract(), test_b2c_journey_order_and_refund_with_confirmation(), test_handoff_requested_explicitly(), test_long_conversation_summarization_and_context_preservation() (+12 more)

### Community 5 - "pytest"
Cohesion: 0.06
Nodes (23): AgentPredictedOutcome, calibrate_judge_against_human_sample(), DeterministicEvaluation, EvalCase, evaluate_case_deterministically(), JudgeScore, LLMJudge, build_canonical_85_cases() (+15 more)

### Community 6 - "test_tools.py"
Cohesion: 0.08
Nodes (14): do_run_migrations(), run_async_migrations(), run_migrations_online(), upgrade(), Settings, test_api_auth_failure_with_wrong_key(), test_api_auth_failure_without_header(), test_api_identificar_cliente_success() (+6 more)

### Community 7 - "ToolAuditEntry"
Cohesion: 0.11
Nodes (10): AnthropicLLMClient, GeminiLLMClient, LLMClient, LLMMessage, LLMResponse, LLMToolCall, MockLLMClient, OpenAILLMClient (+2 more)

### Community 8 - "steps"
Cohesion: 0.09
Nodes (11): configure_structured_logging(), mask_pii_dict(), mask_pii_text(), ObservabilityManager, _sanitize_value(), TraceRecord, TraceSpan, test_mask_pii_dict_recursively_masks_nested_structures() (+3 more)

### Community 9 - "typing"
Cohesion: 0.13
Nodes (5): lifespan(), AuditRepository, InMemoryAuditRepository, MongoAuditRepository, ToolAuditEntry

### Community 10 - "Atendente IA Platform"
Cohesion: 0.20
Nodes (13): clean_digits(), validate_cnpj(), validate_cpf(), validate_document(), test_clean_digits(), test_property_clean_digits(), test_validate_cnpj_invalid_digits(), test_validate_cnpj_invalid_repeated_digits() (+5 more)

### Community 11 - "http_exception_handler"
Cohesion: 0.13
Nodes (4): IdempotencyStore, InMemoryIdempotencyStore, RedisIdempotencyStore, test_idempotency_store_blocks_duplicates()

### Community 12 - "repos"
Cohesion: 0.18
Nodes (8): InMemoryDLQStore, MessageWorkerProcessor, TransientWorkerError, WebhookMessagePayload, test_worker_exhausts_retries_and_routes_to_dlq(), always_failing_handler(), test_worker_retries_with_exponential_backoff_and_succeeds(), flaky_handler()

### Community 13 - "Motor RAG H?brido"
Cohesion: 0.12
Nodes (16): jobs, quality-and-tests, name, branches, branches, runs-on, steps, name (+8 more)

### Community 14 - "Dom?nio Central (Domain)"
Cohesion: 0.17
Nodes (3): DLQEntry, DLQStore, RedisDLQStore

### Community 15 - "atendente/__init__.py"
Cohesion: 0.24
Nodes (6): compute_hmac_signature(), verify_webhook_hmac(), test_webhook_dlq_inspection_endpoint(), test_webhook_rejects_invalid_hmac_and_replay_attack(), test_webhook_valid_hmac_and_idempotency_deduplication(), test_hmac_signature_verification_and_tampering_defense()

### Community 16 - "Stack Langfuse + Prometheus"
Cohesion: 0.18
Nodes (10): apiVersion, path, providers, disableDeletion, folder, name, options, orgId (+2 more)

### Community 17 - "atendente-ia"
Cohesion: 0.20
Nodes (10): GF_SECURITY_ADMIN_PASSWORD, GF_SECURITY_ADMIN_USER, GF_USERS_ALLOW_SIGN_UP, container_name, depends_on, environment, image, ports (+2 more)

### Community 18 - "agent/__init__.py"
Cohesion: 0.22
Nodes (9): MONGO_INITDB_DATABASE, MONGO_INITDB_ROOT_PASSWORD, MONGO_INITDB_ROOT_USERNAME, container_name, environment, image, ports, volumes (+1 more)

### Community 19 - "api/__init__.py"
Cohesion: 0.22
Nodes (9): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, container_name, environment, image, ports, volumes (+1 more)

### Community 20 - "domain/__init__.py"
Cohesion: 0.22
Nodes (8): apiVersion, datasources, access, editable, isDefault, name, type, url

### Community 21 - "infra/__init__.py"
Cohesion: 0.22
Nodes (8): global, evaluation_interval, scrape_interval, scrape_configs, job_name, metrics_path, static_configs, targets

### Community 22 - "mcp_server/__init__.py"
Cohesion: 0.25
Nodes (8): Servidor MCP Oficial, Roadmap de Fases (0 a 6), Cat?logo de Skills & Fallback, Atendente IA Platform, Jornada B2B, Jornada B2C, A??o Sens?vel (Reembolso), Contrato de Tools API

### Community 23 - "rag/__init__.py"
Cohesion: 0.29
Nodes (7): postgres, container_name, depends_on, image, ports, condition, langfuse-server

### Community 24 - "tools/__init__.py"
Cohesion: 0.57
Nodes (7): interval, retries, test, timeout, healthcheck, healthcheck, healthcheck

### Community 25 - "workers/__init__.py"
Cohesion: 0.29
Nodes (6): args, id, repos, hooks, repo, rev

### Community 26 - "rag/__init__.py"
Cohesion: 0.33
Nodes (5): services, volumes, mongodb_data, postgres_data, redis_data

### Community 27 - "tools/__init__.py"
Cohesion: 0.33
Nodes (6): DATABASE_URL, NEXTAUTH_SECRET, NEXTAUTH_URL, SALT, TELEMETRY_ENABLED, environment

### Community 28 - "workers/__init__.py"
Cohesion: 0.33
Nodes (3): ConversationState Tipado, Motor RAG H?brido, Orquestrador LangGraph

### Community 30 - "api/__init__.py"
Cohesion: 0.40
Nodes (5): container_name, image, ports, volumes, prometheus

### Community 31 - "domain/__init__.py"
Cohesion: 0.40
Nodes (5): container_name, image, ports, volumes, redis

### Community 32 - "infra/__init__.py"
Cohesion: 0.40
Nodes (3): Dom?nio Central (Domain), Adaptador FastAPI, Arquitetura Hexagonal

## Knowledge Gaps
- **82 isolated node(s):** `name`, `branches`, `branches`, `runs-on`, `name` (+77 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 294 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `NovaLojaToolsService` connect `NovaLojaToolsService` to `KBChunk`, `typing`, `Customer`?**
  _High betweenness centrality (0.006) - this node is a cross-community bridge._
- **Are the 22 inferred relationships involving `NovaLojaToolsService` (e.g. with `ContractSLA` and `Customer`) actually correct?**
  _`NovaLojaToolsService` has 22 INFERRED edges - model-reasoned connections that need verification._
- **What connects `name`, `branches`, `branches` to the rest of the system?**
  _82 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `KBChunk` be split into smaller, more focused modules?**
  _Cohesion score 0.0579785392869505 - nodes in this community are weakly interconnected._
- **Why does `AgentNodeHandler` connect `mongodb` to `ToolAuditEntry`?**
  _High betweenness centrality (0.002) - this node is a cross-community bridge._
- **Should `NovaLojaToolsService` be split into smaller, more focused modules?**
  _Cohesion score 0.06591865357643759 - nodes in this community are weakly interconnected._
- **Should `Customer` be split into smaller, more focused modules?**
  _Cohesion score 0.059097127222982215 - nodes in this community are weakly interconnected._