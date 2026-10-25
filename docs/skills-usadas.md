# Registro de Skills Usadas e Mapeamento de Fallback

Este documento registra todas as skills disponíveis no ambiente, seus caminhos absolutos para `SKILL.md` (utilizados pelo mecanismo de fallback obrigatório), e o histórico de uso de cada skill ao longo das fases do projeto.

---

## 1. Mapa de Resolução de Skills (`nome-da-skill -> caminho do SKILL.md`)

| Nome da Skill | Caminho do SKILL.md | Status / Disponibilidade |
|---|---|---|
| `api-and-interface-design` | `C:\Users\victo\.gemini\config\skills\api-and-interface-design\SKILL.md` | Disponível |
| `browser-testing-with-devtools` | `C:\Users\victo\.gemini\config\skills\browser-testing-with-devtools\SKILL.md` | Disponível (não aplicável ao projeto) |
| `ci-cd-and-automation` | `C:\Users\victo\.gemini\config\skills\ci-cd-and-automation\SKILL.md` | Disponível |
| `code-review-and-quality` | `C:\Users\victo\.gemini\config\skills\code-review-and-quality\SKILL.md` | Disponível |
| `code-simplification` | `C:\Users\victo\.gemini\config\skills\code-simplification\SKILL.md` | Disponível |
| `constraint-driven-development` | `C:\Users\victo\.gemini\config\skills\constraint-driven-development\SKILL.md` | Disponível |
| `context-engineering` | `C:\Users\victo\.gemini\config\skills\context-engineering\SKILL.md` | Disponível |
| `debugging-and-error-recovery` | `C:\Users\victo\.gemini\config\skills\debugging-and-error-recovery\SKILL.md` | Disponível |
| `deprecation-and-migration` | `C:\Users\victo\.gemini\config\skills\deprecation-and-migration\SKILL.md` | Disponível |
| `documentation-and-adrs` | `C:\Users\victo\.gemini\config\skills\documentation-and-adrs\SKILL.md` | Disponível |
| `doubt-driven-development` | `C:\Users\victo\.gemini\config\skills\doubt-driven-development\SKILL.md` | Disponível |
| `find-skills` | `C:\Users\victo\.gemini\config\skills\find-skills\SKILL.md` | Disponível |
| `frontend-ui-engineering` | `C:\Users\victo\.gemini\config\skills\frontend-ui-engineering\SKILL.md` | Disponível (não aplicável ao projeto) |
| `git-workflow-and-versioning` | `C:\Users\victo\.gemini\config\skills\git-workflow-and-versioning\SKILL.md` | Disponível |
| `graphify` | `C:\Users\victo\.gemini\config\skills\graphify\SKILL.md` | Disponível (CLI + regras + workflow) |
| `idea-refine` | `C:\Users\victo\.gemini\config\skills\idea-refine\SKILL.md` | Disponível (não aplicável ao projeto) |
| `incremental-implementation` | `C:\Users\victo\.gemini\config\skills\incremental-implementation\SKILL.md` | Disponível |
| `interview-me` | `C:\Users\victo\.gemini\config\skills\interview-me\SKILL.md` | Disponível (não aplicável ao projeto) |
| `observability-and-instrumentation` | `C:\Users\victo\.gemini\config\skills\observability-and-instrumentation\SKILL.md` | Disponível |
| `performance-optimization` | `C:\Users\victo\.gemini\config\skills\performance-optimization\SKILL.md` | Disponível |
| `planning-and-task-breakdown` | `C:\Users\victo\.gemini\config\skills\planning-and-task-breakdown\SKILL.md` | Disponível |
| `security-and-hardening` | `C:\Users\victo\.gemini\config\skills\security-and-hardening\SKILL.md` | Disponível |
| `shipping-and-launch` | `C:\Users\victo\.gemini\config\skills\shipping-and-launch\SKILL.md` | Disponível |
| `source-driven-development` | `C:\Users\victo\.gemini\config\skills\source-driven-development\SKILL.md` | Disponível |
| `spec-driven-development` | `C:\Users\victo\.gemini\config\skills\spec-driven-development\SKILL.md` | Disponível |
| `test-driven-development` | `C:\Users\victo\.gemini\config\skills\test-driven-development\SKILL.md` | Disponível |
| `using-agent-skills` | `C:\Users\victo\.gemini\config\skills\using-agent-skills\SKILL.md` | Disponível |

---

## 2. Histórico de Uso por Fase

| Fase | Skill / Ferramenta | Modo de Invocação | Evidência / Notas |
|---|---|---|---|
| **Fase -1** | `graphify` | CLI nativo + Hooks | Executados `graphify antigravity install` e `graphify hook install`. Regras e workflows gravados em `.agent/` e `.agents/`. Hook post-commit disparado com sucesso. |
| **Fase -1** | `spec-driven-development` | Fallback Obrigatório (Leitura Direta de `SKILL.md`) | Arquivo `C:\Users\victo\.gemini\config\skills\spec-driven-development\SKILL.md` lido na íntegra (linhas 1 a 100+). Processo de 4 fases (Scope Check, Specify, Plan, Tasks, Implement) validado para uso na Fase 0. |
| **Fase -1** | `git-workflow-and-versioning` | Fallback / Prática Direta | Repositório inicializado com Conventional Commits (`chore: init repository`, `chore: install graphify rules, workflows and gitattributes`). |
| **Fase 0** | `spec-driven-development` | Fallback Obrigatório (`SKILL.md`) | Elaboração do documento formal `docs/SPEC.md` com Capability Map, escopo, suposições e riscos sem necessidade de entrevista (`interview-me` desativado conforme regras). |
| **Fase 0** | `documentation-and-adrs` | Fallback Obrigatório (`SKILL.md`) | Criação de `docs/ARCHITECTURE.md` com diagramas Mermaid e 5 ADRs fundamentais em `docs/adr/` (ADR-0001 a ADR-0005). |
| **Fase 0** | `planning-and-task-breakdown` | Fallback Obrigatório (`SKILL.md`) | Elaboração do roadmap completo das 7 fases em `docs/PLAN.md` com fatiamento vertical e critérios de saída estritos. |
| **Fase 0** | `graphify` | CLI nativo + Engine Python | Primeiro grafo de conhecimento gerado com 20 nós, 16 arestas e 5 comunidades. Exportados `graph.html`, `graph.json` e `docs/graph/GRAPH_REPORT_fase-0.md`. |
| **Fase 0** | `git-workflow-and-versioning` | Fallback / Prática Direta | Criação da branch `fase-0-descoberta-e-especificacao` e commits convencionais estruturados. |
| **Fase 1** | `api-and-interface-design` | Fallback Obrigatório (`SKILL.md`) | Definição dos contratos canônicos `ToolResult[T]` e `ToolError(code, message, retryable, details)`, schemas OpenAPI e 8 Tools. |
| **Fase 1** | `deprecation-and-migration` | Fallback Obrigatório (`SKILL.md`) | Configuração do Alembic com migração inicial seguindo padrão expand/contract e scripts de seed. |
| **Fase 1** | `test-driven-development` | Fallback Obrigatório (`SKILL.md`) | Ciclo Red-Green com 41 testes unitários, testes de contrato OpenAPI e testes de propriedade via Hypothesis. Cobertura de 88%. |
| **Fase 1** | `incremental-implementation` | Fallback Obrigatório (`SKILL.md`) | Implementação em fatias finas: validadores -> modelos -> DB/Alembic -> audit -> tools -> FastAPI -> contratos. |
| **Fase 1** | `security-and-hardening` | Fallback Obrigatório (`SKILL.md`) | Autenticação via API Key, proteção contra IDOR em pedidos e reembolsos, gatekeeper para ações sensíveis e parameterized queries. |
| **Fase 1** | `graphify` | CLI nativo + Engine Python | Grafo atualizado para 222 nós e 510 arestas. Comprovada ausência de dependência de `domain` para `infra` via `graphify path`. |
| **Fase 1** | `git-workflow-and-versioning` | Fallback / Prática Direta | Branch `fase-1-fundacao-e-tools-api` criada, commits atômicos com Conventional Commits. |
| **Fase 2** | `source-driven-development` | Fallback Obrigatório (`SKILL.md`) | Implementação canônica de chunking com breadcrumbs semânticos, embeddings normalizados L2 e fusão recíproca de ranqueamento (RRF, k=60). |
| **Fase 2** | `documentation-and-adrs` | Fallback Obrigatório (`SKILL.md`) | Atualização do `docs/adr/0004-chunking-strategy.md` com a tabela empírica do benchmark (Hit Rate@3=0.90, MRR=0.90) e decisão final pela Configuração B (512 tokens). |
| **Fase 2** | `test-driven-development` | Fallback Obrigatório (`SKILL.md`) | Ciclo Red-Green para testes de chunker, embeddings determinísticos, retriever híbrido, abstenção e benchmark de avaliação de recuperação com 10 casos reais. |
| **Fase 2** | `incremental-implementation` | Fallback Obrigatório (`SKILL.md`) | Fatiamento fino: criação de 30 documentos KB -> chunker semântico -> embeddings -> store léxico/vetorial -> retriever RRF -> integração na Tool `buscar_base_conhecimento`. |
| **Fase 2** | `graphify` | CLI nativo + AST Python | Grafo atualizado para 463 nós e 1166 arestas. Identificação de `KBChunk` e `HybridRetriever` como novos God Nodes canônicos do sistema RAG. Relatório em `docs/graph/GRAPH_REPORT_fase-2.md`. |
| **Fase 2** | `git-workflow-and-versioning` | Fallback / Prática Direta | Branch `fase-2-pipeline-rag`, commits atômicos com Conventional Commits. |
