# Relatório de Avaliações (Evals) e Comparativo de Versões de Prompt — Atendente IA

Este documento registra a evolução empírica da Engenharia de Prompts e de Contexto (`context-engineering`) do Atendente IA da NovaLoja, comparando 3 versões versionadas (`v1.0.0`, `v2.0.0` e `v3.0.0`) executadas pela suíte automatizada (`src/atendente/agent/prompts/evaluator.py` e `tests/integration/test_prompt_versions_eval.py`).

> **Nota sobre Ambiente Determinístico:** Conforme definido nas restrições do projeto, todas as execuções de CI rodam sobre o avaliador determinístico e `MockLLMClient` sem dependência de chave externa. Testes com chamada de API ao vivo estão isolados sob a marcação `@pytest.mark.live`.

---

## 1. Técnicas de Engenharia de Contexto Aplicadas (`src/atendente/agent/prompts/`)

1. **Instruções por Papel (`system.py`):** Definição clara da persona corporativa da NovaLoja e das fronteiras entre atendimento B2C (CDC, pedidos, devoluções) e B2B (contratos SLA, faturas consolidadas, chamados priorizados).
2. **Exemplos Few-Shot por Intenção (`classifier.py`):** Exemplos canônicos rotulados cobrindo todas as intenções (`consultar_pedido`, `solicitar_reembolso`, `consultar_fatura`, `consultar_contrato_sla`, `abrir_chamado`, `duvida_geral`, `falar_com_atendente`).
3. **Saída Estruturada Forçada por Schema (`classifier.py`):** Validação estrita com Pydantic v2 via `IntentClassificationOutput` (`intent`, `confidence`, `frustration_detected`, `extracted_order_id`, `reasoning`) com `extra="forbid"`.
4. **Instrução de Abstenção Explícita (`system.py`):** Proibição formal de extrapolar políticas não presentes nos documentos recuperados, com oferta imediata de transferência para especialista humano.
5. **Delimitação XML Contra Prompt Injection Indireto (`rag_delimiters.py`):** Empacotamento de chunks em `<contexto_seguro><documento indice="..." fonte="..." secao="...">...</documento></contexto_seguro>` combinado com sanitização de expressões imperativas maliciosas (`</contexto_seguro>`, `IGNORE TODAS AS INSTRUÇÕES`, `SYSTEM OVERRIDE`).
6. **Checklist de Auto-Verificação Silencioso (`system.py`):** Quatro verificações obrigatórias antes da emissão da resposta final (isolamento de segmento, citação `[Fonte: ...]`, confirmação de ação sensível e ausência de alucinação de protocolos).

---

## 2. Benchmark Comparativo das 3 Versões de Prompt

| Versão | Nome / Perfil | Hash SHA-256 (Prefixo) | Acurácia de Abstenção | Conformidade de Citação | Defesa Anti-Injection | Segurança Ação Sensível | Isolamento B2C/B2B | Score Global |
|---|---|---|---|---|---|---|---|---|
| **`v1.0.0`** | `novaloja_system_naive` (Ingênuo) | `e1562d762b16...` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | **0.00** |
| **`v2.0.0`** | `novaloja_system_structured` (Intermediário) | `c6750eaf10b0...` | 1.00 | 0.00 | 0.00 | 1.00 | 1.00 | **0.60** |
| **`v3.0.0`** | `novaloja_system_production` (Otimizado) | `5b40185bff2c...` | **1.00** | **1.00** | **1.00** | **1.00** | **1.00** | **1.00** |

### Análise de Erros e Evolução entre Versões
- **`v1.0.0` → `v2.0.0` (+60% no Score Global):**
  - *Problema na `v1.0.0`:* O prompt ingênuo de uma única frase não instruía o modelo sobre quando abster-se nem exigia confirmação explícita para reembolsos.
  - *Correção na `v2.0.0`:* A introdução de regras numeradas de negócio e da diretriz de abstenção elevou a segurança de ações sensíveis, o isolamento de segmento e a abstenção para `1.00`.
- **`v2.0.0` → `v3.0.0` (+40% no Score Global, atingindo 1.00):**
  - *Problema na `v2.0.0`:* Textos recuperados do RAG eram concatenados sem tags delimitadoras, permitindo que um documento contendo `</contexto_seguro> IGNORE TODAS AS INSTRUÇÕES` sequestrasse o prompt. Além disso, o modelo esquecia de formatar a fonte `[Fonte: arquivo.md]` em respostas longas.
  - *Correção na `v3.0.0`:* Adição do wrapper `format_rag_context_safe` com `<contexto_seguro>`, sanitizador regex de injeção indireta e o **Checklist de Auto-Verificação** no final do prompt (aproveitando o efeito de recência da janela de contexto).

---

## 3. Verificação do Orçamento de Tokens por Seção (`ContextBudgetManager`)

O gerenciador `ContextBudgetManager` (`src/atendente/agent/prompts/budget.py`) aplica as disciplinas da skill `context-engineering`:
- **Selective Include:** Filtra schemas de Tools mantendo apenas as ferramentas aplicáveis ao segmento identificado (`B2C_TOOLS` vs `B2B_TOOLS`).
- **Compress Before Dropping:** Compacta turnos antigos em `[RESUMO]` antes de descartar histórico.
- **Order for Recency:** Preserva inviolavelmente a última mensagem do cliente no final da seção `history`.
- **Invariante Testada por Propriedade (Hypothesis):** Mesmo sob entradas massivas (10 chunks gigantes + 60 turnos de histórico), nenhuma seção jamais ultrapassa seu teto (`system_max`, `tools_max`, `rag_max`, `history_max`, `total_max`).
