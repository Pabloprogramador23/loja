# Investigation: Remoção de Integrações Desnecessárias

> Identificador: `015-remocao-integracoes`
> Data: `2026-06-01`

---

## 1. Backend customizado de email auth no Django

### Contexto

O `ModelBackend` padrão do Django autentica por **username**, não por email. O projeto já contorna isso em `accounts/views.py:302`:

```python
# workaround existente (accounts/views.py)
u = User.objects.get(email=email)
user = authenticate(request, username=u.username, password=password)
```

Essa lógica precisa migrar para um `AuthenticationBackend` formal que possa ser declarado em `AUTHENTICATION_BACKENDS`.

### Padrão a aplicar

```python
# accounts/backends.py — novo arquivo
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()

class EmailAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = kwargs.get('email') or username
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
```

**Observação:** herdar de `ModelBackend` garante que `user_can_authenticate()` (checa `is_active`) e `get_user()` são herdados, sem reimplementação. 🟢

### Settings após remoção do allauth

```python
# store_saas/settings.py
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'accounts.backends.EmailAuthBackend',
]
# Remover: SITE_ID, ACCOUNT_LOGIN_METHODS, ACCOUNT_SIGNUP_FIELDS
```

---

## 2. O que o allauth realmente entrega no projeto

Com base em `_reversa_sdd/code-analysis.md#3.3`:

| Funcionalidade allauth | Usada? | Após remoção |
|------------------------|--------|-------------|
| Social login Google | Sim (feat 012) | Removida |
| Login por email (ACCOUNT_LOGIN_METHODS) | Sim | Substituída por EmailAuthBackend |
| Signup com email | Sim (ACCOUNT_SIGNUP_FIELDS) | Já gerenciado pelo `CustomerSignupForm` customizado |
| Email confirmation | Não configurado | Sem impacto |
| Password reset | Via `accounts/urls.py` (Django built-in) | Sem impacto — já usa Django nativo |

**Conclusão:** o único papel insubstituível do allauth era o social login. A autenticação por email já é tratada pelo workaround em `accounts/views.py`. 🟢

---

## 3. Checklist de referências ao allauth no código

Antes de executar a remoção, verificar cada ocorrência:

| Símbolo | Onde buscar | O que fazer |
|---------|-------------|-------------|
| `allauth` | `settings.py` INSTALLED_APPS | Remover todas as entradas |
| `allauth.urls` | `store_saas/urls.py` | Remover `path('accounts/', include('allauth.urls'))` |
| `from allauth` | Todo o código Python | Remover import e lógica dependente |
| `socialaccount` | Templates HTML | Remover blocos `{% load socialaccount %}` e tags `{% provider_login_url %}` |
| `SITE_ID` | `settings.py` | Remover |
| `ACCOUNT_LOGIN_METHODS` | `settings.py` | Remover |
| `ACCOUNT_SIGNUP_FIELDS` | `settings.py` | Remover |

---

## 4. Checklist de referências ao Uber Direct no código

| Símbolo | Onde buscar | O que fazer |
|---------|-------------|-------------|
| `import uber_direct` / `from core.uber_direct` | Todo código Python | Remover |
| `UberDirectConfig` | `core/models.py`, `core/forms.py`, `core/views.py` | Remover modelo, campos do form, lógica de views |
| `UberDirectDelivery` | `core/models.py`, `core/api.py` | Remover |
| `UberDirectDeliveryEvent` | `core/models.py`, `core/tasks.py` | Remover |
| `uber_quote_id` | `core/models.py` (Order), `core/views.py` (checkout) | Remover campo e referências |
| `uber_quote_` (sessão) | `core/context_processors.py`, `core/views.py` | Remover lógica de leitura de session |
| `process_uber_webhook` | `core/tasks.py` | Remover task |
| `UBER_SANDBOX`, `UBER_CLIENT_*`, `UBER_CUSTOMER_ID` | `settings.py`, `.env.example` | Remover variáveis |
| `httpx` | `core/uber_direct.py` (principal), todo o código | Confirmar ausência em outros arquivos antes de remover de `requirements.txt` |

---

## 5. Tabelas afetadas pelas migrations

### Removidas por remoção dos modelos Uber Direct

| Tabela | Modelo |
|--------|--------|
| `core_uberdirectconfig` | `UberDirectConfig` |
| `core_uberdirectdelivery` | `UberDirectDelivery` |
| `core_uberdirectdeliveryevent` | `UberDirectDeliveryEvent` |

### Coluna removida

| Tabela | Coluna |
|--------|--------|
| `core_order` | `uber_quote_id` |

### Removidas por remoção do allauth (geradas pelo migrate das apps)

| Tabela | App |
|--------|-----|
| `account_emailaddress` | allauth.account |
| `account_emailconfirmation` | allauth.account |
| `socialaccount_socialaccount` | allauth.socialaccount |
| `socialaccount_socialapp` | allauth.socialaccount |
| `socialaccount_socialapp_sites` | allauth.socialaccount |
| `socialaccount_socialtoken` | allauth.socialaccount |
| `django_site` | django.contrib.sites (se removido junto) |

---

## 6. django.contrib.sites — remover ou manter?

`SITE_ID = 1` e `django.contrib.sites` foram adicionados como dependência do allauth. Verificar no código se qualquer outra parte usa `from django.contrib.sites.models import Site`. Se não houver, remover limpa o schema de `django_site` também.

**Recomendação:** buscar `django.contrib.sites` e `from django.contrib.sites` antes de decidir.
