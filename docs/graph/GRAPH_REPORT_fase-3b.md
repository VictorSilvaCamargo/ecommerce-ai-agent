# Graph Report - atendente-ia  (2026-10-25)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 631 nodes · 1619 edges · 30 communities (16 shown, 14 thin omitted)
- Extraction: 76% EXTRACTED · 24% INFERRED · 0% AMBIGUOUS · INFERRED: 392 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `35a7d67a`
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
- agent/__init__.py
- api/__init__.py

## God Nodes (most connected - your core abstractions)
1. `NovaLojaToolsService` - 72 edges
2. `AgentNodeHandler` - 28 edges
3. `ConversationState` - 27 edges
4. `ToolResult` - 24 edges
5. `HybridRetriever` - 21 edges
6. `Customer` - 20 edges
7. `KBChunk` - 19 edges
8. `CustomerRepository` - 18 edges
9. `Order` - 17 edges
10. `OrderRepository` - 17 edges

## Surprising Connections (you probably didn't know these)
- `client()` --uses--> `InMemoryAuditRepository`  [INFERRED]
  tests/integration/test_api_tools.py → src/atendente/infra/audit.py
- `client()` --uses--> `DatabaseManager`  [INFERRED]
  tests/integration/test_api_tools.py → src/atendente/infra/db/database.py
- `client()` --uses--> `Base`  [INFERRED]
  tests/integration/test_api_tools.py → src/atendente/infra/db/models.py
- `client()` --calls--> `seed_data()`  [INFERRED]
  tests/integration/test_api_tools.py → src/atendente/infra/db/seed.py
- `tools_service_with_rag()` --calls--> `InMemoryAuditRepository`  [INFERRED]
  tests/integration/test_agent_graph.py → src/atendente/infra/audit.py

## Import Cycles
- None detected.

## Communities (30 total, 14 thin omitted)

### Community 0 - "KBChunk"
Cohesion: 0.06
Nodes (32): chunk_directory(), chunk_markdown_document(), ChunkingConfig, detect_segment_from_path(), estimate_tokens(), DeterministicEmbeddingService, EmbeddingService, IngestionPipeline (+24 more)

### Community 1 - "NovaLojaToolsService"
Cohesion: 0.09
Nodes (41): get_tools_service(), ContractSLA, ContractTier, Customer, CustomerSegment, Invoice, InvoiceStatus, Order (+33 more)

### Community 2 - "Customer"
Cohesion: 0.06
Nodes (22): BudgetedContextResult, ContextBudgetManager, count_tokens(), SectionBudgetConfig, truncate_text_to_tokens(), build_classifier_prompt(), IntentClassificationOutput, PromptEvaluationReport (+14 more)

### Community 3 - "src_atendente_infra_db_repositories"
Cohesion: 0.07
Nodes (36): api_abrir_chamado(), api_buscar_base_conhecimento(), api_consultar_contrato_sla(), api_consultar_fatura(), api_consultar_pedido(), api_identificar_cliente(), api_solicitar_reembolso(), api_transferir_para_humano() (+28 more)

### Community 4 - "mongodb"
Cohesion: 0.07
Nodes (20): build_conversation_graph(), route_after_classify(), AgentNodeHandler, ConversationState, test_b2b_journey_sla_contract(), test_b2c_journey_order_and_refund_with_confirmation(), test_handoff_requested_explicitly(), test_long_conversation_summarization_and_context_preservation() (+12 more)

### Community 5 - "pytest"
Cohesion: 0.06
Nodes (18): do_run_migrations(), run_async_migrations(), run_migrations_online(), upgrade(), Settings, DatabaseManager, Base, ContractSLAORM (+10 more)

### Community 6 - "test_tools.py"
Cohesion: 0.10
Nodes (10): AnthropicLLMClient, GeminiLLMClient, LLMClient, LLMMessage, LLMResponse, LLMToolCall, MockLLMClient, OpenAILLMClient (+2 more)

### Community 7 - "ToolAuditEntry"
Cohesion: 0.07
Nodes (35): MONGO_INITDB_DATABASE, MONGO_INITDB_ROOT_PASSWORD, MONGO_INITDB_ROOT_USERNAME, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, interval, retries (+27 more)

### Community 8 - "steps"
Cohesion: 0.17
Nodes (13): clean_digits(), validate_cnpj(), validate_cpf(), validate_document(), test_clean_digits(), test_property_clean_digits(), test_validate_cnpj_invalid_digits(), test_validate_cnpj_invalid_repeated_digits() (+5 more)

### Community 9 - "typing"
Cohesion: 0.13
Nodes (5): lifespan(), AuditRepository, InMemoryAuditRepository, MongoAuditRepository, ToolAuditEntry

### Community 10 - "Atendente IA Platform"
Cohesion: 0.20
Nodes (9): test_api_auth_failure_with_wrong_key(), test_api_auth_failure_without_header(), test_api_identificar_cliente_success(), test_api_solicitar_reembolso_sensitive_confirmed_success(), test_api_solicitar_reembolso_sensitive_requires_confirmation(), test_health_check(), test_contract_and_invoices_repository(), test_customer_repository() (+1 more)

### Community 11 - "http_exception_handler"
Cohesion: 0.12
Nodes (16): jobs, quality-and-tests, name, branches, branches, runs-on, steps, name (+8 more)

### Community 12 - "repos"
Cohesion: 0.25
Nodes (8): Servidor MCP Oficial, Roadmap de Fases (0 a 6), Cat?logo de Skills & Fallback, Atendente IA Platform, Jornada B2B, Jornada B2C, A??o Sens?vel (Reembolso), Contrato de Tools API

### Community 14 - "Dom?nio Central (Domain)"
Cohesion: 0.29
Nodes (6): args, id, repos, hooks, repo, rev

### Community 15 - "atendente/__init__.py"
Cohesion: 0.33
Nodes (3): ConversationState Tipado, Motor RAG H?brido, Orquestrador LangGraph

### Community 16 - "Stack Langfuse + Prometheus"
Cohesion: 0.40
Nodes (3): Dom?nio Central (Domain), Adaptador FastAPI, Arquitetura Hexagonal

## Knowledge Gaps
- **41 isolated node(s):** `name`, `branches`, `branches`, `runs-on`, `name` (+36 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 189 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `NovaLojaToolsService` connect `NovaLojaToolsService` to `KBChunk`, `typing`, `src_atendente_infra_db_repositories`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **Are the 22 inferred relationships involving `NovaLojaToolsService` (e.g. with `ContractSLA` and `Customer`) actually correct?**
  _`NovaLojaToolsService` has 22 INFERRED edges - model-reasoned connections that need verification._
- **What connects `name`, `branches`, `branches` to the rest of the system?**
  _41 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `KBChunk` be split into smaller, more focused modules?**
  _Cohesion score 0.05880780539962577 - nodes in this community are weakly interconnected._
- **Why does `AgentNodeHandler` connect `mongodb` to `test_tools.py`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `HybridRetriever` (e.g. with `EmbeddingService` and `KBChunk`) actually correct?**
  _`HybridRetriever` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `NovaLojaToolsService` be split into smaller, more focused modules?**
  _Cohesion score 0.08551278283867177 - nodes in this community are weakly interconnected._