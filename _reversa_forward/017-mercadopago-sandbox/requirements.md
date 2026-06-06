# Requirements: Integração Real MercadoPago (Sandbox)

> Identificador: `017-mercadopago-sandbox`
> Data: `2026-06-02`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

---

## 1. Resumo executivo

Substituir o mock de desenvolvimento do MercadoPago (token `TEST-0000…` com QR Code hardcoded) por uma integração funcional com as credenciais reais de **sandbox** do MP, permitindo testar o fluxo completo de pagamento — geração de PIX, aprovação via webhook HMAC e transição de status do pedido — sem processar dinheiro real.

O problema a resolver: atualmente qualquer token começando com `TEST-0000` retorna um QR Code de 1×1 pixel, que não pode ser escaneado nem testado; e o webhook sem `MERCADOPAGO_WEBHOOK_SECRET` configurado rejeita toda notificação real do MP (`401 Webhook secret not configured`).

Impacto direto: Pablo (dono da loja `pizzapablo`) pode testar o checkout completo em sandbox antes de ir para produção.

---

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/adrs/003-pagamento-pix-mercadopago.md` | Token por tenant: `order.store.mercadopago_access_token or settings.MERCADOPAGO_ACCESS_TOKEN`; mock ativa se token `TEST-0000` ou API retorna 403 | 🟢 |
| `_reversa_sdd/domain.md#RN-09` | Prioridade de token: token do Store > token global do settings | 🟢 |
| `_reversa_sdd/domain.md#RN-10` | Condição do mock: `token.startswith("TEST-0000")` OU API retorna HTTP 403 | 🟢 |
| `_reversa_sdd/domain.md#RN-11` | Email do pagador PIX para convidados: placeholder `guest@placeholder.invalid` — MP pode rejeitar em produção | 🔴 |
| `_reversa_sdd/architecture.md#Integrações Externas` | Webhook recebido sem validação de assinatura HMAC era L-04 (já resolvido no código) | 🟢 |
| `core/payment.py:104` | Mock também ativa para HTTP 403 da API — mascara erros de credencial inválida silenciosamente | 🟢 |
| `core/payment.py:93` | `float(order.total_amount)` — conversão de Decimal para float pode causar arredondamento | 🟡 |
| `store_saas/settings.py` | `MERCADOPAGO_ACCESS_TOKEN` via `decouple.config`, default `TEST-000…`; `MERCADOPAGO_WEBHOOK_SECRET` via `config`, default `''` | 🟢 |
| `core/api.py` (webhook) | HMAC já implementado; sem segredo configurado E fora de `REVERSA_TESTING` → 401 | 🟢 |

---

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| **Pablo** (dono da pizzaria) | Confirmar que o QR Code PIX real aparece para o cliente e que o pedido muda de PENDING → PREPARING após pagamento | Faz pedido no sandbox, escaneia QR Code real com app do MP, vê pedido mudar de status no dashboard |
| **Desenvolvedor** (Pablo no papel técnico) | Configurar credenciais sandbox sem risco de cobrar dinheiro real | Define token e webhook secret no `.env` local; webhook chega via túnel (ngrok ou similar) |

---

## 4. Regras de negócio novas ou alteradas

1. **RN-017-01:** O mock automático **não deve ser ativado** quando o token sandbox real do MP for configurado (tokens sandbox reais começam com `TEST-` seguido de UUID real, diferente de `TEST-0000`). Apenas `TEST-0000` e resposta 403 ativam o fallback. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#RN-10`
   - Tipo: confirmação — comportamento já correto no código; o mock *não* ativa para tokens `TEST-<UUID-real>`

2. **RN-017-02:** O email do pagador PIX para pedidos de **convidado** deve ser um endereço válido. O placeholder `guest@placeholder.invalid` deve ser substituído por um email real coletado no checkout ou, como mínimo aceitável em sandbox, por um email de teste configurável via settings. 🔴
   - Origem no legado: `_reversa_sdd/domain.md#RN-11`
   - Tipo: alterada — resolve lacuna L-05 / RN-11

3. **RN-017-03:** O `MERCADOPAGO_WEBHOOK_SECRET` deve estar configurado para que o webhook aceite notificações do MP em sandbox. Sem ele, toda notificação real é rejeitada com 401. 🟢
   - Tipo: nova configuração obrigatória para sandbox funcionar

4. **RN-017-04:** O erro de API do MercadoPago (status ≠ 201) **não deve silenciosamente retornar mock**. Em ambiente com token real configurado, falha da API deve retornar erro claro ao usuário. 🟡
   - Origem no legado: `core/payment.py:104` — o HTTP 403 cai no mock, mascarando credencial inválida
   - Tipo: alterada

---

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Configurar variáveis de ambiente de sandbox (`MERCADOPAGO_ACCESS_TOKEN`, `MERCADOPAGO_WEBHOOK_SECRET`) via arquivo `.env` | Must | `python-decouple` carrega os valores; `settings.MERCADOPAGO_ACCESS_TOKEN` não começa com `TEST-0000` | 🟢 |
| RF-02 | Fluxo PIX sandbox: QR Code real gerado e exibido ao cliente | Must | QR Code renderizado no template é um código PIX escaneável real (não o 1×1 pixel de mock) | 🟢 |
| RF-03 | Fluxo Checkout Pro sandbox: redirect para `sandbox_init_point` do MP | Must | Ao clicar em pagar, usuário é redirecionado para página do MP sandbox (URL `sandbox.mercadopago.com.br`) | 🟢 |
| RF-04 | Webhook sandbox recebe notificação de aprovação e transiciona pedido para PREPARING | Must | Após simular aprovação no painel sandbox do MP, `Order.status` muda de `PENDING` para `PREPARING` | 🟢 |
| RF-05 | Email do pagador PIX para convidado usa email real (não placeholder) | Must | PIX criado para guest usa `customer_email` vindo do formulário de checkout; MP não rejeita o email | 🔴 |
| RF-06 | Erro real da API MP (token inválido, saldo, etc.) exibe mensagem de erro ao usuário em vez de mock silencioso | Should | Quando token sandbox inválido, checkout exibe mensagem de erro clara; não exibe QR Code fictício | 🟡 |
| RF-07 | Documentar no `.env.example` quais variáveis são necessárias para sandbox | Should | Arquivo `.env.example` atualizado com `MERCADOPAGO_ACCESS_TOKEN`, `MERCADOPAGO_WEBHOOK_SECRET` e `SITE_URL` | 🟢 |

---

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Segurança | `MERCADOPAGO_ACCESS_TOKEN` e `MERCADOPAGO_WEBHOOK_SECRET` jamais devem ser comitados no repositório | `.gitignore` já exclui `.env`; deve ser verificado | 🟢 |
| Segurança | Validação HMAC do webhook deve estar ativa em sandbox (não só em produção) | Webhook sem HMAC aceita POST de qualquer origem — risco mesmo em sandbox | 🟢 |
| Confiabilidade | `transaction_amount` enviado ao MP deve usar `Decimal` ou `str`, não `float` | `float(Decimal('0.10'))` pode virar `0.10000000000000001`; MP pode rejeitar | 🟡 |
| Operabilidade | O desenvolvedor precisa de uma forma de receber webhook do MP em localhost (ngrok ou similar) | MP não consegue chamar `localhost`; exige URL pública | 🟢 |
| Rastreabilidade | Log de erro da API MP deve exibir status code e resposta para facilitar debug | Atualmente usa `print()`; deve ir para `logger` | 🟡 |

---

## 7. Critérios de Aceitação

```gherkin
Cenário: Checkout PIX com token sandbox real
  Dado que MERCADOPAGO_ACCESS_TOKEN é um token sandbox real (TEST-<UUID-real>)
  E o usuário está no checkout com itens no carrinho
  Quando o usuário conclui o checkout
  Então um QR Code PIX real é exibido na tela de pagamento
  E Order.mp_payment_id é salvo com o ID real retornado pelo MP
  E Order.status permanece PENDING aguardando aprovação

Cenário: Webhook de aprovação transiciona pedido
  Dado que MERCADOPAGO_WEBHOOK_SECRET está configurado
  E um pedido PENDING existe com mp_payment_id salvo
  Quando o MP envia POST /api/webhooks/mercadopago com action=payment.updated e assinatura HMAC válida
  Então Order.status muda para PREPARING
  E o webhook responde 200

Cenário: Email de convidado no PIX
  Dado que o cliente não está autenticado
  E informou email no formulário de checkout
  Quando o checkout PIX é criado
  Então o campo payer.email enviado ao MP é o email real informado pelo cliente
  E não é guest@placeholder.invalid

Cenário: Token inválido não exibe mock
  Dado que MERCADOPAGO_ACCESS_TOKEN é um token inválido (não começa com TEST-0000)
  Quando o usuário tenta fazer checkout
  Então o sistema exibe mensagem de erro (não o QR Code de 1×1 pixel)
  E não cria pedido com status PENDING sem pagamento real vinculado

Cenário: Webhook sem HMAC configurado rejeitado
  Dado que MERCADOPAGO_WEBHOOK_SECRET está vazio
  E REVERSA_TESTING é false
  Quando qualquer POST chega em /api/webhooks/mercadopago
  Então a resposta é 401
```

---

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 — configurar variáveis de ambiente | Must | Pré-requisito de tudo; sem isso nada funciona |
| RF-02 — QR Code PIX real | Must | Objetivo central do item I-01 |
| RF-03 — Checkout Pro sandbox redirect | Must | Segundo fluxo de pagamento ativo |
| RF-04 — webhook transiciona pedido | Must | Sem isso o pedido trava em PENDING para sempre |
| RF-05 — email de convidado | Must | MP sandbox pode rejeitar o placeholder; bloqueia testes |
| RF-06 — erro visível sem mock silencioso | Should | Melhora a experiência de debug, mas não bloqueia o fluxo principal |
| RF-07 — `.env.example` atualizado | Should | Boa prática de onboarding; não impede o funcionamento |

---

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda. Rode `/reversa-clarify` quando houver `[DÚVIDA]` pendente.

---

## 10. Lacunas

- 🔴 [DÚVIDA] O campo `customer_email` já chega no checkout de convidados (feature 010/012 adicionou email obrigatório no signup, mas não está claro se o email também é coletado em guest checkout sem signup). Verificar `core/views.py:checkout()` e o template do cart drawer.

---

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-02 | Versão inicial gerada por `/reversa-requirements` | reversa |
