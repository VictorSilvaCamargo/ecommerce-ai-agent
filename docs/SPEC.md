# Especificação Técnica — Sistema Atendente IA (NovaLoja)

## 1. Visão Geral e Objetivos

O **Atendente IA** é uma plataforma agêntica de atendimento inteligente em nível de produção para a empresa fictícia **NovaLoja** (e-commerce e serviços corporativos recorrentes). O sistema foi concebido para atender clientes em dois segmentos distintos:
- **B2C (Consumidor Final):** Status de pedido, solicitação de troca/devolução, segunda via de faturas/boletos, solicitação de reembolso (ação sensível sujeita a confirmação explícita) e esclarecimento de políticas gerais.
- **B2B (Corporativo):** Gestão de contratos e SLA, abertura de chamados priorizados com prazos garantidos, consulta a faturas consolidadas por período e escalonamento para gerentes de conta dedicados.

### Metas Principais
1. **Confiabilidade e Decisão Baseada em Regras:** Lógica de negócio, regras de elegibilidade e autorização residem no código de domínio em Python, e não no prompt do LLM.
2. **Prevenção Ativa de Alucinações e Segurança:** RAG híbrido com pontuação e limiar de relevância; se a informação recuperada for insuficiente, o agente abstém-se e oferece transbordo humano (*human handoff*). Ações sensíveis (como reembolsos) exigem estritamente `confirmado=true` no estado da sessão.
3. **Auditabilidade e Observabilidade Total:** Trilha de auditoria no MongoDB para todas as invocações de Tools; tracing ponta a ponta com Langfuse (latência, custo e tokens); métricas Prometheus e dashboards Grafana versionados.
4. **Resiliência e Desacoplamento:** Webhooks assinados com HMAC processados via fila assíncrona Celery + Redis, com garantia de idempotência e Dead Letter Queue (DLQ).
5. **Arquitetura Hexagonal Rigorosa:** Dependência estrita de fora para dentro, monitorada e validada no pipeline de CI com `import-linter` e `graphify`.

---

## 2. Mapa de Capacidades (Capability Map)

Seguindo o processo de *Spec-Driven Development*, decompomos o sistema em módulos estáveis com dependências unidirecionais:

```
                  ┌────────────────┐
                  │     domain     │
                  └───────┬────────┘
                          │ (usado por)
            ┌─────────────┼──────────────┐
            ▼             ▼              ▼
     ┌───────────┐  ┌───────────┐  ┌───────────┐
     │   tools   │  │    rag    │  │   agent   │
     └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
           │              │              │
           └──────────────┼──────────────┘
                          ▼
                   ┌─────────────┐
                   │  api/infra  │
                   └─────────────┘
```

| Módulo ID | Responsabilidade Primária | Dependências Permitidas | Contratos Import-Linter |
|---|---|---|---|
| `domain` | Entidades, regras de negócio de pedidos, clientes, contratos, faturas, cálculo de SLA e elegibilidade de reembolso. | Nenhuma (puro Python / Pydantic) | `domain` NÃO importa `api`, `infra`, `agent`, `tools`, `rag` |
| `tools` | Contratos de Function Calling e adaptadores REST com Pydantic v2 in/out, auditoria e controle de idempotência. | `domain` | `tools` NÃO importa `api`, `agent` |
| `rag` | Ingestão de documentos da NovaLoja, chunking semântico, embeddings, armazenamento vetorial (pgvector) e busca híbrida (BM25 + vetorial). | `domain` | `rag` NÃO importa `api`, `agent` |
| `agent` | Grafo de conversação LangGraph (`ConversationState`), nós de decisão, sumarização incremental, guardrails e orçamento de contexto. | `domain`, `tools`, `rag` | `agent` NÃO importa `api` |
| `infra` | Adaptadores de persistência (PostgreSQL 16, MongoDB, Redis 7), cliente Celery, orquestração de LLM (`LLMClient`), Langfuse e Prometheus. | `domain` | `infra` implementa portas |
| `api` | Endpoints FastAPI, validação de payload, autenticação (API Key / JWT), verificação HMAC de webhooks, roteamento HTTP e servidor MCP. | `domain`, `tools`, `agent`, `infra`, `rag` | Camada externa de entrada |

---

## 3. Escopo e Limites

### No Escopo
- **Tools Integradas:**
  1. `identificar_cliente` (ambos: validação de CPF/CNPJ com código simulado de 6 dígitos)
  2. `consultar_pedido` (B2C: status, itens, rastreio e prazo)
  3. `solicitar_reembolso` (**B2C Sensível:** exige confirmação explícita, verificação de prazo de 7 dias e política de devolução)
  4. `abrir_chamado` (ambos: tickets com priorização; cálculo automático de SLA no B2B)
  5. `consultar_contrato_sla` (B2B: prazos, escopo e nível de serviço)
  6. `consultar_fatura` (B2B: faturas consolidadas por período com PDF/código de barras simulado)
  7. `buscar_base_conhecimento` (ambos: busca híbrida RAG com metadados e citações)
  8. `transferir_para_humano` (ambos: handoff com resumo estruturado da conversa e motivo)
- **Persistência Poliglota:**
  - PostgreSQL 16 + pgvector para dados relacionais (pedidos, clientes, contratos, faturas) e vetoriais (embeddings da base de conhecimento).
  - MongoDB para mensagens de conversa, trilhas de auditoria das ferramentas e feedbacks dos usuários.
  - Redis 7 para sessões em cache, checkpointing de memória e broker/backend do Celery.
- **Motor Agêntico:** LangGraph com nós explícitos, transições condicionais, memória de longo prazo com sumarização e checkpointing persistente.
- **Observabilidade:** Traces no Langfuse, logs estruturados em JSON (`structlog`) com máscara de PII (CPF, e-mail, telefone) e `/metrics` para Prometheus.
- **Servidor MCP:** Exposição das Tools de atendimento através do SDK oficial Python do Model Context Protocol (MCP).
- **Suíte de Avaliações (Evals):** Mínimo de 80 casos de teste com métricas determinísticas e juiz LLM (*LLM-as-a-judge*) com rubricas versionadas.

### Fora do Escopo
- Interface web/frontend (o sistema é exclusivamente focado em API REST, Webhooks assíncronos e Servidor MCP).
- Gateway de pagamento real ou emissão real de notas fiscais (dados e transações serão mockados deterministicamente).
- Treinamento/fine-tuning de modelos fundacionais (utiliza modelos de mercado via `LLMClient` padronizado).

---

## 4. Suposições Técnicas Registradas

1. **Localização e Idioma:** Todo o diálogo, documentação da base de conhecimento e mensagens ao cliente são em Português do Brasil (pt-BR), em tom cordial, profissional e resolutivo.
2. **Validação de Identidade:** Como não há envio real de SMS/e-mail no ambiente de teste, o método `identificar_cliente` aceita um código simulado previsível em testes ou gerado na sessão.
3. **Modo Determinístico para CI/CD:** Todos os nós e testes que dependem de LLM possuem implementação de mock determinístico injetável via interface `LLMClient`, permitindo execução total e cobertura sem chave de API em ambiente desconectado.
4. **Sem Front-End Web:** Toda validação é conduzida via chamadas de API, endpoints de teste, suíte pytest, Locust para carga e inspeção de traces.

---

## 5. Riscos e Mitigações

| Risco | Impacto | Mitigação Arquitetural |
|---|---|---|
| **Alucinação em Políticas de Reembolso / SLA** | Alto | O LLM é instruído a abster-se quando a similaridade do RAG estiver abaixo do threshold; as regras de elegibilidade residem no serviço de domínio (`RefundService`), e não no prompt. |
| **Execução Acidental de Ação Sensível** | Crítico | O nó de execução de ferramenta verifica compulsoriamente `state.confirmed == True` antes de autorizar `solicitar_reembolso`. Sem confirmação prévia explícita no histórico, a ação é suspensa com pedido de confirmação. |
| **Vazamento de PII em Logs e Traces** | Alto | Implementação de processador central no `structlog` que substitui números de CPF, CNPJ, e-mails e números de cartão por máscaras antes do flush para console e Langfuse. |
| **Prompt Injection Direto ou Indireto (RAG)** | Alto | Delimitação estrita do contexto recuperado com tags XML `<contexto_seguro>`, sanitização de entradas via nó de guardrail e separação entre instruções do sistema e dados não confiáveis. |
| **Estouro de Contexto em Conversas Longas** | Médio | Política híbrida de contexto: janela deslizante dos últimos N turnos + sumarização incremental automática no nó `summarize_history`. Fatos essenciais (cliente, pedido, pendência) são preservados no estado e nunca descartados. |

---

## 6. Comandos e Contratos de Execução

- **Ambiente Virtual & Dependências:** `uv sync` / `uv run ...`
- **Execução da API:** `uv run uvicorn atendente.api.main:app --host 0.0.0.0 --port 8000`
- **Worker Assíncrono:** `uv run celery -A atendente.workers.celery_app worker -l info`
- **Servidor MCP:** `uv run python -m atendente.mcp_server`
- **Testes & Cobertura:** `uv run pytest --cov=src/atendente --cov-report=term-missing`
- **Linting & Formatação:** `uv run ruff check .` e `uv run ruff format --check .`
- **Verificação Estrita de Tipos:** `uv run mypy --strict src`
- **Contratos de Arquitetura:** `uv run lint-imports`
- **Grafo de Conhecimento:** `graphify update .` e `graphify query "<pergunta>"`

---

## 7. Detalhamento da Fase 1: Fundação e API de Tools

### 7.1 Contratos de Dados do Domínio (`src/atendente/domain/models.py`)
- **`Customer`:** `id`, `name`, `doc_type` (`CPF` | `CNPJ`), `doc_number` (validado com dígitos verificadores oficiais), `segment` (`B2C` | `B2B`), `email`, `phone`, `created_at`.
- **`Order`:** `id`, `customer_id`, `items: list[OrderItem]`, `total_cents`, `status` (`PROCESSING`, `SHIPPED`, `DELIVERED`, `CANCELLED`), `delivery_date: Optional[datetime]`, `tracking_code: Optional[str]`.
- **`RefundRequest`:** `id`, `order_id`, `customer_id`, `reason: str`, `amount_cents: int`, `status` (`PENDING`, `APPROVED`, `REJECTED`), `eligible: bool`, `created_at: datetime`.
- **`Ticket`:** `id`, `customer_id`, `title: str`, `description: str`, `priority` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), `sla_hours: int`, `status` (`OPEN`, `IN_PROGRESS`, `RESOLVED`), `created_at: datetime`.
- **`ContractSLA`:** `id`, `customer_id`, `tier` (`GOLD`, `PLATINUM`, `ENTERPRISE`), `response_sla_minutes: int`, `resolution_sla_hours: int`, `account_manager: str`, `active: bool`.
- **`Invoice`:** `id`, `customer_id`, `period: str`, `amount_cents: int`, `status` (`PAID`, `OPEN`, `OVERDUE`), `barcode: str`, `due_date: date`, `pdf_url: str`.

### 7.2 Contratos e Validação das Tools (`src/atendente/tools/`)
Toda Tool retorna a estrutura canônica `ToolResult[T]`:
```python
class ToolError(BaseModel):
    code: str  # ex: "CONFIRMATION_REQUIRED", "ORDER_NOT_FOUND", "INELIGIBLE_REFUND"
    message: str  # Mensagem amigável em pt-BR
    retryable: bool  # Se o cliente ou LLM pode tentar novamente com novos parâmetros
    details: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[ToolError] = None
```

- **Ação Sensível (`solicitar_reembolso`):**
  - Parâmetros: `order_id`, `customer_id`, `motivo`, `confirmado: bool = False`.
  - Se `confirmado == False`: retorna erro estruturado `code="CONFIRMATION_REQUIRED"`, com detalhes do pedido e valor a ser reembolsado para exibição ao usuário antes da confirmação.
  - Regra de Negócio de Devolução: Elegível somente se o status for `DELIVERED` e a data de entrega tiver no máximo 7 dias corridos (Art. 49 CDC).

### 7.3 Isolamento de Camadas (`.importlinter`)
- Contrato 1: `domain` é núcleo puro (`domain` não importa `api`, `infra`, `agent`, `tools`, `rag`).
- Contrato 2: `tools` depende de `domain` e `infra` (repositórios de auditoria), mas não importa `api` nem `agent`.
- Contrato 3: `rag` não importa `api` nem `agent`.

---

## 8. Detalhamento da Fase 2: Pipeline de RAG

### 8.1 Corpus de Conhecimento NovaLoja (`data/kb/`)
- Mínimo de 30 documentos estruturados em Markdown:
  - `data/kb/b2c/` (12 docs: políticas de devolução e arrependimento, trocas, cancelamentos, prazos e rastreio, garantia legal, estorno).
  - `data/kb/b2b/` (12 docs: SLAs contratuais Platinum/Gold/Enterprise, faturamento e NF consolidada, limites de crédito PJ, suporte 24x7, multas por quebra de SLA).
  - `data/kb/geral/` (6 docs: termos de uso, canais de ouvidoria, segurança da informação, LGPD e regras institucionais).

### 8.2 Estratégia de Chunking e Comparação (ADR-0004)
- Particionamento semântico orientado por seções Markdown com cabeçalho completo como breadcrumbs.
- Avaliação de 3 configurações de granularidade:
  - **Config A:** 256 tokens / overlap 30
  - **Config B (Produção):** 512 tokens / overlap 64
  - **Config C:** 1024 tokens / overlap 128
- Métricas obrigatórias avaliadas: **Hit Rate@k** (k=3, k=5) e **Mean Reciprocal Rank (MRR)** sobre dataset de perguntas de teste.

### 8.3 Motor de Busca Híbrida e Anti-Alucinação
- **Combinação Vetorial + BM25:** pgvector (`Vector`) com similaridade de cosseno combinada com busca lexical Full-Text Search via Reciprocal Rank Fusion (RRF).
- **Segregação por Segmento:** Filtro obrigatório de metadados (`segment IN ('B2C', 'GERAL')` ou `'B2B', 'GERAL'`).
- **Abstenção por Relevância:** Se o score do melhor chunk for inferior ao limiar mínimo ($\theta_{\text{min}}$), o retriever retorna vazio, acionando a abstenção estruturada.
- **Rastreabilidade:** Cada chunk recuperado expõe `source_file`, `section`, `title` e `breadcrumbs` para citação na resposta do agente.


