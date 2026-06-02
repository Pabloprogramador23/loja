# Regression Watch: 011-fluxo-cliente-redesign (011-D)

> Feature: Localização Pré-Catálogo
> Gerado em: 2026-05-31

## Watch Items

| ID | Origem | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------|-----------------------------|------|-------------------|
| W001 | `core/views.py — save_location()` | View `save_location` existe, é decorada com `@require_POST` e grava `session['session_delivery_address']` | presença | Se extração futura não encontrar a view ou encontrá-la sem `@require_POST` |
| W002 | `core/views.py — catalog()` | `catalog()` passa `session_delivery_address` ao contexto do template | presença | Se a chave `session_delivery_address` sumir do contexto de `catalog()` |
| W003 | `core/views.py — cart_detail()` | `cart_detail()` passa `session_delivery_address` ao contexto de `cart_drawer.html` | presença | Se a chave `session_delivery_address` sumir do contexto de `cart_detail()` |
| W004 | `templates/core/catalog.html` | Banner `#location-banner` exibido condicionalmente para clientes sem endereço na sessão e sem `is_staff` | presença | Se o banner sumir do template ou perder a condicional de `is_staff` |

## Observações (🟡 INFERIDO — sem peso de regressão)

- GPS usa `navigator.geolocation` inline no template. Ambientes sem HTTPS (dev local) podem ter o GPS bloqueado pelo browser — comportamento esperado, não é regressão.
- O banner usa `hx-swap="outerHTML"` no `#location-banner`. Se o ID mudar, o swap para de funcionar e o banner não some após submit — bug de UX, não de dados.

## Histórico de re-extrações

<!-- Preenchido automaticamente pelo /reversa quando re-executado -->

## Arquivadas

<!-- IDs de watch items encerrados em extrações futuras -->
