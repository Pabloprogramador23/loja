# Data Delta: 002-cadastro-loja-saas

> Data: `2026-05-26`
> Modelo base extraído em: `_reversa_sdd/code-analysis.md#Módulo 2` e `_reversa_sdd/erd-complete.md`

---

## Mudanças no model `Store` (`core/models.py`)

### Campo novo: `owner`

| Atributo | Valor |
|----------|-------|
| Tipo Django | `OneToOneField` |
| Aponta para | `settings.AUTH_USER_MODEL` (`auth.User`) |
| `on_delete` | `SET_NULL` |
| `null` | `True` |
| `blank` | `True` |
| `related_name` | `'owned_store'` |
| Posição na classe | Após `updated_at` |

**Justificativa do `on_delete=SET_NULL`:** se o usuário dono for deletado, a loja não deve ser removida — ela pode ser reatribuída manualmente via admin. `CASCADE` apagaria toda a loja (categorias, produtos, pedidos) ao deletar o usuário, risco inaceitável.

### Migration

**Arquivo:** `core/migrations/0007_store_owner.py`

```python
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_add_mp_payment_id_to_order'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='store',
            name='owner',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='owned_store',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
```

### Impacto em queries existentes

| Query | Impacto |
|-------|---------|
| `Store.objects.all()` | Nenhum — coluna nullable adicionada |
| `Store.objects.filter(is_active=True).first()` (TenantMiddleware fallback) | Nenhum |
| `Store.objects.get(subdomain=...)` | Nenhum |
| `TenantAwareModel.save()` (auto-assign de loja) | Nenhum — não toca `owner` |

### Acesso ao campo no código

```python
# Do Store → User (dono)
store.owner          # User ou None

# Do User → Store (loja que ele possui)
# SEGURO — usa getattr para evitar RelatedObjectDoesNotExist
store = getattr(user, 'owned_store', None)

# ALTERNATIVA com try/except
try:
    store = user.owned_store
except Store.DoesNotExist:
    store = None
```

> **Atenção:** `user.owned_store` levanta `RelatedObjectDoesNotExist` (não retorna `None`) quando o User não possui Store associado. Sempre usar `getattr(user, 'owned_store', None)` fora de contextos onde a existência já foi confirmada.

---

## Nenhuma outra tabela alterada

| Model | Alterado? | Motivo |
|-------|-----------|--------|
| `Category` | Não | Feature não toca catálogo |
| `Product` | Não | Feature não toca catálogo |
| `Order` | Não | Feature não toca pedidos |
| `OrderItem` | Não | Feature não toca pedidos |
| `Address` | Não | Feature não toca endereços |
| `auth.User` | Não | Extensão via OneToOne no lado `Store`, não no User |
