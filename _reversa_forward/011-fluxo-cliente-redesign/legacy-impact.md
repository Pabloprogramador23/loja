# Legacy Impact: 011-fluxo-cliente-redesign (011-D)

> Data: 2026-05-31
> Feature: Localização Pré-Catálogo (RF-01)

## Arquivos modificados

| Arquivo afetado | Componente (`_reversa_sdd/`) | Tipo | Severidade | Justificativa |
|-----------------|------------------------------|------|------------|---------------|
| `core/views.py` — `save_location()` | `architecture.md#Frontend` | componente-novo | LOW | Nova view POST que grava endereço na sessão Django |
| `core/views.py` — `catalog()` | `architecture.md#Frontend` | regra-alterada | LOW | Passa `session_delivery_address` ao contexto do template |
| `core/views.py` — `cart_detail()` | `architecture.md#Frontend` | regra-alterada | LOW | Passa `session_delivery_address` ao contexto do `cart_drawer.html` |
| `core/urls.py` | `architecture.md#Frontend` | componente-novo | LOW | Nova rota `save-location/` |
| `templates/core/catalog.html` | `architecture.md#Frontend` | regra-nova | LOW | Banner de localização não-bloqueante exibido para clientes sem endereço na sessão |
| `templates/core/partials/cart_drawer.html` | `architecture.md#Frontend` | regra-alterada | LOW | Campo `delivery_address` pré-preenchido de `session_delivery_address` quando POST não tem valor |

## Arquivos criados

| Arquivo | Tipo |
|---------|------|
| `core/tests_location.py` | componente-novo |

## Diff conceitual por componente

### save_location() (core/views.py)

Nova view decorada com `@require_POST` que lê `delivery_address` do POST, faz strip e trunca em 500 chars, grava em `request.session['session_delivery_address']` e retorna `HttpResponse('')`. O retorno vazio permite que HTMX faça `hx-swap="outerHTML"` no banner, efetivamente removendo-o do DOM.

### catalog() (core/views.py)

Delta mínimo: uma linha adicionada ao dicionário de contexto. Sem lógica de negócio alterada.

### cart_detail() (core/views.py)

Delta mínimo: `session_delivery_address` adicionado ao contexto. Permite que `cart_drawer.html` pré-preencha o campo de endereço sem JavaScript adicional.

### catalog.html

Banner condicional (`{% if not session_delivery_address and not request.user.is_staff %}`) inserido antes do hero section. Usa HTMX para submit e Hyperscript para dismiss local. GPS via `navigator.geolocation` inline — sem nova dependência JS.

### cart_drawer.html

O `<textarea delivery_address>` agora usa `{{ request.POST.delivery_address|default:session_delivery_address }}`. POST tem prioridade sobre sessão — não-destrutivo.

## Regras preservadas (de `_reversa_sdd/domain.md`)

| Regra | Status |
|-------|--------|
| RN-04: Checkout valida customer_name, customer_phone, delivery_address | ✅ Preservada — pré-preenchimento não torna o campo opcional |
| RN-05: Guest checkout com guest_order_id em sessão | ✅ Preservada — sessão não é afetada |
| RN-09: Token MP por tenant | ✅ Preservada — não tocado |

## Regras modificadas

Nenhuma regra de domínio 🟢 foi alterada ou removida. Todas as mudanças são adições.
