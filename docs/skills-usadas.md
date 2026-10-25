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
