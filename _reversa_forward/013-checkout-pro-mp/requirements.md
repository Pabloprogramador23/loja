# Requirements: Checkout Pro MercadoPago (011-B)

> Identificador: `013-checkout-pro-mp`
> Data: `2026-05-30`
> Spec-mãe: `_reversa_forward/011-fluxo-cliente-redesign/requirements.md`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

O sistema atual gera um QR Code PIX via `create_pix_payment()` e exibe inline na tela. Esta feature substitui esse fluxo pelo **Checkout Pro** do MercadoPago: o backend FastAPI cria uma `preference` de pagamento e retorna o `init_point` (URL hospedada pelo MP). O browser redireciona para essa URL, onde o cliente paga via PIX, cartão de crédito ou débito na página do próprio MP. Após o pagamento, o MP redireciona de volta ao app pelas URLs de retorno configuradas (`success`, `pending`, `failure`). O webhook FastAPI existente — já com HMAC e lookup por tenant (feature 009 e melhorias posteriores) — é adaptado para tratar o evento `payment.updated` do Checkout Pro, mantendo a lógica de transição para `PREPARING`. O email do pagador agora sempre vem de `order.user.email` (guest checkout eliminado na feature 012).

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/domain.md#RN-09` | Token MP por tenant: `order.store.mercadopago_access_token` com fallback global — **deve ser preservado** | 🟢 |
| `_reversa_sdd/domain.md#RN-10` | Mock automático quando token começa com `TEST-0000` ou MP retorna 403 — **deve ser preservado** | 🟢 |
| `_reversa_sdd/domain.md#RN-14` | Webhook recebe `payment.updated`, busca pagamento no MP, chama `update_paid_order` → `PREPARING` | 🟡 |
| `_reversa_sdd/code-analysis.md#2.4` | `create_pix_payment()` em `core/payment.py`: cria payment com `payment_method_id: "pix"` e retorna QR Code | 🟢 |
| `_reversa_sdd/code-analysis.md#Webhook` | Webhook atual valida HMAC e usa token do tenant para buscar o payment — **arquitetura boa, reutilizar** | 🟢 |
| `_reversa_sdd/code-analysis.md#2.3` | `checkout()` em `core/views.py` chama `create_pix_payment()` e redireciona para `payment_pix.html` | 🟢 |
| `_reversa_forward/012-auth-social-checkout` | Guest checkout eliminado: todo `order.user` é autenticado; `order.user.email` sempre disponível | 🟢 |
| `_reversa_sdd/domain.md#RN-11` | Email do pagador era lacuna crítica (placeholder hardcoded para guest) — **resolvido pela feature 012** | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Cliente autenticado | Pagar com cartão de crédito | Checkout → redirecionado para MP → paga com cartão → volta para tela de confirmação |
| Cliente autenticado | Pagar com PIX | Checkout → redirecionado para MP → escaneia QR Code na página do MP → volta para confirmação |
| Cliente autenticado | Pagamento pendente | Checkout → MP → sai sem pagar → volta pela URL pending → vê tela de aguardando |
| Cliente autenticado | Pagamento falhou | Checkout → MP → cartão recusado → volta pela URL failure → vê opção de tentar novamente |
| Restaurante (manager) | Receber pedido após pagamento | Webhook MP notifica → pedido transita para PREPARING → aparece no painel |

## 4. Regras de negócio novas ou alteradas

1. **RN-30:** Substituir `create_pix_payment()` por `create_checkout_pro_preference()` em `core/payment.py`. A nova função cria uma `preference` MP com `items`, `payer`, `back_urls` e `auto_return`, e retorna o `init_point`. 🟡
   - Origem: substitui `_reversa_sdd/domain.md#RN-10` (PIX inline) — mantém o fallback mock para dev
   - Tipo: alterada

2. **RN-31:** A `preference` MP inclui `back_urls` com três URLs do app: `success=/payment/success/`, `pending=/payment/pending/`, `failure=/payment/failure/`. O campo `auto_return = 'approved'` faz o MP redirecionar automaticamente para `success` após aprovação. 🟡
   - Tipo: nova

3. **RN-32:** Ao criar a `preference`, o `Order` é salvo com status `PENDING` e `mp_preference_id` (novo campo). O `mp_payment_id` continua sendo preenchido pelo webhook quando o pagamento for aprovado. 🟡
   - Tipo: nova (novo campo no model `Order`)

4. **RN-33:** O `checkout()` em `core/views.py` chama `create_checkout_pro_preference()`, recebe o `init_point` e redireciona o browser para essa URL via `window.location.href`. O `payment_pix.html` é aposentado — as telas de retorno são novas views simples. 🟡
   - Origem: substitui o render de `payment_pix.html`
   - Tipo: alterada

5. **RN-34:** Três novas views Django para as URLs de retorno do MP: `payment_success_view`, `payment_pending_view`, `payment_failure_view`. Essas views leem `payment_id` e `preference_id` dos query params retornados pelo MP e exibem o status correspondente. 🟡
   - Tipo: nova

6. **RN-35:** O webhook `/api/webhooks/mercadopago` mantém a lógica existente (HMAC, lookup por `mp_payment_id`, token por tenant). Adaptação necessária: o Checkout Pro usa `action=payment.created` além de `payment.updated`. Ambos devem ser tratados. 🟡
   - Origem: `_reversa_sdd/domain.md#RN-14` (mantido)
   - Tipo: alterada (ampliar actions tratados)

7. **RN-36:** O email do pagador na `preference` usa sempre `order.user.email` — sem placeholder, sem condicional guest. 🟢
   - Origem: corrige `_reversa_sdd/domain.md#RN-11` (lacuna resolvida pela feature 012)
   - Tipo: alterada

8. **RN-37:** O mock de desenvolvimento é preservado: se token começa com `TEST-0000`, retornar `init_point` fake apontando para `/payment/mock/?order_id={id}` — uma view local que simula a aprovação para testes sem conta MP real. 🟡
   - Origem: `_reversa_sdd/domain.md#RN-10`
   - Tipo: alterada (mock adaptado para Checkout Pro)

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | `create_checkout_pro_preference()` em `core/payment.py`: cria preference com items, payer (email do user), back_urls, auto_return e external_reference (order.id); retorna `init_point` | Must | Preference criada na API MP; `init_point` é URL válida; `mp_preference_id` salvo no Order | 🟡 |
| RF-02 | `checkout()` view: após criar a preference, retornar `<script>window.location.href="{init_point}";</script>` | Must | Browser navega para a URL do MP após finalizar o pedido | 🟡 |
| RF-03 | `Order` model: novo campo `mp_preference_id CharField(max_length=255, blank=True)` | Must | Migration criada; campo salvo ao criar preference | 🟢 |
| RF-04 | View `payment_success_view` em `/payment/success/`: lê query params `payment_id`, `preference_id`, `status` do MP; exibe confirmação de pedido | Must | Cliente retornado pelo MP vê tela de sucesso; Order.id visível | 🟡 |
| RF-05 | View `payment_pending_view` em `/payment/pending/`: exibe mensagem de aguardando processamento com instrução para verificar e-mail | Must | Cliente que saiu sem pagar vê tela de pendente | 🟡 |
| RF-06 | View `payment_failure_view` em `/payment/failure/`: exibe erro e botão para voltar ao carrinho e tentar novamente | Must | Cliente com pagamento recusado vê opção de retry | 🟡 |
| RF-07 | Webhook: tratar `action=payment.created` além de `payment.updated` — ambos devem disparar a verificação de status no MP | Must | Pedido transita para PREPARING tanto por `created` quanto por `updated` quando status MP for `approved` | 🟡 |
| RF-08 | Mock dev: token `TEST-0000` → preference fake com `init_point=/payment/mock/?order_id={id}`; view `payment_mock_view` que simula aprovação e dispara a mesma lógica do webhook | Should | Dev sem conta MP real consegue testar o fluxo completo | 🟡 |
| RF-09 | Preservar token por tenant: `preference` criada com o token da `Store` atual, com fallback para settings | Must | Loja com token próprio usa o seu; loja sem token usa o global | 🟢 |
| RF-10 | `payment_pix.html` aposentado: referências à view `payment_view` atualizadas ou removidas | Must | Nenhuma rota leva para `payment_pix.html`; a view `/payment/<id>/` pode ser mantida para acesso histórico via session | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Segurança | HMAC do webhook preservado — `MERCADOPAGO_WEBHOOK_SECRET` continua obrigatório | `_reversa_sdd/code-analysis.md#L-04` já corrigido; não regredir | 🟢 |
| Segurança | `back_urls` hardcoded no código ou em settings — nunca vir de input do usuário | Risco de open redirect se URL for dinâmica | 🟢 |
| Multi-tenant | `preference.external_reference = str(order.id)` permite ao webhook encontrar o Order sem depender de tenant no payload | `_reversa_sdd/domain.md#RN-09` | 🟢 |
| Sem regressão | Webhook existente e suas lógicas de HMAC e tenant-aware token não devem ser alterados além do tratamento de `payment.created` | `_reversa_sdd/code-analysis.md#Webhook` | 🟢 |
| UX | `auto_return = 'approved'` garante que o MP redireciona automaticamente ao sucesso — sem ação extra do cliente | Padrão Checkout Pro MP | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Cliente finaliza pedido e é redirecionado para o MP
  Dado que o usuário está autenticado e tem itens no carrinho
  Quando clica em "Finalizar Pedido" e confirma o checkout
  Então o backend cria uma preference MP com o email do usuário
  E o browser navega para o init_point (URL do MercadoPago)
  E o Order tem mp_preference_id preenchido

Cenário: Pagamento aprovado — retorno via back_url success
  Dado que o cliente pagou com sucesso no MP
  Quando o MP redireciona para /payment/success/?payment_id=...
  Então o cliente vê tela de confirmação com número do pedido

Cenário: Pagamento aprovado — webhook atualiza o pedido
  Dado que o MP enviou webhook com action=payment.updated e status=approved
  Quando o webhook é recebido e HMAC validado
  Então Order.status transita para PREPARING
  E process_new_order.delay() é disparado

Cenário: Pagamento pendente — retorno via back_url pending
  Dado que o cliente fechou o MP sem pagar
  Quando o MP redireciona para /payment/pending/
  Então o cliente vê instrução de aguardar processamento
  E o Order permanece em PENDING

Cenário: Pagamento falhou — retorno via back_url failure
  Dado que o cartão foi recusado
  Quando o MP redireciona para /payment/failure/
  Então o cliente vê erro e botão "Tentar novamente" que volta ao carrinho

Cenário: Mock de desenvolvimento
  Dado que o token MP começa com TEST-0000
  Quando o checkout é realizado
  Então o init_point aponta para /payment/mock/?order_id=N (local)
  E o cliente pode aprovar o pedido manualmente pela view mock

Cenário: Token por tenant preservado
  Dado que a Store tem mercadopago_access_token próprio
  Quando a preference é criada
  Então o SDK é inicializado com o token da Store (não o global)
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 — create_checkout_pro_preference | Must | Core da feature |
| RF-02 — Redirect para init_point no checkout | Must | Sem isso o cliente não chega ao MP |
| RF-03 — Campo mp_preference_id no Order | Must | Rastreabilidade da preference |
| RF-04/05/06 — Views de retorno (success/pending/failure) | Must | Sem elas o MP não tem para onde redirecionar |
| RF-07 — Webhook: tratar payment.created | Must | MP pode enviar created antes de updated |
| RF-09 — Token por tenant | Must | Preservar RN-09; SaaS multi-tenant |
| RF-10 — Aposentar payment_pix.html | Must | Limpeza necessária; evita rota morta |
| RF-08 — Mock dev | Should | Conveniência de desenvolvimento; não bloqueia prod |

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda.

## 10. Lacunas

Nenhuma lacuna pendente.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-30 | Versão inicial gerada por `/reversa-requirements` | reversa |
