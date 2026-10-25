# ADR-0002: Framework de Orquestração com LangGraph

## Status
Aceito

## Data
2026-10-25

## Contexto
O atendimento inteligente do Atendente IA requer ciclos complexos de diálogo: identificação do cliente, validação de regras de negócio, recuperação de documentos, execução de ferramentas, confirmação em dois passos de ações sensíveis e possibilidade de interrupção com handoff humano. 

Abordagens puramente lineares (como chains simples) ou loops reativos não estruturados (ReAct ingênuo sem controle de estado) geram alucinações de fluxo, perda de controle de variáveis críticas (ex.: se o usuário realmente confirmou o cancelamento de um pedido) e dificuldade de retomada pós-falhas.

## Decisão
Utilizaremos o **LangGraph** como motor de orquestração de máquina de estados conversacional cíclica, com as seguintes diretrizes:

1. **Estado Tipado Estrito (`ConversationState`):** Toda transição entre nós opera sobre um esquema imutável/controlado com tipagem estrita, garantindo previsibilidade.
2. **Nós com Responsabilidade Única:** Cada nó executa exatamente uma função (ex.: `identify_node`, `retrieve_node`, `confirm_action_node`, `respond_node`, `handoff_node`). Regras de transição utilizam arestas condicionais baseadas em valores do estado, e não no texto livre gerado pelo LLM.
3. **Ponto de Confirmação para Ações Sensíveis:** O nó `confirm_action_node` intercepta chamadas sensíveis (ex.: `solicitar_reembolso`) e força um estado de espera até que `state["confirmed"] == True` seja explicitamente sinalizado em um turno subsequente.
4. **Checkpointing e Resumo Incremental:** Checkpointing nativo do LangGraph associado ao Redis, com nó de sumarização acionado automaticamente quando o número de mensagens excede a janela limite, condensando histórico antigo em `state["summary"]` e mantendo fatos essenciais imutáveis.

## Consequências
- **Positivas:**
  - Fluxo conversacional determinístico e auditável;
  - Capacidade de pausar o grafo (*human-in-the-loop*) para handoff ou aprovação externa;
  - Facilidade de teste unitário isolado por nó com injeção de mocks.
- **Negativas / Mitigações:**
  - Curva de aprendizado superior a chains lineares.
  - *Mitigação:* Estrutura de nós padronizada em `src/atendente/agent/nodes/` com contratos claros e tipagem estrita via `mypy --strict`.
