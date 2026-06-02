# Legacy Impact: Remoção de Integrações Desnecessárias

> Feature: `015-remocao-integracoes`
> Data: `2026-06-01`
> Gerado por: `/reversa-coding`

---

## Arquivos afetados

| Arquivo afetado | Componente (`_reversa_sdd/`) | Tipo | Severidade | Justificativa |
|----------------|------------------------------|------|------------|---------------|
| `core/uber_direct.py` | `code-analysis.md#2.6` | componente-extinto | MEDIUM | Arquivo deletado — cliente HTTP Uber Direct removido inteiramente |
| `core/models.py` | `code-analysis.md#modelos` | componente-extinto | HIGH | 3 modelos removidos (UberDirectConfig, UberDirectDelivery, UberDirectDeliveryEvent); campo `uber_quote_id` removido de Order |
| `core/migrations/0015_remove_uber_direct.py` | `code-analysis.md#modelos` | delta-de-dados | HIGH | Migration de remoção de 3 modelos e 1 campo |
| `core/tasks.py` | `code-analysis.md#2.8` | componente-extinto | MEDIUM | Task `process_uber_webhook` removida |
| `core/api.py` | `code-analysis.md#2.7` | delta-de-contrato-externo | MEDIUM | Endpoints `/uber-direct/quote` e `/webhooks/uber-direct` removidos |
| `core/views.py` | `code-analysis.md#checkout` | regra-alterada | HIGH | Checkout simplificado: sem lógica de quote Uber; views `request_uber_delivery` e `cancel_uber_delivery` extintas |
| `core/forms.py` | `code-analysis.md#forms` | regra-alterada | LOW | 7 campos Uber Direct removidos do StoreSettingsForm |
| `core/urls.py` | `architecture.md#roteamento` | contrato-removido | LOW | Rotas `/dashboard/order/<id>/uber-dispatch/` e `/uber-cancel/` removidas |
| `accounts/backends.py` | `code-analysis.md#3.3` | componente-novo | MEDIUM | EmailAuthBackend criado — formaliza workaround email→username |
| `store_saas/settings.py` | `code-analysis.md#1.2` | regra-alterada | HIGH | allauth, django.contrib.sites removidos; AUTHENTICATION_BACKENDS simplificado; variáveis UBER_* e GOOGLE_* removidas |
| `store_saas/urls.py` | `code-analysis.md#1.3` | contrato-removido | LOW | Rota `/accounts/` (allauth callbacks) removida |
| `accounts/views.py` | `code-analysis.md#3.1` | regra-alterada | MEDIUM | Workaround email→username removido; variável google_enabled removida |
| `templates/accounts/auth_modal.html` | `inventory.md#templates` | regra-alterada | LOW | Aba Google removida; modal simplificado para Entrar/Cadastrar |
| `templates/core/manager/settings.html` | `inventory.md#templates` | componente-extinto | LOW | Seção Uber Direct removida do painel |
| `templates/core/partials/uber_delivery_status.html` | `inventory.md#templates` | componente-extinto | LOW | Template deletado |
| `requirements.txt` | `dependencies.md` | regra-alterada | MEDIUM | `django-allauth[socialaccount]` e `httpx` removidos |

---

## Diff conceitual por componente

### Checkout (`core/views.py`)
Antes: branch duplo — Uber Direct ativo (usa quote da sessão) vs. taxa estática. Após: sempre taxa estática (`delivery_fee` + threshold). O campo `uber_quote_id` deixa de ser gravado em `Order.objects.create()`.

### Autenticação (`accounts/`)
Antes: `allauth.AuthenticationBackend` + workaround manual em `checkout_login_view` (email→username lookup). Após: `EmailAuthBackend(ModelBackend)` encapsula esse comportamento de forma limpa. Login por email/senha continua funcionando.

### Settings
Antes: 8 apps em INSTALLED_APPS (inclui allauth 4x + sites), `AccountMiddleware` no middleware stack, 6 variáveis de ambiente opcionais (UBER_*, GOOGLE_*). Após: 7 apps, sem middleware de terceiros no stack crítico, sem variáveis externas desnecessárias.

### Contratos externos extintos
- `POST /api/uber-direct/quote` — não existe mais
- `POST /api/webhooks/uber-direct` — não existe mais
- `GET /accounts/google/login/` — retorna 404

---

## Preservadas

Regras de domínio do `_reversa_sdd/domain.md` que permanecem intactas:

- **RN-01** (Isolamento de Tenant por ContextVar) — não afetada
- **RN-03** (Auto-atribuição de Tenant em Save) — não afetada
- **RN-04** (Checkout Requer Nome, Telefone e Endereço) — não afetada
- **RN-05** (Pedido de Convidado e Vinculação Pós-Signup) — não afetada
- **RN-06** (Limite de 3 Endereços por Usuário por Loja) — não afetada
- **RN-07** (Snapshot de Preço no OrderItem) — não afetada
- **RN-08** (Pedido de Balcão — Sem PIX, Já em Preparo) — não afetada

MercadoPago Checkout Pro, modo escuro, taxa estática, pagamento na entrega — todos preservados.

---

## Modificadas

- **RN-01 (taxa de entrega):** de dual-mode (Uber Direct/estática) para sempre estática. `Order.uber_quote_id` não é mais gravado.
- **RN-autenticação:** login por email agora via `EmailAuthBackend` em vez de workaround manual + allauth backend.
