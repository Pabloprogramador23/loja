# Interface: Google OAuth2

> Contrato externo gerenciado pelo `django-allauth`; não requer implementação manual.

## Fluxo

```
Browser → GET /accounts/google/login/?next=/checkout/
       ← 302 → accounts.google.com/o/oauth2/auth?client_id=...&redirect_uri=...&scope=email+profile

Browser → GET accounts.google.com/o/oauth2/auth  (autorização pelo usuário)
       ← 302 → /accounts/google/login/callback/?code=AUTH_CODE&state=STATE

Browser → GET /accounts/google/login/callback/?code=...
  allauth internamente:
    POST https://oauth2.googleapis.com/token  (troca code por access_token)
    GET  https://www.googleapis.com/oauth2/v2/userinfo  (busca profile)
  → cria/atualiza User + SocialAccount
  → login(request, user)
  ← 302 → LOGIN_REDIRECT_URL ou next param
```

## Escopos solicitados

| Scope | Dado obtido | Uso |
|-------|-------------|-----|
| `email` | E-mail verificado | Chave de identificação do usuário |
| `profile` | Nome e foto | Preencher `first_name`, `last_name` no cadastro |

## Parâmetros relevantes

| Campo | Valor |
|-------|-------|
| Authorization URL | `https://accounts.google.com/o/oauth2/auth` |
| Token URL | `https://oauth2.googleapis.com/token` |
| Redirect URI | `http://localhost:8000/accounts/google/login/callback/` |
| Timeout | Gerenciado pelo allauth (padrão: 10s) |
| Idempotência | SocialAccount é upserted pelo e-mail — sem duplicatas |

## Erros mapeados

| Cenário | Comportamento allauth |
|---------|----------------------|
| Usuário nega autorização | Redireciona para `/accounts/google/login/cancelled/` |
| Token expirado | allauth tenta refresh; se falhar, pede novo login |
| `SocialApp` não configurado no banco | `SocialApp.DoesNotExist` → 500 se não tratado |
| `GOOGLE_CLIENT_ID` vazio | Tratar no template: ocultar aba Google |

## Configuração no Google Cloud Console

- Authorized JavaScript origins: `http://localhost:8000`
- Authorized redirect URIs: `http://localhost:8000/accounts/google/login/callback/`
- Para produção: adicionar domínio real nas duas listas
