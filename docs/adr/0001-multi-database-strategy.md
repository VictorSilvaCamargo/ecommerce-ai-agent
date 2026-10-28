# ADR-0001: Estratégia de Persistência Poliglota (PostgreSQL, MongoDB e Redis)

## Status
Aceito

## Data
2026-10-25

## Contexto
O sistema **Atendente IA** opera em um cenário de alta confiabilidade corporativa, lidando simultaneamente com:
1. Transações relacionais com integridade referencial estrita (clientes, pedidos, contratos corporativos, faturas e itens);
2. Vetores de alta dimensionalidade para busca semântica em base de conhecimento RAG;
3. Trilhas de auditoria imutáveis e documentos de conversação semiestruturados de tamanho variável (payloads de function calling, feedbacks com polegar, logs de turnos);
4. Estado volátil de alta frequência, cache de tokens/sessão e fila de mensagens assíncronas.

Avaliou-se a possibilidade de concentrar todos os dados em um único banco (ex.: apenas PostgreSQL ou apenas MongoDB) versus adotar persistência poliglota especializada.

## Decisão
Adotamos uma arquitetura de **Persistência Poliglota** com papéis rigorosamente delimitados:

1. **PostgreSQL 16 + pgvector:**
   - **Papel:** Repositório primário para entidades de negócio relacionais (`customers`, `orders`, `b2b_contracts`, `invoices`, `tickets`) e armazenamento de embeddings vetoriais na mesma instância (`kb_chunks` com índice HNSW).
   - **Justificativa:** Garantia de transações ACID e constraints estritas em pedidos e contratos; evita duplicação de infraestrutura mantendo vetor e metadados relacionais no mesmo mecanismo, permitindo consultas combinadas (ex.: filtrar base de conhecimento B2B com joins na tabela de contratos do cliente).
2. **MongoDB:**
   - **Papel:** Trilhas de auditoria das Tools (`tool_audit_logs`), histórico bruto de conversação e eventos de feedback dos usuários (`user_feedback`).
   - **Justificativa:** Payloads de entrada e saída de LLMs e ferramentas variam de esquema dinamicamente e demandam gravação em lote sem bloqueio de tabelas relacionais. A imutabilidade e a flexibilidade de documentos JSON são ideais para auditoria forense e recuperação de traces.
3. **Redis 7:**
   - **Papel:** Broker de mensagens e backend de resultados para o Celery, cache temporário de tokens de autenticação/rate-limit e checkpointing de memória volátil rápida para o LangGraph.
   - **Justificativa:** Baixíssima latência (em memória) para coordenação distribuída, filas idempotentes e expiração automática via TTL.

## Consequências
- **Positivas:**
  - Especialização de motores: integridade relacional no Postgres, escalabilidade de logs/auditoria no Mongo e velocidade no Redis.
  - O Postgres não sofre com bloat decorrente de milhões de logs de auditoria e mensagens temporárias.
  - Simplificação das consultas vetoriais acopladas a metadados relacionais.
- **Negativas / Mitigações:**
  - Necessidade de gerenciar 3 contêineres no Docker Compose.
  - *Mitigação:* Configuração automatizada via `docker-compose.yml`, healthchecks padronizados e scripts de seed integrados (`make seed`).
