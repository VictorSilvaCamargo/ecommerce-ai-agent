# Arquitetura do Sistema — Atendente IA

Este documento especifica a topologia, fluxo de dados, padrão de camadas e fronteiras do sistema **Atendente IA**. O design segue estritamente a **Arquitetura Hexagonal (Ports & Adapters)**, garantindo que regras de negócio permaneçam puras, testáveis e independentes de frameworks de orquestração, bancos de dados ou provedores de LLM.

---

## 1. Visão Geral dos Componentes

```mermaid
flowchart TD
    subgraph Canais["Canais de Entrada"]
        WEBHOOK["Webhook Externo (HMAC)"]
        CHAT["API de Chat / REST"]
        MCP_CLIENT["Clientes MCP (Claude Desktop, etc.)"]
    end

    subgraph Entrada["Camada API & Entrada"]
        FASTAPI["FastAPI (Auth, HMAC, Rate Limit, Error Handling)"]
        MCP_SERVER["Servidor MCP (SDK Oficial Python)"]
    end

    subgraph Fila["Processamento Assíncrono"]
        REDIS_QUEUE["Redis 7 (Fila Celery)"]
        WORKER["Worker Celery (Idempotência, Retry, DLQ)"]
    end

    subgraph Orquestracao["Orquestração Agêntica (LangGraph)"]
        GRAPH["Grafo de Conversação (Stateful)"]
        GUARDRAILS["Nó de Guardrails (PII, Injection)"]
        IDENTIFY["Nó de Identificação de Cliente"]
        CLASSIFY["Nó de Classificação de Intenção"]
        RETRIEVE["Nó de Recuperação RAG"]
        DECIDE["Nó de Decisão / Function Calling"]
        CONFIRM["Nó de Confirmação de Ações Sensíveis"]
        RESPOND["Nó de Geração de Resposta"]
        HANDOFF["Nó de Avaliação de Handoff"]
    end

    subgraph Dominio["Domínio & Tools"]
        TOOLS["Tools com Validação Pydantic v2"]
        SERVICES["Serviços de Domínio (Pedidos, Reembolsos, Chamados)"]
    end

    subgraph RAG_Engine["Motor de RAG"]
        INGEST["Ingestor Semântico de Documentos"]
        SEARCH["Busca Híbrida (BM25 tsvector + Embeddings)"]
    end

    subgraph Persistencia["Camada de Persistência Poliglota"]
        POSTGRES[("PostgreSQL 16 + pgvector (Relacional + Embeddings)")]
        MONGO[("MongoDB (Auditoria de Tools, Sessões, Feedbacks)")]
        REDIS[("Redis 7 (Cache, Checkpoint de Memória)")]
    end

    subgraph Observabilidade["Observabilidade & Telemetria"]
        LANGFUSE["Langfuse (Tracing, Custo, Tokens, Evals)"]
        PROMETHEUS["Prometheus (/metrics)"]
        GRAFANA["Grafana (Dashboards Versionados)"]
        STRUCTLOG["Logs Estruturados JSON (Máscara PII)"]
    end

    Canais --> Entrada
    FASTAPI --> REDIS_QUEUE
    REDIS_QUEUE --> WORKER
    WORKER --> GRAPH
    FASTAPI --> GRAPH
    MCP_CLIENT --> MCP_SERVER
    MCP_SERVER --> TOOLS

    GRAPH --> GUARDRAILS --> IDENTIFY --> CLASSIFY --> RETRIEVE --> DECIDE --> CONFIRM --> RESPOND --> HANDOFF
    DECIDE --> TOOLS
    TOOLS --> SERVICES
    RETRIEVE --> SEARCH

    SERVICES --> POSTGRES
    SERVICES --> MONGO
    SEARCH --> POSTGRES
    GRAPH --> REDIS

    GRAPH -.-> LANGFUSE
    FASTAPI -.-> PROMETHEUS
    SERVICES -.-> STRUCTLOG
    PROMETHEUS --> GRAFANA
```

---

## 2. Fluxo de Conversação no LangGraph

O grafo de atendimento implementa uma máquina de estados com transições condicionais bem definidas. As ações sensíveis (como `solicitar_reembolso`) nunca são executadas sem a presença explícita de aprovação no estado.

```mermaid
stateDiagram-v2
    [*] --> GuardrailCheck: Mensagem recebida
    GuardrailCheck --> AbortMalicious: Injeção ou Violação Crítica detectada
    GuardrailCheck --> IdentifyCustomer: Entrada Sanitizada

    IdentifyCustomer --> ClassifyIntent: Cliente já autenticado ou identificado
    IdentifyCustomer --> RequestAuth: Documento / Código pendente

    ClassifyIntent --> RetrieveKnowledge: Dúvida de política, manual, SLA, FAQ
    ClassifyIntent --> DecideAction: Consulta de pedido, fatura, chamado

    RetrieveKnowledge --> EvaluateRelevance: Chunks recuperados
    EvaluateRelevance --> DecideAction: Score >= Threshold
    EvaluateRelevance --> AbstainOrHandoff: Score < Threshold

    DecideAction --> ValidateToolCall: Tool acionada
    DecideAction --> FormatResponse: Resposta direta

    ValidateToolCall --> CheckSensitivity: Tool válida
    ValidateToolCall --> HandleToolError: Argumentos inválidos

    CheckSensitivity --> ExecuteTool: Ação comum (leitura/consulta)
    CheckSensitivity --> RequireConfirmation: Ação sensível (reembolso)

    RequireConfirmation --> AskUserConfirmation: confirmed == False
    RequireConfirmation --> ExecuteTool: confirmed == True

    ExecuteTool --> AuditAndFormat: Sucesso
    ExecuteTool --> HandleToolError: Falha na execução

    HandleToolError --> EvaluateHandoff: Tentativas excedidas (>=2)
    HandleToolError --> FormatResponse: Recuperável

    AuditAndFormat --> FormatResponse
    AskUserConfirmation --> FormatResponse
    AbstainOrHandoff --> FormatResponse

    FormatResponse --> EvaluateHandoff
    EvaluateHandoff --> HumanHandoff: Pedido expresso, falhas repetidas ou baixa confiança
    EvaluateHandoff --> SaveCheckpoint: Continuidade normal

    SaveCheckpoint --> [*]
    HumanHandoff --> [*]
    AbortMalicious --> [*]
```

---

## 3. Estado Central da Sessão (`ConversationState`)

O estado da conversação é tipado via `TypedDict` / Pydantic com esquema estrito:

| Campo | Tipo | Descrição |
|---|---|---|
| `customer` | `Optional[Customer]` | Dados cadastrais e segmento (`B2C` ou `B2B`) |
| `segment` | `Literal["B2C", "B2B", "UNKNOWN"]` | Segmento operacional ativo |
| `authenticated` | `bool` | Status de validação de CPF/CNPJ e código |
| `intent` | `str` | Intenção classificada (ex.: `order_tracking`, `refund`, `sla_query`) |
| `messages` | `list[BaseMessage]` | Histórico recente de mensagens (janela deslizante) |
| `summary` | `str` | Resumo incremental condensado de turnos antigos |
| `retrieved_docs` | `list[RetrievedDocument]` | Chunks retornados pelo motor RAG com score |
| `pending_action` | `Optional[SensitiveAction]` | Detalhes da ação sensível aguardando confirmação |
| `confirmed` | `bool` | Flag explícita indicando aprovação do cliente |
| `tool_errors` | `int` | Contador de falhas consecutivas de execução de Tools |
| `handoff_reason` | `Optional[str]` | Motivo detalhado caso o handoff seja acionado |
| `turn_count` | `int` | Total de turnos executados na conversa |

---

## 4. Contratos de Isolamento entre Camadas (Arquitetura Hexagonal)

A separação de preocupações é imposta programaticamente via `.importlinter`:

1. **`domain` (Núcleo):** Não conhece banco de dados, bibliotecas de LLM, FastAPI nem frameworks. Contém entidades puras e validações.
2. **`tools` (Contratos de Ação):** Conhece apenas `domain` para executar regras e retornar estruturas de dados padronizadas.
3. **`rag` (Motor de Busca):** Conhece `domain` e adaptadores de vetor/embeddings. Não depende de `api` nem de `agent`.
4. **`agent` (Orquestrador):** Orquestra chamadas entre `domain`, `tools` e `rag` através de nós do LangGraph. Não conhece endpoints HTTP.
5. **`infra` (Persistência & Clientes):** Implementa interfaces de banco (PostgreSQL, MongoDB, Redis) e provedores de LLM.
6. **`api` & `mcp_server` (Adaptadores de Entrada):** Recebem requisições externas, autenticam, despacham para a fila ou grafo e devolvem respostas formatadas.
