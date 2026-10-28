# Changelog do Catálogo de Prompts — Atendente IA (NovaLoja)

Este documento registra todas as versões do catálogo de prompts da NovaLoja, suas motivações de engenharia de contexto e os hashes SHA-256 imutáveis anexados aos traces de observabilidade (Langfuse).

---

## `[v3.0.0]` — 2026-10-25 (Produção Atual)
- **System Prompt (`novaloja_system_production`):**
  - **SHA-256:** `5b40185bff2c8fc9431efd9d61ea8092c75c53c95f2134e32e626d19c7439e42`
  - **Técnicas Aplicadas:**
    1. **Instrução por Papel (Role Prompting):** Especialista Oficial NovaLoja com separação estrita B2C/B2B.
    2. **Delimitação XML Contra Prompt Injection Indireto:** Isolamento obrigatório de chunks em `<contexto_seguro>...</contexto_seguro>` tratados como dados passivos.
    3. **Política Estrita de Abstenção e Citação:** Formato obrigatório `[Fonte: arquivo.md]` e recusa transparente quando o contexto é insuficiente.
    4. **Gate de Ações Sensíveis:** Proibição explícita de reembolso ou chamado crítico sem confirmação.
    5. **Checklist de Auto-Verificação:** 4 itens verificados silenciosamente antes da síntese final.
- **Classifier Prompt (`novaloja_intent_classifier_few_shot`):**
  - **SHA-256:** `dbd36f0b8b55217aeed33d9ac7680ebc38ba0a0a0216ede30158a2d3d59d1bd5`
  - **Técnicas Aplicadas:** Exemplos *Few-Shot* cobrindo todas as intenções B2C, B2B e pedidos de transbordo humano, com saída estruturada forçada pelo schema Pydantic `IntentClassificationOutput`.

---

## `[v2.0.0]` — 2026-10-25 (Iteração Estruturada Intermediária)
- **System Prompt (`novaloja_system_structured`):**
  - **SHA-256:** `c6750eaf10b0e5793f98a3313afd6ff2330446f09dcdc312c148d345ee3165dc`
  - **Mudanças:** Adição de definição de papel, distinção básica B2C/B2B e regra de abstenção textual.
  - **Limitações Observadas nos Evals:** Sem tags XML `<contexto_seguro>` e sem checklist de auto-verificação, ainda apresentava vulnerabilidade a *indirect prompt injection* em textos do RAG e omissão ocasional de citações `[Fonte: ...]`.

---

## `[v1.0.0]` — 2026-10-25 (Baseline Ingênuo)
- **System Prompt (`novaloja_system_naive`):**
  - **SHA-256:** `e1562d762b16a482920ab0d45dbdba5be8327bed4e2b1695a9532e96ad1fed8d`
  - **Mudanças:** Prompt inicial de uma única sentença sem instruções de abstenção, sem citação de fontes e sem proteção contra injeção ou ações sensíveis.
