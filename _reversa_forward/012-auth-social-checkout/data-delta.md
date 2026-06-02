# Data Delta: 012-auth-social-checkout

> Data: `2026-05-30`
> Fonte: `_reversa_sdd/domain.md`, `_reversa_sdd/dependencies.md`

## Nova dependência

```
django-allauth[socialaccount]>=65.0.0
```

Adicionar em `requirements.txt`.

## Tabelas criadas pelo allauth (via migrations automáticas)

O allauth gerencia suas próprias migrations. Não há código manual de migration necessário.

| Tabela | Descrição |
|--------|-----------|
| `django_site` | Sites framework (`django.contrib.sites`) — criado pela migration `sites.0001_initial` |
| `account_emailaddress` | E-mails verificados por usuário |
| `account_emailconfirmation` | Tokens de confirmação de e-mail |
| `socialaccount_socialapp` | Configuração do app social (client_id, client_secret por provider + site) |
| `socialaccount_socialaccount` | Vínculo entre `User` e conta social (ex.: Google UID) |
| `socialaccount_socialtoken` | Tokens OAuth armazenados por conta social |

## Configuração obrigatória no settings.py

```python
SITE_ID = 1  # Obrigatório para django.contrib.sites

INSTALLED_APPS += [
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

MIDDLEWARE += [
    'allauth.account.middleware.AccountMiddleware',  # Após AuthenticationMiddleware
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Allauth — comportamento
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Sem verificação por e-mail obrigatória agora
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True

# Google — credenciais via env vars (NÃO hardcode)
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='')
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET', default='')
```

## Configuração manual no Django Admin (pós-migration)

1. Acesse `/admin/sites/site/` → edite o Site ID 1 → defina `domain` e `name` (ex.: `localhost:8000`)
2. Acesse `/admin/socialaccount/socialapp/add/` → crie um SocialApp:
   - Provider: Google
   - Name: Google
   - Client id: `<GOOGLE_CLIENT_ID>`
   - Secret key: `<GOOGLE_CLIENT_SECRET>`
   - Sites: mova `localhost:8000` para "Chosen sites"

## Models customizados — nenhum novo

O `CustomerSignupForm` já existe (feature 010) e `UserProfile` já tem `phone`. O ajuste é somente no form: adicionar `first_name` e `last_name` à versão do modal (sem alterar o form de signup normal).

## Variáveis de ambiente novas

Adicionar a `.env` e `.env.prod`:

```
GOOGLE_CLIENT_ID=cole_aqui_o_client_id_do_google_cloud
GOOGLE_CLIENT_SECRET=cole_aqui_o_client_secret_do_google_cloud
```

Como obter: Google Cloud Console → APIs & Services → Credentials → Create OAuth 2.0 Client ID → Web application → Authorized redirect URIs: `http://localhost:8000/accounts/google/login/callback/`
