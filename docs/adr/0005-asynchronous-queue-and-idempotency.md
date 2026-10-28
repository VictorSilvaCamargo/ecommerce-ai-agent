# ADR-0005: Filas Assíncronas, Verificação HMAC e Idempotência com Celery e Redis

## Status
Aceito

## Data
2026-10-25

## Contexto
O atendimento via mensageria (WhatsApp, Telegram, canais de terceiros e webhooks de sistemas parceiros) exige que a API responda com `202 Accepted` em milissegundos (< 200 ms), desacoplando a ingestão da requisição do processamento conversacional do LLM (que pode levar de 1 a 5 segundos). Além disso, instabilidades de rede e retentativas dos canais externos costumam causar duplicidade de requisições (*webhook replay*), correndo o risco de processar um pedido ou reembolso duas vezes.

## Decisão
Implementar um pipeline assíncrono com **Celery + Redis** e garantias de segurança:
1. **Validação Criptográfica de HMAC (SHA-256):** Webhooks recebidos no endpoint FastAPI devem conter o cabeçalho `X-Hub-Signature-256`. A assinatura é recalculada em tempo constante (`hmac.compare_digest`) contra o segredo compartilhado. Se inválida, rejeição imediata com `401 Unauthorized`.
2. **Chave de Idempotência (`Idempotency-Key` / Message ID):** O payload é verificado contra uma chave atômica no Redis (`SETNX webhook:idempotency:<id> 1 EX 86400`). Se a chave já existir, a mensagem duplicada é descartada ou o resultado prévio é devolvido sem novo disparo de agente.
3. **Fila Celery com Retentativas Exponenciais:** Tarefas assíncronas do Celery configuradas com retentativas e backoff exponencial (`retry_backoff=True`, `max_retries=3`).
4. **Dead Letter Queue (DLQ):** Mensagens que falharem após o esgotamento das retentativas são encaminhadas para uma fila de falhas (`dlq_unhandled_messages`), alertando a equipe e gravando evento de erro no MongoDB para diagnóstico.

## Consequências
- **Positivas:**
  - Resposta imediata ao canal externo, eliminando timeouts de rede;
  - Proteção completa contra ataques de replay e duplicação acidental de transações de clientes;
  - Isolamento de falhas: indisponibilidade transitória do LLM não derruba a recepção de mensagens.
- **Negativas / Mitigações:**
  - Necessidade de gerenciar worker Celery e monitorar filas.
  - *Mitigação:* Monitoramento de fila via métricas Prometheus exportadas e incluídas no dashboard do Grafana.
