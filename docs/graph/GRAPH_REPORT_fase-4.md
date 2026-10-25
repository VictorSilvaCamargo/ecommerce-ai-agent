# Graph Report - atendente-ia  (2026-10-25)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 704 nodes · 1812 edges · 38 communities (21 shown, 17 thin omitted)
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 372 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8e54d11b`
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
- rag/__init__.py
- tools/__init__.py

## God Nodes (most connected - your core abstractions)
1. `NovaLojaToolsService` - 73 edges
2. `AgentNodeHandler` - 28 edges
3. `ConversationState` - 27 edges
4. `ToolResult` - 25 edges
5. `HybridRetriever` - 21 edges
6. `Customer` - 21 edges
7. `CustomerRepository` - 19 edges
8. `KBChunk` - 19 edges
9. `OrderRepository` - 18 edges
10. `Order` - 18 edges

## Surprising Connections (you probably didn't know these)
- `client()` --uses--> `DatabaseManager`  [INFERRED]
  tests/integration/test_api_tools.py → src/atendente/infra/db/database.py
- `client()` --uses--> `Base`  [INFERRED]
  tests/integration/test_api_tools.py → src/atendente/infra/db/models.py
- `client()` --calls--> `seed_data()`  [INFERRED]
  tests/integration/test_api_tools.py → src/atendente/infra/db/seed.py
- `sample_customer_b2b()` --uses--> `DocumentType`  [INFERRED]
  tests/unit/test_domain_services.py → src/atendente/domain/validators.py
- `sample_customer_b2c()` --uses--> `DocumentType`  [INFERRED]
  tests/unit/test_domain_services.py → src/atendente/domain/validators.py

## Import Cycles
- None detected.

## Communities (38 total, 17 thin omitted)

### Community 0 - "KBChunk"
Cohesion: 0.07
Nodes (56): api_abrir_chamado(), api_buscar_base_conhecimento(), api_consultar_contrato_sla(), api_consultar_fatura(), api_consultar_pedido(), api_identificar_cliente(), api_solicitar_reembolso(), api_transferir_para_humano() (+48 more)

### Community 1 - "NovaLojaToolsService"
Cohesion: 0.06
Nodes (30): chunk_directory(), chunk_markdown_document(), ChunkingConfig, detect_segment_from_path(), estimate_tokens(), DeterministicEmbeddingService, EmbeddingService, IngestionPipeline (+22 more)

### Community 2 - "Customer"
Cohesion: 0.06
Nodes (23): build_conversation_graph(), route_after_classify(), AgentNodeHandler, ConversationState, test_b2b_journey_sla_contract(), test_b2c_journey_order_and_refund_with_confirmation(), test_handoff_requested_explicitly(), test_long_conversation_summarization_and_context_preservation() (+15 more)

### Community 3 - "src_atendente_infra_db_repositories"
Cohesion: 0.06
Nodes (22): BudgetedContextResult, ContextBudgetManager, count_tokens(), SectionBudgetConfig, truncate_text_to_tokens(), build_classifier_prompt(), IntentClassificationOutput, PromptEvaluationReport (+14 more)

### Community 4 - "mongodb"
Cohesion: 0.06
Nodes (17): do_run_migrations(), run_async_migrations(), run_migrations_online(), upgrade(), Settings, DatabaseManager, Base, ContractSLAORM (+9 more)

### Community 5 - "pytest"
Cohesion: 0.11
Nodes (23): ContractTier, Customer, CustomerSegment, InvoiceStatus, Order, OrderItem, OrderStatus, RefundStatus (+15 more)

### Community 6 - "test_tools.py"
Cohesion: 0.10
Nodes (10): AnthropicLLMClient, GeminiLLMClient, LLMClient, LLMMessage, LLMResponse, LLMToolCall, MockLLMClient, OpenAILLMClient (+2 more)

### Community 7 - "ToolAuditEntry"
Cohesion: 0.07
Nodes (35): MONGO_INITDB_DATABASE, MONGO_INITDB_ROOT_PASSWORD, MONGO_INITDB_ROOT_USERNAME, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, interval, retries (+27 more)

### Community 8 - "steps"
Cohesion: 0.19
Nodes (14): clean_digits(), DocumentType, validate_cnpj(), validate_cpf(), validate_document(), test_clean_digits(), test_property_clean_digits(), test_validate_cnpj_invalid_digits() (+6 more)

### Community 9 - "typing"
Cohesion: 0.12
Nodes (16): jobs, quality-and-tests, name, branches, branches, runs-on, steps, name (+8 more)

### Community 10 - "Atendente IA Platform"
Cohesion: 0.26
Nodes (6): compute_hmac_signature(), verify_webhook_hmac(), test_webhook_dlq_inspection_endpoint(), test_webhook_rejects_invalid_hmac_and_replay_attack(), test_webhook_valid_hmac_and_idempotency_deduplication(), test_hmac_signature_verification_and_tampering_defense()

### Community 13 - "Motor RAG H?brido"
Cohesion: 0.32
Nodes (6): test_api_auth_failure_with_wrong_key(), test_api_auth_failure_without_header(), test_api_identificar_cliente_success(), test_api_solicitar_reembolso_sensitive_confirmed_success(), test_api_solicitar_reembolso_sensitive_requires_confirmation(), test_health_check()

### Community 14 - "Dom?nio Central (Domain)"
Cohesion: 0.20
Nodes (3): MessageWorkerProcessor, process_webhook_message_task(), WebhookMessagePayload

### Community 15 - "atendente/__init__.py"
Cohesion: 0.26
Nodes (3): DLQEntry, DLQStore, RedisDLQStore

### Community 16 - "Stack Langfuse + Prometheus"
Cohesion: 0.26
Nodes (6): InMemoryDLQStore, TransientWorkerError, test_worker_exhausts_retries_and_routes_to_dlq(), always_failing_handler(), test_worker_retries_with_exponential_backoff_and_succeeds(), flaky_handler()

### Community 17 - "atendente-ia"
Cohesion: 0.25
Nodes (8): Servidor MCP Oficial, Roadmap de Fases (0 a 6), Cat?logo de Skills & Fallback, Atendente IA Platform, Jornada B2B, Jornada B2C, A??o Sens?vel (Reembolso), Contrato de Tools API

### Community 18 - "agent/__init__.py"
Cohesion: 0.36
Nodes (3): http_exception_handler(), receive_webhook_message(), validation_exception_handler()

### Community 19 - "api/__init__.py"
Cohesion: 0.29
Nodes (6): args, id, repos, hooks, repo, rev

### Community 20 - "domain/__init__.py"
Cohesion: 0.33
Nodes (3): ConversationState Tipado, Motor RAG H?brido, Orquestrador LangGraph

### Community 21 - "infra/__init__.py"
Cohesion: 0.33
Nodes (3): health_check(), inspect_dlq_messages(), list_tool_schemas()

### Community 23 - "rag/__init__.py"
Cohesion: 0.40
Nodes (3): Dom?nio Central (Domain), Adaptador FastAPI, Arquitetura Hexagonal

## Knowledge Gaps
- **41 isolated node(s):** `args`, `id`, `repo`, `rev`, `atendente-ia` (+36 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 209 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `NovaLojaToolsService` connect `KBChunk` to `NovaLojaToolsService`, `http_exception_handler`, `pytest`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Are the 22 inferred relationships involving `NovaLojaToolsService` (e.g. with `ContractSLA` and `Customer`) actually correct?**
  _`NovaLojaToolsService` has 22 INFERRED edges - model-reasoned connections that need verification._
- **What connects `args`, `id`, `repo` to the rest of the system?**
  _41 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `KBChunk` be split into smaller, more focused modules?**
  _Cohesion score 0.07123964027508375 - nodes in this community are weakly interconnected._
- **Why does `AgentNodeHandler` connect `Customer` to `test_tools.py`?**
  _High betweenness centrality (0.003) - this node is a cross-community bridge._
- **Should `NovaLojaToolsService` be split into smaller, more focused modules?**
  _Cohesion score 0.058823529411764705 - nodes in this community are weakly interconnected._
- **Should `Customer` be split into smaller, more focused modules?**
  _Cohesion score 0.06103286384976526 - nodes in this community are weakly interconnected._