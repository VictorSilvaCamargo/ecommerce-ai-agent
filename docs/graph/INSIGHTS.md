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
