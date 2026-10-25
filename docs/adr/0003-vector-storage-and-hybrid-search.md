# ADR-0003: Armazenamento Vetorial e Busca Híbrida com pgvector e BM25

## Status
Aceito

## Data
2026-10-25

## Contexto
O Atendente IA precisa responder dúvidas sobre manuais de produtos, políticas de devolução e prazos de SLA contratuais corporativos. Consultas puramente vetoriais (baseadas em embeddings densos) frequentemente falham ao buscar termos exatos, números de artigos de lei, códigos de produto ou siglas específicas (ex.: "SLA nível 1", "7 dias corridos Art. 49", "SKU-9923"). Por outro lado, buscas puramente lexicais (BM25) não capturam sinonímias conceituais ("quero meu dinheiro de volta" vs "política de estorno").

## Decisão
Implementar **Busca Híbrida** diretamente no PostgreSQL 16 utilizando:
1. **pgvector (HNSW Index):** Para similaridade de cosseno em vetores densos (modelo de embeddings configurável, ex.: `text-embedding-3-small` / modelo local compatível).
2. **PostgreSQL Full-Text Search (`tsvector` + BM25 equivalent):** Para correspondência léxica com dicionário em português (`portuguese`), índices GIN em campos de texto e títulos de seções.
3. **Reciprocal Rank Fusion (RRF) / Pontuação Ponderada:** Combinação dos rankings lexical e vetorial:
   $$\text{Score} = \alpha \cdot \text{Score}_{\text{vetorial}} + (1 - \alpha) \cdot \text{Score}_{\text{lexical}}$$
4. **Filtro Estrito por Segmento (`segment IN ('B2C', 'AMBOS')` ou `'B2B'`):** Isolamento de políticas contratuais sensíveis para que clientes B2C nunca visualizem SLAs corporativos e vice-versa.
5. **Limiar de Relevância e Abstenção:** Se o score combinado máximo estiver abaixo de um limiar $\theta_{\text{min}}$ (ex.: 0.65), o sistema não injeta os documentos no prompt e aciona a mensagem de abstenção padronizada.

## Consequências
- **Positivas:**
  - Alta precisão tanto para jargões corporativos e números de regras quanto para dúvidas expressas em linguagem natural informal;
  - Zero necessidade de ferramentas externas caras como Elasticsearch/Pinecone/Milvus;
  - Governança transacional unificada no PostgreSQL.
- **Negativas / Mitigações:**
  - Tuning necessário dos pesos $\alpha$ e do limiar de abstenção.
  - *Mitigação:* Otimização orientada por testes de retrieval no módulo de Evals (Fase 2 e Fase 5), registrando métricas de Hit Rate@k e MRR.
