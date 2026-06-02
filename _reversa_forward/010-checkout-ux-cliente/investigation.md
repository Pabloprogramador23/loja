# Investigation: 010-checkout-ux-cliente

> Data: `2026-05-30`

## Padrão UserProfile no Django

O padrão `OneToOneField` para extensão de `auth.User` é o caminho recomendado pela documentação oficial do Django quando não é possível usar um custom user model desde o início do projeto. Ver: https://docs.djangoproject.com/en/5.0/topics/auth/customizing/#extending-the-existing-user-model

**Por que não usar custom user model agora?** Trocar o `AUTH_USER_MODEL` após o projeto já ter migrations aplicadas exige reconstrução completa do banco de dados, inviável em produção.

## Alternativa descartada: buscar phone do último Order

```python
# Abordagem descartada
phone = Order.objects.filter(
    user=request.user, store=tenant
).order_by('-created_at').values_list('customer_phone', flat=True).first() or ''
```

**Problema:** Executa uma query a cada abertura do carrinho sem cache. Em tenant com muitos pedidos, pode gerar lentidão. Além disso, o dado não é "do usuário" — é do último pedido, podendo refletir um número temporário digitado errado. `UserProfile` permite que o usuário corrija o telefone no perfil.

## Hyperscript para toggle do textarea

O projeto já usa Hyperscript (biblioteca `_="..."`) em outros lugares do template (ex.: `_="on click add .translate-x-full to #cart-drawer"`). A sintaxe para revelar o textarea é:

```html
<button type="button"
  _="on click remove .hidden from #delivery-address-textarea then add .hidden to me">
  Outro endereço
</button>
```

Isso mantém consistência com o padrão já adotado no projeto, sem precisar de JavaScript vanilla ou Alpine.js.

## Formato da string de endereço

Formato atual (bugado):
```
Rua Baturité, 118 - Centro
```

Formato corrigido (RN-11):
```
Rua Baturité, 118 - Centro, Fortaleza - CE
Rua Baturité, 118 - Centro, Fortaleza - CE, CEP 60410-350  ← quando zip_code preenchido
```

A string é armazenada em `Order.delivery_address` e exibida no painel do manager. Incluir cidade e estado melhora também a exibição para o gestor da loja.

## Compatibilidade com Uber Direct (feature 009)

O endpoint FastAPI `POST /api/uber-direct/quote` recebe o valor do textarea via `hx-include="[name='delivery_address']"`. Se o textarea estiver oculto mas presente no DOM com um valor preenchido (via `selectAddress`), o HTMX ainda o incluirá na requisição. Testado o comportamento do HTMX: `hx-include` seleciona por atributo `name`, não por visibilidade.

**Conclusão:** manter o textarea no DOM (apenas com `class="hidden"`) é suficiente para não regredir o Uber Direct.
