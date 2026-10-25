# Integra??o T?cnica via API e Webhooks B2B

## 1. Autentica??o e Seguran?a
A integra??o com o gateway NovaLoja exige autentica??o m?tua via tokens de longa dura??o e valida??o de assinatura criptogr?fica HMAC-SHA256 em todos os webhooks disparados.

## 2. Rate Limits e Idempot?ncia
O limite padr?o de requisi??es corporativas ? de 1.000 requisi??es por minuto por chave de API. Todas as opera??es de cria??o de pedidos ou solicita??es de tickets devem incluir o cabe?alho `Idempotency-Key`.