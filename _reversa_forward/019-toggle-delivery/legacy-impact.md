# Legacy Impact: 019-toggle-delivery

> Data: `2026-06-04`
> Feature: `019-toggle-delivery`
> Pipeline reversa de referência: `_reversa_sdd/` (re-extração 2026-05-31)

---

## Arquivos afetados

| Arquivo afetado | Componente (`_reversa_sdd/`) | Tipo | Severidade | Justificativa |
|-----------------|------------------------------|------|------------|---------------|
| `core/models.py` | `Store` (`architecture.md#Domínio de Negócio`) | delta-de-dados | LOW | Campo `delivery_enabled BooleanField(default=True)` adicionado |
| `core/migrations/0017_store_delivery_enabled.py` | — | delta-de-dados | LOW | Migration ADD COLUMN não-destrutiva |
| `core/context_processors.py` | Camada de apresentação | regra-nova | LOW | Expõe `delivery_enabled` a todos os templates via context processor `cart()` |
| `core/views.py` — `checkout()` | `core/checkout` (`flowcharts/core-checkout.md`) | regra-nova | MEDIUM | Primeira guarda bloqueia pedidos quando `delivery_enabled=False` |
| `core/views.py` — `toggle_delivery_view` | — | componente-novo | LOW | View POST-only, staff-only, HTMX; flip do campo + log |
| `core/forms.py` — `StoreSettingsForm` | `core/dashboard-manager` | regra-alterada | LOW | Campo `delivery_enabled` exposto no formulário de configurações |
| `core/urls.py` | `store_saas/roteamento-asgi` | contrato-novo | LOW | Rota `POST /dashboard/toggle-delivery/` |
| `templates/core/manager/partials/delivery_toggle.html` | — | componente-novo | LOW | Partial HTMX com botão de toggle e feedback visual |
| `templates/core/manager/dashboard.html` | `core/dashboard-manager` | regra-alterada | LOW | Botão toggle adicionado no topo do dashboard |
| `templates/core/partials/cart_drawer.html` | `core/carrinho` | regra-alterada | LOW | Aviso + botão "Confirmar Pedido" desabilitado quando loja fechada |
| `templates/core/catalog.html` | `core/catalogo` | regra-alterada | LOW | Banner de loja fechada quando `delivery_enabled=False` |
| `templates/core/index.html` | `core/catalogo` | regra-alterada | LOW | Idem |
| `core/tests_toggle_delivery.py` | — | componente-novo | LOW | 10 novos testes cobrindo toggle, bloqueio de checkout e context processor |

---

## Diff conceitual por componente

### `Store` (core/models.py)

Campo `delivery_enabled` adicionado. Semântica distinta de `is_active`: `is_active=False` remove a loja do TenantMiddleware (404); `delivery_enabled=False` mantém a loja visível mas bloqueia novos pedidos. As duas flags coexistem independentemente.

### `views.checkout` (core/views.py)

Nova primeira guarda antes de qualquer leitura de dados ou criação de objeto:
```python
if store and not store.delivery_enabled:
    return _checkout_error(request, cart, 'A loja não está aceitando pedidos no momento.')
```
Proteção server-side — a UI desabilitada é apenas conveniência.

### `context_processors.cart` (core/context_processors.py)

Chave `delivery_enabled` adicionada ao dict. Valor padrão `True` quando `tenant` é `None` (seguro).

---

## Regras preservadas

| Regra | Status |
|-------|--------|
| RN-01: Isolamento de Tenant por ContextVar | ✅ Preservada — `delivery_enabled` lido de `request.tenant`, não de ContextVar diretamente |
| RN-04: Checkout requer nome, telefone e endereço | ✅ Preservada — validações mantidas; a nova guarda é anterior a elas |
| RN-05: Guest order com `session['guest_order_id']` | ✅ Preservada — sessão não é tocada pela nova guarda |
| RN-09: Token MP por tenant | ✅ Preservada — `create_checkout_pro_preference` não alterada |
| RN-12: Acesso ao Dashboard — controle binário | ✅ Preservada — `toggle_delivery_view` usa `user_can_manage_store()` idêntico ao padrão |

---

## Regras modificadas

| Regra | Modificação |
|-------|-------------|
| RN-04 (checkout valida campos) | A guarda de `delivery_enabled` precede a validação de campos. Comportamento observável: loja fechada retorna erro antes de checar nome/telefone/endereço. Semanticamente correto. |
