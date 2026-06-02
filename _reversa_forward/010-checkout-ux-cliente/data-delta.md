# Data Delta: 010-checkout-ux-cliente

> Data: `2026-05-30`
> Fonte do legado: `_reversa_sdd/domain.md`, `_reversa_sdd/erd-complete.md`

## Novo model: `UserProfile`

```python
# core/models.py
class UserProfile(models.Model):
    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='profile',
    )
    phone = models.CharField(max_length=20, blank=True, default='')

    def __str__(self):
        return f"Perfil de {self.user.username}"
```

**Notas:**
- `OneToOneField` com `related_name='profile'` → acesso via `user.profile`
- Não herda `TenantAwareModel` — o perfil é global do usuário, não por loja (um usuário pode ter pedidos em múltiplas lojas com o mesmo telefone)
- `phone` é `blank=True` para não quebrar criação de usuários sem telefone (admin, seed, signup)

## Migration: `0012_userprofile`

```python
# core/migrations/0012_userprofile.py
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0011_uber_direct'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(blank=True, default='', max_length=20)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='profile',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
    ]
```

## Models não alterados

| Model | Motivo de não alterar |
|-------|----------------------|
| `Order` | `delivery_address` permanece TextField livre — a correção é na montagem da string no JS |
| `Address` | Nenhum campo novo; a regra de limite já existe no model |
| `Store` | Sem alteração |
| `auth.User` | Sem alteração — extensão via `UserProfile` |

## Padrão de acesso seguro

Em toda leitura de `user.profile.phone`, usar `get_or_create` para evitar `RelatedObjectDoesNotExist`:

```python
profile, _ = UserProfile.objects.get_or_create(user=request.user)
phone = profile.phone
```

Em toda escrita após checkout:

```python
if request.user.is_authenticated and phone:
    UserProfile.objects.update_or_create(
        user=request.user,
        defaults={'phone': phone}
    )
```
