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

## Consequências
- **Positivas:**
  - Chunks semanticamente coerentes e autoexplicativos;
  - Rastreabilidade precisa da fonte (título da seção, documento de origem e ID da cláusula exibidos na resposta do agente);
  - Eliminação de alucinações causadas por fragmentos descontextualizados.
- **Negativas / Mitigações:**
  - Processo de ingestão ligeiramente mais elaborado.
  - *Mitigação:* Implementação de pipeline padronizado em `src/atendente/rag/ingestion.py` com LlamaIndex / utilitários dedicados.
