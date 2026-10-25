# Graph Report - atendente-ia  (2026-10-25)

## Corpus Check
- Corpus is ~5,660 words - fits in a single context window. You may not need a graph.

## Summary
- 222 nodes · 510 edges · 20 communities (10 shown, 10 thin omitted)
- Extraction: 80% EXTRACTED · 20% INFERRED · 0% AMBIGUOUS · INFERRED: 103 edges (avg confidence: 0.94)
- Token cost: 1,250 input · 450 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 11

## God Nodes (most connected - your core abstractions)
1. `NovaLojaToolsService` - 42 edges
2. `ToolResult` - 22 edges
3. `CustomerRepository` - 11 edges
4. `Customer` - 10 edges
5. `Order` - 10 edges
6. `RefundRequest` - 10 edges
7. `RefundService` - 10 edges
8. `ToolAuditEntry` - 10 edges
9. `Base` - 10 edges
10. `OrderRepository` - 10 edges

## Surprising Connections (you probably didn't know these)
- `lifespan()` --uses--> `InMemoryAuditRepository`  [INFERRED]
  src/atendente/api/main.py → src/atendente/infra/audit.py
- `lifespan()` --uses--> `MongoAuditRepository`  [INFERRED]
  src/atendente/api/main.py → src/atendente/infra/audit.py
- `get_tools_service()` --uses--> `ContractRepository`  [INFERRED]
  src/atendente/api/main.py → src/atendente/infra/db/repositories.py
- `get_tools_service()` --uses--> `CustomerRepository`  [INFERRED]
  src/atendente/api/main.py → src/atendente/infra/db/repositories.py
- `get_tools_service()` --uses--> `NovaLojaToolsService`  [INFERRED]
  src/atendente/api/main.py → src/atendente/tools/service.py

## Import Cycles
- None detected.

## Communities (20 total, 10 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.16
Nodes (19): api_abrir_chamado(), api_buscar_base_conhecimento(), api_consultar_contrato_sla(), api_consultar_fatura(), api_consultar_pedido(), api_identificar_cliente(), api_solicitar_reembolso(), api_transferir_para_humano() (+11 more)

### Community 1 - "Community 1"
Cohesion: 0.12
Nodes (16): get_tools_service(), Invoice, InvoiceStatus, Order, OrderItem, OrderStatus, RefundRequest, RefundStatus (+8 more)

### Community 2 - "Community 2"
Cohesion: 0.11
Nodes (11): DatabaseManager, Base, ContractSLAORM, CustomerORM, InvoiceORM, OrderItemORM, OrderORM, RefundRequestORM (+3 more)

### Community 3 - "Community 3"
Cohesion: 0.12
Nodes (7): ConfirmationRequiredError, DomainError, IneligibleRefundError, clean_digits(), validate_cnpj(), validate_cpf(), validate_document()

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (7): health_check(), http_exception_handler(), lifespan(), list_tool_schemas(), validation_exception_handler(), Settings, get_tool_definitions()

### Community 5 - "Community 5"
Cohesion: 0.21
Nodes (10): ContractSLA, ContractTier, Customer, CustomerSegment, TicketPriority, TicketStatus, TicketService, DocumentType (+2 more)

### Community 6 - "Community 6"
Cohesion: 0.14
Nodes (3): InMemoryAuditRepository, MongoAuditRepository, ToolAuditEntry

### Community 7 - "Community 7"
Cohesion: 0.25
Nodes (8): Servidor MCP Oficial, Roadmap de Fases (0 a 6), Cat?logo de Skills & Fallback, Atendente IA Platform, Jornada B2B, Jornada B2C, A??o Sens?vel (Reembolso), Contrato de Tools API

### Community 8 - "Community 8"
Cohesion: 0.33
Nodes (3): ConversationState Tipado, Motor RAG H?brido, Orquestrador LangGraph

### Community 9 - "Community 9"
Cohesion: 0.40
Nodes (3): Dom?nio Central (Domain), Adaptador FastAPI, Arquitetura Hexagonal

## Knowledge Gaps
- **6 isolated node(s):** `Jornada B2B`, `A??o Sens?vel (Reembolso)`, `ConversationState Tipado`, `Servidor MCP Oficial`, `Stack Langfuse + Prometheus` (+1 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 68 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `NovaLojaToolsService` connect `Community 0` to `Community 1`, `Community 3`, `Community 5`, `Community 6`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `NovaLojaToolsService` (e.g. with `ContractSLA` and `Customer`) actually correct?**
  _`NovaLojaToolsService` has 21 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Jornada B2B`, `A??o Sens?vel (Reembolso)`, `ConversationState Tipado` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.11693548387096774 - nodes in this community are weakly interconnected._
- **Why does `CustomerRepository` connect `Community 5` to `Community 1`, `Community 2`?**
  _High betweenness centrality (0.002) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `CustomerRepository` (e.g. with `Customer` and `CustomerSegment`) actually correct?**
  _`CustomerRepository` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.10967741935483871 - nodes in this community are weakly interconnected._