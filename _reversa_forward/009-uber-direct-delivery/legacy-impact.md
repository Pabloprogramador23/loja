# Legacy Impact: 009-uber-direct-delivery

> Data: `2026-05-30`
> Identificador: `009-uber-direct-delivery`

---

## Arquivos afetados

| Arquivo afetado | Componente (`_reversa_sdd/`) | Tipo | Severidade | Justificativa |
|-----------------|------------------------------|------|------------|---------------|
| `requirements.txt` | `architecture.md#Stack Tecnológica` | regra-nova | LOW | Nova dependência `httpx` adicionada |
| `store_saas/settings.py` | `architecture.md#Configurações por Ambiente` | regra-nova | LOW | Quatro novas variáveis de ambiente Uber Direct |
| `core/models.py` | `data-dictionary.md` | componente-novo + delta-de-dados | HIGH | Três novos modelos; campo `uber_quote_id` em `Order` |
| `core/migrations/0011_uber_direct.py` | `data-dictionary.md` | delta-de-dados | HIGH | Migration criando todos os novos modelos e campo |
| `core/uber_direct.py` | `architecture.md#Integrações Externas` | componente-novo | HIGH | Novo cliente HTTP para Uber Direct API |
| `core/tasks.py` | `code-analysis.md#Celery` | regra-nova | MEDIUM | Nova task Celery `process_uber_webhook` |
| `core/api.py` | `code-analysis.md#2.6` | contrato-novo | HIGH | Dois novos endpoints FastAPI: `/uber-direct/quote` e `/webhooks/uber-direct` |
| `core/views.py` | `code-analysis.md#2.3` (checkout) + `code-analysis.md#2.7` (manager) | regra-alterada + regra-nova | HIGH | `checkout()` agora consome `uber_quote_id` da sessão; dois novos views de despacho/cancelamento |
| `core/urls.py` | `code-analysis.md#2.7` | regra-nova | LOW | Duas novas rotas de despacho/cancelamento |
| `core/forms.py` | `code-analysis.md#Formulários` | regra-alterada | MEDIUM | `StoreSettingsForm` com 7 novos campos Uber Direct |
| `templates/core/partials/cart_drawer.html` | `code-analysis.md#2.2` (carrinho) | regra-alterada | MEDIUM | Linha de taxa condicionalmente Uber ou estática; trigger HTMX |
| `templates/core/manager/settings.html` | `code-analysis.md#2.7` (dashboard) | regra-alterada | LOW | Nova seção "Uber Direct" no formulário de configurações |
| `templates/core/partials/uber_delivery_status.html` | `code-analysis.md#2.7` | componente-novo | MEDIUM | Novo partial para status/despacho/cancelamento Uber |
| `templates/core/partials/order_modal.html` | `code-analysis.md#2.7` | regra-alterada | MEDIUM | Modal de pedido inclui partial Uber Direct quando ativo |
| `core/tests.py` | — | regra-nova | LOW | Novos testes de modelo Uber Direct |
| `core/tests_uber.py` | — | componente-novo | LOW | Novos testes de helper, webhook e despacho |
| `core/tests_checkout.py` | — | regra-nova | LOW | Três novos testes de integração Uber Direct no checkout |

---

## Diff conceitual por componente

### Checkout (`core/views.py:checkout`)
A lógica de cálculo de `effective_delivery_fee` foi ampliada. Antes: sempre calculava com base em `store.delivery_fee` e `free_delivery_threshold`. Agora: quando `store.uber_config.is_active == True`, lê `uber_quote_data` da sessão (`uber_quote_{store_id}`). Se o quote for válido (não expirado), usa `fee` da cotação. Caso contrário, faz fallback para a lógica da feature 007. O campo `uber_quote_id` agora é persistido no `Order`.

### Integrações externas (`core/uber_direct.py` + `core/api.py`)
Uber Direct adicionada como segunda integração externa. O cliente `UberDirectClient` usa `httpx` assíncrono e cacheia token OAuth2 no Redis. Dois novos endpoints FastAPI: `POST /api/uber-direct/quote` (cotação em tempo real) e `POST /api/webhooks/uber-direct` (webhook com validação HMAC-SHA256).

### Processamento assíncrono (`core/tasks.py`)
Nova task `process_uber_webhook` segue o padrão de `process_new_order`: `select_for_update`, `transaction.atomic`, idempotência, retentativas. Responsável por atualizar `UberDirectDelivery.status` e, quando necessário, `Order.status` (DELIVERING, COMPLETED).

### Modelo de dados
Três novos modelos (`UberDirectConfig`, `UberDirectDelivery`, `UberDirectDeliveryEvent`) e campo `uber_quote_id` em `Order`. Nenhum campo existente foi removido ou renomeado.

---

## Regras preservadas

As seguintes regras 🟢 confirmadas em `_reversa_sdd/domain.md` permanecem inalteradas por esta feature:

- **RN-01** (Isolamento multi-tenant) — `UberDirectConfig` e `UberDirectDelivery` respeitam o padrão de tenant isolation
- **RN-04** (Checkout requer name/phone/address) — validação mantida, lógica de fee expandida após a validação
- **RN-07** (Snapshot de preço no OrderItem) — inalterado
- **RN-08** (Pedido de balcão sem PIX) — balcão explicitamente excluído do fluxo Uber Direct (RN-D05)
- **RN-12** (Acesso dashboard binário) — views Uber usam `user_can_manage_store()`
- **RN-19** (Preferência de tema) — inalterada

---

## Regras modificadas

| Regra original | Modificação | Watch item |
|----------------|-------------|------------|
| Feature 007: `effective_delivery_fee = store.delivery_fee` (ou isenção por threshold) | Quando `uber_config.is_active`, a taxa vem da cotação Uber. O threshold é ignorado. A taxa estática funciona como fallback de erro. | W001 |
| `Order.delivery_fee` = snapshot da taxa estática ou zero | Agora pode ser snapshot de cotação Uber dinâmica | W002 |
| `architecture.md#Integrações Externas`: apenas MercadoPago | Uber Direct adicionada como segunda integração | W003 |
