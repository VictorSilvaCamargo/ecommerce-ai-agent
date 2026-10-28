# Graph Report - atendente-ia  (2026-10-25)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 463 nodes · 1166 edges · 26 communities (14 shown, 12 thin omitted)
- Extraction: 74% EXTRACTED · 26% INFERRED · 0% AMBIGUOUS · INFERRED: 306 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9e1b7e1e`
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
- Stack Langfuse + Prometheus
- atendente-ia

## God Nodes (most connected - your core abstractions)
1. `NovaLojaToolsService` - 62 edges
2. `ToolResult` - 23 edges
3. `Customer` - 20 edges
4. `KBChunk` - 19 edges
5. `HybridRetriever` - 18 edges
6. `Order` - 17 edges
7. `RefundService` - 16 edges
8. `CustomerRepository` - 16 edges
9. `DeterministicEmbeddingService` - 15 edges
10. `CustomerSegment` - 15 edges

## Surprising Connections (you probably didn't know these)
- `client()` --uses--> `InMemoryAuditRepository`  [INFERRED]
  tests/integration/test_api_tools.py → src/atendente/infra/audit.py
- `client()` --uses--> `DatabaseManager`  [INFERRED]
  tests/integration/test_api_tools.py → src/atendente/infra/db/database.py
- `client()` --uses--> `Base`  [INFERRED]
  tests/integration/test_api_tools.py → src/atendente/infra/db/models.py
- `client()` --uses--> `ContractRepository`  [INFERRED]
  tests/integration/test_api_tools.py → src/atendente/infra/db/repositories.py
- `client()` --uses--> `CustomerRepository`  [INFERRED]
  tests/integration/test_api_tools.py → src/atendente/infra/db/repositories.py

## Import Cycles
- None detected.

## Communities (26 total, 12 thin omitted)

### Community 0 - "KBChunk"
Cohesion: 0.06
Nodes (31): chunk_directory(), chunk_markdown_document(), ChunkingConfig, detect_segment_from_path(), estimate_tokens(), DeterministicEmbeddingService, EmbeddingService, IngestionPipeline (+23 more)

### Community 1 - "NovaLojaToolsService"
Cohesion: 0.09
Nodes (40): api_abrir_chamado(), api_buscar_base_conhecimento(), api_consultar_contrato_sla(), api_consultar_fatura(), api_consultar_pedido(), api_identificar_cliente(), api_solicitar_reembolso(), api_transferir_para_humano() (+32 more)

### Community 2 - "Customer"
Cohesion: 0.09
Nodes (31): ContractSLA, ContractTier, Customer, CustomerSegment, InvoiceStatus, Order, OrderItem, OrderStatus (+23 more)

### Community 3 - "src_atendente_infra_db_repositories"
Cohesion: 0.06
Nodes (18): do_run_migrations(), run_async_migrations(), run_migrations_online(), upgrade(), Settings, DatabaseManager, Base, ContractSLAORM (+10 more)

### Community 4 - "mongodb"
Cohesion: 0.07
Nodes (35): MONGO_INITDB_DATABASE, MONGO_INITDB_ROOT_PASSWORD, MONGO_INITDB_ROOT_USERNAME, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, interval, retries (+27 more)

### Community 5 - "pytest"
Cohesion: 0.13
Nodes (14): clean_digits(), validate_cnpj(), validate_cpf(), validate_document(), test_contract_tools_parameters_match_openapi(), test_clean_digits(), test_property_clean_digits(), test_validate_cnpj_invalid_digits() (+6 more)

### Community 6 - "test_tools.py"
Cohesion: 0.17
Nodes (10): client(), test_api_auth_failure_with_wrong_key(), test_api_auth_failure_without_header(), test_api_identificar_cliente_success(), test_api_solicitar_reembolso_sensitive_confirmed_success(), test_api_solicitar_reembolso_sensitive_requires_confirmation(), test_health_check(), test_contract_and_invoices_repository() (+2 more)

### Community 7 - "ToolAuditEntry"
Cohesion: 0.13
Nodes (5): lifespan(), AuditRepository, InMemoryAuditRepository, MongoAuditRepository, ToolAuditEntry

### Community 8 - "steps"
Cohesion: 0.12
Nodes (16): jobs, quality-and-tests, name, branches, branches, runs-on, steps, name (+8 more)

### Community 9 - "typing"
Cohesion: 0.17
Nodes (4): health_check(), list_tool_schemas(), ToolError, get_tool_definitions()

### Community 10 - "Atendente IA Platform"
Cohesion: 0.25
Nodes (8): Servidor MCP Oficial, Roadmap de Fases (0 a 6), Cat?logo de Skills & Fallback, Atendente IA Platform, Jornada B2B, Jornada B2C, A??o Sens?vel (Reembolso), Contrato de Tools API

### Community 12 - "repos"
Cohesion: 0.29
Nodes (6): args, id, repos, hooks, repo, rev

### Community 13 - "Motor RAG H?brido"
Cohesion: 0.33
Nodes (3): ConversationState Tipado, Motor RAG H?brido, Orquestrador LangGraph

### Community 14 - "Dom?nio Central (Domain)"
Cohesion: 0.40
Nodes (3): Dom?nio Central (Domain), Adaptador FastAPI, Arquitetura Hexagonal

## Knowledge Gaps
- **41 isolated node(s):** `args`, `id`, `repo`, `rev`, `atendente-ia` (+36 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 135 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `NovaLojaToolsService` connect `NovaLojaToolsService` to `KBChunk`, `Customer`, `ToolAuditEntry`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Are the 22 inferred relationships involving `NovaLojaToolsService` (e.g. with `ContractSLA` and `Customer`) actually correct?**
  _`NovaLojaToolsService` has 22 INFERRED edges - model-reasoned connections that need verification._
- **What connects `args`, `id`, `repo` to the rest of the system?**
  _41 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `KBChunk` be split into smaller, more focused modules?**
  _Cohesion score 0.05800588078053996 - nodes in this community are weakly interconnected._
- **Should `NovaLojaToolsService` be split into smaller, more focused modules?**
  _Cohesion score 0.0884857460199926 - nodes in this community are weakly interconnected._
- **Should `Customer` be split into smaller, more focused modules?**
  _Cohesion score 0.08602150537634409 - nodes in this community are weakly interconnected._
- **Should `src_atendente_infra_db_repositories` be split into smaller, more focused modules?**
  _Cohesion score 0.06127946127946128 - nodes in this community are weakly interconnected._