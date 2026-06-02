# Roadmap: Checkout Pro MercadoPago (011-B)

> Identificador: `013-checkout-pro-mp`
> Data: `2026-05-30`
> Requirements: `_reversa_forward/013-checkout-pro-mp/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A feature é uma **substituição cirúrgica** do método de pagamento: `payment().create()` → `preference().create()`. O impacto se propaga em três direções:

**Direção 1 — payment.py:** nova função `create_checkout_pro_preference()` que usa a API `preference` do MP SDK. Retorna `init_point` (URL) em vez de QR Code. O mock de dev é adaptado para retornar uma URL local `/payment/mock/`.

**Direção 2 — checkout view + URLs de retorno:** `checkout()` redireciona para `init_point` via `window.location.href`. Três novas views simples (`payment_success_view`, `payment_pending_view`, `payment_failure_view`) recebem o cliente de volta do MP pelos query params. Uma quarta view (`payment_mock_view`) simula aprovação em dev. Novo setting `SITE_URL` define a base das `back_urls`.

**Direção 3 — webhook:** O Checkout Pro pode disparar `payment.created` OU `payment.updated` quando o pagamento é concluído. O webhook atual só trata `payment.updated`. Além disso, o lookup atual é por `mp_payment_id` — mas no Checkout Pro o `mp_payment_id` ainda não está no Order quando o webhook chega (só a `mp_preference_id`). A solução: após chamar `sdk.payment().get(payment_id)`, usar `external_reference` (= `order.id`) do response para encontrar o Order, salvar `mp_payment_id` e chamar `update_paid_order`.

**Modelo de dados:** um único novo campo: `Order.mp_preference_id`.

## 2. Princípios aplicados

Arquivo `principles.md` não encontrado — sem princípios registrados.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|---------------|--------------------------|-------------|
| D-01 | `preference().create()` do MP SDK para Checkout Pro | API oficial; suporta PIX + cartão + débito na mesma tela; sem código de QR no backend | PIX QR Code inline (descartado: suporta só PIX; QR Code base64 grande na sessão) | 🟢 |
| D-02 | `SITE_URL` em settings para montar `back_urls` | `payment.py` não tem acesso ao `request`; URL base precisa de config explícita | Construir URL a partir de `ALLOWED_HOSTS[0]` (frágil, pode ser `*`) | 🟡 |
| D-03 | Lookup do Order no webhook via `external_reference` do payment response | No Checkout Pro, `mp_payment_id` não existe no Order antes do webhook; `external_reference = order.id` é confiável e foi definido na preference | Lookup por `mp_preference_id` (descartado: o payload do webhook contém `payment_id`, não `preference_id`) | 🟡 |
| D-04 | Tratar `payment.created` e `payment.updated` com a mesma lógica no webhook | MP pode enviar qualquer um dos dois dependendo do método de pagamento e timing | Tratar apenas `payment.updated` (descartado: perderia notificações de `created`) | 🟡 |
| D-05 | `create_pix_payment()` mantido no código mas sem chamada ativa | Permite rollback fácil e preserva referências em testes existentes | Deletar (descartado: testes de checkout_ux usam mock desta função) | 🟢 |
| D-06 | Mock dev: `init_point = f'/payment/mock/?order_id={order.id}'` + view local | Permite testar fluxo completo sem conta MP; ativa o mesmo `update_paid_order` do webhook real | Mock retornando URL do MP sandbox (descartado: sandbox MP é instável e lento para dev) | 🟡 |
| D-07 | Views de retorno simples (sem `@login_required`) | MP pode redirecionar antes da sessão ser restaurada; URL pública é mais robusta | `@login_required` nas views de retorno (descartado: pode redirecionar para login quebrando o fluxo) | 🟡 |

## 4. Premissas

Nenhuma — sem marcadores `[DÚVIDA]` no requirements.

## 5. Delta arquitetural

| Componente | Arquivo legado | Tipo | Resumo |
|------------|---------------|------|--------|
| `create_checkout_pro_preference()` | `core/payment.py` | componente-novo | Nova função; `create_pix_payment()` mantida sem chamada ativa |
| `checkout()` | `core/views.py` | regra-alterada | Chama `create_checkout_pro_preference()` em vez de `create_pix_payment()`; redireciona para `init_point` |
| `payment_success_view`, `payment_pending_view`, `payment_failure_view`, `payment_mock_view` | `core/views.py` | componente-novo | Quatro novas views de retorno MP |
| URLs `/payment/success/`, `/payment/pending/`, `/payment/failure/`, `/payment/mock/` | `core/urls.py` | regra-nova | Quatro novas rotas |
| `mercadopago_webhook` | `core/api.py` | regra-alterada | Trata `payment.created` e `payment.updated`; lookup por `external_reference` |
| `Order.mp_preference_id` | `core/models.py` | delta-de-dados | Novo CharField |
| `SITE_URL` | `store_saas/settings.py` | regra-nova | Base URL para `back_urls` da preference |
| Templates de retorno | — (novos) | componente-novo | `payment_success.html`, `payment_pending.html`, `payment_failure.html`, `payment_mock.html` |

## 6. Delta no modelo de dados

- Novo campo `Order.mp_preference_id = CharField(max_length=255, blank=True, default='')`
- Detalhe completo em: `_reversa_forward/013-checkout-pro-mp/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| MercadoPago Preference API | HTTP/REST | `interfaces/mp-preference-api.md` |
| MercadoPago Webhook (atualização) | HTTP callback | `interfaces/mp-webhook.md` |

## 8. Plano de migração

1. Adicionar `Order.mp_preference_id` ao model e gerar migration `0013_order_mp_preference_id`
2. Adicionar `SITE_URL` a `settings.py`, `.env` e `.env.prod`
3. Implementar `create_checkout_pro_preference()` em `core/payment.py`
4. Atualizar `checkout()` em `core/views.py`
5. Adicionar 4 views de retorno em `core/views.py`
6. Adicionar 4 novas URLs em `core/urls.py`
7. Atualizar `mercadopago_webhook` em `core/api.py`
8. Criar 4 templates de retorno
9. Aplicar migration

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| `external_reference` ausente ou incorreto no response do MP → Order não encontrado | Alto | Baixo | Log de warning + retornar 200 (MP não retenta se receber 4xx em todo webhook) |
| `SITE_URL` errado em prod → cliente retorna para URL inválida | Alto | Médio | Validar no startup que `SITE_URL` não é `localhost` quando `DEBUG=False` |
| MP não suporta `back_urls` com `localhost` em produção | Médio | Baixo | Em dev usar `ngrok` ou `SITE_URL=http://localhost:8000`; MP aceita localhost em sandbox |
| `payment.created` chega antes do `mp_payment_id` existir → tentativa de lookup falha | Médio | Baixo | O lookup é feito por `external_reference` (order.id), não por `mp_payment_id`; não há problema |
| Testes existentes que mockam `create_pix_payment` quebram | Baixo | Médio | `create_pix_payment` é mantida; testes apontam para ela ainda; `checkout()` agora chama a nova função — ajustar mocks nos testes de checkout |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Checkout em dev: `TEST-0000` token → redireciona para `/payment/mock/` → aprovar → pedido vira PREPARING
- [ ] Views de retorno funcionam com query params do MP
- [ ] Webhook trata `payment.created` e `payment.updated`
- [ ] Token por tenant preservado na preference
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-30 | Versão inicial gerada por `/reversa-plan` | reversa |
