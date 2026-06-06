# Investigation: Painel SaaS Admin

> Identificador: `023-painel-saas-admin`
> Data: `2026-06-05`

## 1. Problema central: queries cross-tenant no mesmo processo

O `TenantManager` injeta `.filter(store=tenant)` em qualquer queryset sobre `TenantAwareModel` quando há tenant no `ContextVar`. O `TenantMiddleware` roda em TODOS os requests Django — incluindo `/saas/` — e resolve um tenant (em dev: `Store.filter(is_active=True).first()`). Isso significa que uma view em `/saas/` que fizesse `Order.objects.all()` sem intervenção receberia apenas os pedidos do tenant resolvido pelo middleware, não de todas as lojas.

**Solução adotada:** `SuperuserRequiredMixin` chama `set_current_tenant(None)` como primeiro passo na view, zerando o ContextVar para o contexto da requisição atual. A partir daí, `TenantManager.get_queryset()` retorna o queryset sem filtro.

**Referência no legado:** `_reversa_sdd/code-analysis.md#2.1 Multi-tenancy`:
```python
def get_queryset(self):
    tenant = get_current_tenant()
    if tenant:
        return super().get_queryset().filter(store=tenant)
    return super().get_queryset()  # ← retorno global quando None
```

## 2. Por que métricas via `Store.objects.annotate()` é seguro

`Store` herda de `models.Model`, não de `TenantAwareModel`. Seu manager é o padrão do Django — sem filtro de tenant. A annotation via FK reversa (`Count('order')`) vira um JOIN SQL direto:

```sql
SELECT core_store.*, COUNT(core_order.id) AS total_orders
FROM core_store
LEFT OUTER JOIN core_order ON core_order.store_id = core_store.id
GROUP BY core_store.id
```

Nenhum filtro de tenant é injetado aqui. O resultado é sempre global.

## 3. Criação de Store + User sem TenantAwareModel.save()

`TenantAwareModel.save()` faz:
```python
if not self.store_id:
    self.store = get_current_tenant()
```

Na criação pelo painel SaaS, o ContextVar está zerado (`None`) — então `get_current_tenant()` retornaria `None` e o Store criado ficaria sem `store_id` (o que não faz sentido para o próprio model Store, que é o tenant).

Para `Store`, isso não é problema — Store não herda de `TenantAwareModel`. Para modelos filhos (Category, Product) que poderiam ser criados indiretamente, o `store_id` deve ser atribuído explicitamente na view.

A view `SaasCreateStoreView` usará:
```python
with transaction.atomic():
    user = User.objects.create_user(username=..., email=..., password=..., is_staff=True)
    store = Store.objects.create(name=..., subdomain=..., owner=user, is_active=True)
```

Sem ambiguidade de ContextVar.

## 4. Toggle is_active — impacto imediato no middleware

`TenantMiddleware` resolve o tenant com `Store.objects.get(subdomain=subdomain, is_active=True)`. Ao setar `is_active=False`, a próxima requisição ao subdomínio resulta em `Store.DoesNotExist` → HTTP 404. O efeito é imediato — sem necessidade de cache invalidation, pois não há cache nesse path.

Referência: `_reversa_sdd/domain.md#RN-02` e `_reversa_sdd/code-analysis.md#2.1 Multi-tenancy`.

## 5. Padrão HTMX para toggle sem reload (feature 019 como referência)

A feature 019 (Toggle Delivery) implementou exatamente o padrão de toggle com HTMX:
- View Django recebe `POST`
- Atualiza campo booleano
- Retorna HTML parcial do elemento atualizado
- HTMX faz `hx-swap="outerHTML"` no elemento clicado

O mesmo padrão se aplica ao toggle `is_active` da loja. Arquivo de referência: `templates/core/manager/partials/delivery_toggle.html`.

## 6. Mascaramento do token MercadoPago

O token é uma string no formato `TEST-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX` (sandbox) ou `APP_USR-...` (produção). No template, exibir apenas os últimos 6 caracteres:

```python
# No context da view ou como template filter
def mask_token(token):
    if not token or len(token) < 6:
        return "****"
    return f"****{token[-6:]}"
```

Nunca renderizar o token completo em HTML — ele apareceria no código-fonte da página.
