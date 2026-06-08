# Investigation: Toggle de Métodos de Pagamento

> Identificador: `024-toggle-metodos-pagamento`
> Data: `2026-06-08`

---

## 1. Padrão de referência no próprio legado

A feature `019-toggle-delivery` (pasta `_reversa_forward/019-toggle-delivery/`) é o template exato desta feature. Implementou `Store.delivery_enabled` com:

- Campo booleano no model + migration com `default=True`
- Guard em `views.checkout()` verificando `request.tenant.delivery_enabled`
- Exposição via `context_processors.cart()` (chave `delivery_enabled`)
- Toggle rápido no dashboard (botão HTMX POST sem recarregar a página)
- Checkbox no `StoreSettingsForm`

A feature 024 segue o mesmo padrão, com duas diferenças:
1. São três campos em vez de um
2. Não há toggle rápido separado no dashboard — o `StoreSettingsForm` é o único ponto de configuração (decisão D-04 do roadmap)

---

## 2. Localização dos arquivos a modificar

| Arquivo | O que muda |
|---------|-----------|
| `core/models.py` | +3 `BooleanField` em `Store` após `delivery_enabled` |
| `core/forms.py` | `StoreSettingsForm.fields` recebe os 3 novos campos |
| `core/context_processors.py` | `cart()` retorna +3 chaves lidas de `request.tenant` |
| `core/views.py` | `checkout()` — guard após leitura de `payment_method` |
| Template do drawer do carrinho | Seletores condicionais com `{% if payment_*_enabled %}` |
| Template de settings do dashboard | Seção de checkboxes de métodos de pagamento |

---

## 3. Onde está o drawer do carrinho

Buscar pelo template que contém o radio de `payment_method`. Prováveis candidatos baseados no padrão do projeto:

- `templates/core/cart_drawer.html` ou
- `templates/core/cart.html` (partial HTMX)

O seletor de método de pagamento provavelmente contém algo como:
```html
<input type="radio" name="payment_method" value="online">
<input type="radio" name="payment_method" value="cash">
<input type="radio" name="payment_method" value="card">
```

Cada input deve ser envolvido em `{% if payment_online_enabled %}` etc.

---

## 4. Guard no checkout — posição exata

Em `core/views.py`, a função `checkout()` lê `payment_method = request.POST.get('payment_method')` antes do bloco `transaction.atomic()`. O guard deve ser inserido imediatamente após esta leitura:

```python
# Após: payment_method = request.POST.get('payment_method')

allowed = {
    'online': request.tenant.payment_online_enabled,
    'cash':   request.tenant.payment_cash_enabled,
    'card':   request.tenant.payment_card_enabled,
}

if not any(allowed.values()):
    # Todos desabilitados
    return _checkout_error(request, "Nenhum método de pagamento disponível no momento.")

if payment_method not in allowed or not allowed.get(payment_method):
    return _checkout_error(request, "Método de pagamento não disponível.")
```

`_checkout_error()` já existe no projeto (criado na feature 010) — retorna o drawer do carrinho com contexto de erro.

---

## 5. Aviso de MP sem token

No template de settings, acima do checkbox `payment_online_enabled`:

```html
{% if not store.mercadopago_access_token %}
  <div class="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800 dark:bg-yellow-900/20 dark:border-yellow-700 dark:text-yellow-300">
    Configure o token do MercadoPago para aceitar pagamentos online.
  </div>
{% endif %}
```

---

## 6. Alternativas descartadas

| Alternativa | Por que descartada |
|-------------|-------------------|
| `accepted_payment_methods = JSONField(default=list)` | Mais complexo de validar no form e no backend; rompe com o padrão booleano do projeto |
| `accepted_payment_methods = IntegerField (bitmask)` | Ilegível no admin e no código; desnecessária para 3 opções fixas |
| Toggle rápido no dashboard (como 019) | Métodos de pagamento são configuração planejada, não operação de urgência cotidiana |
| Opção desabilitada renderizada como `disabled` (cinza) | Confunde o cliente — ele não sabe se é bug ou indisponibilidade |
| Bloqueio no `clean()` do form quando `payment_online_enabled=True` sem token | Quebra lojas em dev/staging que usam o fallback mock |
