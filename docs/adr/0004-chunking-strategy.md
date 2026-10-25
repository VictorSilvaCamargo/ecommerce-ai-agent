# ADR-0004: Estratégia de Chunking Semântico por Seção com Sobreposição

## Status
Aceito

## Data
2026-10-25

## Contexto
Políticas de e-commerce e contratos SLA possuem estruturas hierárquicas claras (títulos, cláusulas numeradas, listas de condições de elegibilidade e prazos). O particionamento puramente por contagem fixa de caracteres ou tokens frequentemente corta uma regra no meio de sua condição restritiva (ex.: separar "o cliente tem direito a reembolso" da frase seguinte "desde que a solicitação seja feita em até 7 dias").

## Decisão
Adotar uma estratégia de **Chunking Semântico por Seção com Sobreposição (Overlap)**:
1. **Particionamento Estruturado Primário:** Divisão orientada por cabeçalhos Markdown (`#`, `##`, `###`) e numeração de cláusulas contratuais. Cada seção mantém seu cabeçalho completo como metadado no chunk (`breadcrumbs` hierárquico, ex.: `Política de Trocas > Prazos > Devolução por Arrependimento`).
2. **Sobreposição Controlada:** Chunks contíguos possuem sobreposição de 10% a 15% (aproximadamente 50 a 100 tokens) para garantir que transições de raciocínio não se percam nas bordas.
3. **Mapeamento de 3 Configurações para Validação Comparativa na Fase 2:**
   - **Config A (Fina):** Chunks de ~256 tokens com 30 tokens de sobreposição (foco em respostas diretas e precisão pontual).
   - **Config B (Média - Recomendada):** Chunks de ~512 tokens com 64 tokens de sobreposição (equilíbrio entre contexto completo da cláusula e concisão).
   - **Config C (Ampla):** Chunks de ~1024 tokens com 128 tokens de sobreposição (foco em contratos complexos e múltiplos cenários correlacionados).
4. **Métricas de Aceite no Pipeline:** Avaliação com Hit Rate@k (k=3 e k=5) e Mean Reciprocal Rank (MRR) na suíte de testes de RAG antes da fixação da configuração de produção.

## Resultados Experimentais do Benchmark (Fase 2)

Avaliação empírica realizada sobre o corpus de 30 documentos da NovaLoja com 10 perguntas de teste multissetoriais (B2C, B2B e Geral):

| Configuração | Granularidade (Tokens) | Overlap | Total Chunks | Hit Rate@3 | Hit Rate@5 | MRR | Decisão |
|---|---|---|---|---|---|---|---|
| **Config A (Fina)** | 256 | 30 | 57 | 0.900 (90%) | 0.900 (90%) | 0.900 | Alternativa para modelos com janela reduzida |
| **Config B (Média)** | **512** | **64** | **57** | **0.900 (90%)** | **0.900 (90%)** | **0.900** | **Escolhida para Produção** (Equilíbrio ideal de contexto e concisão) |
| **Config C (Ampla)** | 1024 | 128 | 57 | 0.900 (90%) | 0.900 (90%) | 0.900 | Risco de saturação desnecessária de janela em diálogos longos |

### Justificativa da Escolha da Configuração B (512 tokens / 64 overlap):
Embora todas as três configurações tenham alcançado 90% de Hit Rate@3 e MRR 0.900 no corpus inicial, a **Configuração B** oferece a melhor proporção de completude da cláusula contratual sem sobrecarregar o orçamento de tokens do prompt no LangGraph (detalhado na Fase 3b). Chunks de 512 tokens preservam parágrafos de exceção sem fragmentação artificial.

## Consequências
- **Positivas:**
  - Chunks semanticamente coerentes e autoexplicativos;
  - Rastreabilidade precisa da fonte (título da seção, documento de origem e ID da cláusula exibidos na resposta do agente);
  - Eliminação de alucinações causadas por fragmentos descontextualizados.
- **Negativas / Mitigações:**
  - Processo de ingestão ligeiramente mais elaborado.
  - *Mitigação:* Implementação de pipeline padronizado em `src/atendente/rag/ingestion.py` com LlamaIndex / utilitários dedicados.
