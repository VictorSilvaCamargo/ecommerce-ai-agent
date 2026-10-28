# Graph Report - atendente-ia  (2026-10-25)

## Corpus Check
- Corpus is ~5,660 words - fits in a single context window. You may not need a graph.

## Summary
- 20 nodes · 16 edges · 5 communities (3 shown, 2 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 1,250 input · 450 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4

## God Nodes (most connected - your core abstractions)
1. `Atendente IA Platform` - 4 edges
2. `Orquestrador LangGraph` - 3 edges
3. `Motor RAG H?brido` - 3 edges
4. `Jornada B2C` - 2 edges
5. `Contrato de Tools API` - 2 edges
6. `Arquitetura Hexagonal` - 2 edges
7. `Dom?nio Central (Domain)` - 2 edges
8. `Adaptador FastAPI` - 2 edges
9. `Roadmap de Fases (0 a 6)` - 2 edges
10. `Jornada B2B` - 1 edges

## Surprising Connections (you probably didn't know these)
- `Roadmap de Fases (0 a 6)` --conceptually_related_to--> `Atendente IA Platform`  [EXTRACTED]
  docs/PLAN.md → docs/SPEC.md
- `Servidor MCP Oficial` --implements--> `Contrato de Tools API`  [EXTRACTED]
  docs/ARCHITECTURE.md → docs/SPEC.md
- `ADR-0001: Persist?ncia Poliglota` --rationale_for--> `Arquitetura Hexagonal`  [EXTRACTED]
  docs/adr/0001-multi-database-strategy.md → docs/ARCHITECTURE.md
- `ADR-0005: Filas Celery, HMAC e Idempot?ncia` --rationale_for--> `Adaptador FastAPI`  [EXTRACTED]
  docs/adr/0005-asynchronous-queue-and-idempotency.md → docs/ARCHITECTURE.md
- `ADR-0002: LangGraph State Machine` --rationale_for--> `Orquestrador LangGraph`  [EXTRACTED]
  docs/adr/0002-orchestration-framework-langgraph.md → docs/ARCHITECTURE.md

## Communities (5 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.33
Nodes (3): ConversationState Tipado, Motor RAG H?brido, Orquestrador LangGraph

### Community 1 - "Community 1"
Cohesion: 0.33
Nodes (6): Servidor MCP Oficial, Roadmap de Fases (0 a 6), Cat?logo de Skills & Fallback, Atendente IA Platform, Jornada B2B, Contrato de Tools API

### Community 2 - "Community 2"
Cohesion: 0.40
Nodes (3): Dom?nio Central (Domain), Adaptador FastAPI, Arquitetura Hexagonal

## Knowledge Gaps
- **6 isolated node(s):** `Jornada B2B`, `A??o Sens?vel (Reembolso)`, `ConversationState Tipado`, `Servidor MCP Oficial`, `Stack Langfuse + Prometheus` (+1 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 11 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Atendente IA Platform` connect `Community 1` to `Community 3`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **What connects `Jornada B2B`, `A??o Sens?vel (Reembolso)`, `ConversationState Tipado` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._