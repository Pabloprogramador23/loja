# Regression Watch: Remoção de Integrações Desnecessárias

> Feature: `015-remocao-integracoes`
> Data: `2026-06-01`
> Gerado por: `/reversa-coding`

---

## Watch Items

| ID | Origem | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------|-----------------------------|--------------------|--------------------|
| W001 | `core/views.py` → `checkout()` | Taxa de entrega sempre calculada como `store.delivery_fee` (ou 0 se threshold atingido) — sem leitura de `session['uber_quote_*']` | presença | Re-extração encontrar lógica de session `uber_quote_` ou referência a `UberDirectConfig` no checkout |
| W002 | `core/models.py` → `Order` | Modelo `Order` não possui campo `uber_quote_id` | ausência | Re-extração encontrar campo `uber_quote_id` em `Order` |
| W003 | `store_saas/settings.py` | `INSTALLED_APPS` não inclui `allauth`, `allauth.account`, `allauth.socialaccount`, `django.contrib.sites` | ausência | Re-extração encontrar qualquer entrada allauth ou sites no INSTALLED_APPS |
| W004 | `accounts/backends.py` | `EmailAuthBackend(ModelBackend)` existe e está listado em `AUTHENTICATION_BACKENDS` | presença | Re-extração não encontrar `EmailAuthBackend` em AUTHENTICATION_BACKENDS ou o arquivo não existir |
| W005 | `core/models.py` | Modelos `UberDirectConfig`, `UberDirectDelivery`, `UberDirectDeliveryEvent` não existem | ausência | Re-extração encontrar qualquer um desses modelos definidos |
| W006 | `core/api.py` | Endpoints `/uber-direct/quote` e `/webhooks/uber-direct` não existem | ausência | Re-extração encontrar rotas FastAPI com path `uber-direct` ou `uber_direct` |
| W007 | `requirements.txt` | `django-allauth` e `httpx` não aparecem como dependências | ausência | Re-extração encontrar `allauth` ou `httpx` no requirements.txt |

---

## Observações (sem peso de regressão)

Itens abaixo eram 🟡 INFERIDO ou 🔴 LACUNA na extração original — registrados apenas para contexto:

- O campo `uber_quote_id` em pedidos históricos (antes da migration 0015) perdeu seu valor após o `ALTER TABLE`. Dados históricos com esse campo não são recuperáveis sem backup.
- `django.contrib.sites` pode ser re-adicionado por outros pacotes no futuro — não é sinal de violação por si só.

---

## Histórico de re-extrações

<!-- Preenchido automaticamente pelo /reversa quando uma nova extração reversa for executada após esta feature. -->

---

## Arquivadas

<!-- Watch items resolvidos ou obsoletos em extrações futuras. -->
