# Interface: `set-theme` (HTTP)

> Identificador: `006-dark-mode`
> Data: `2026-05-29`
> Tipo: HTTP first-party (consumido pelo browser via HTMX/fetch)
> Confidência: 🟡 INFERIDO (contrato novo, ainda não implementado)

## Propósito

Persistir a preferência de tema de um **usuário autenticado** no modelo `UserSettings`. Visitantes anônimos **não** chamam este endpoint (persistem só em `localStorage`).

## Endpoint

```
POST /set-theme/
```

- **Roteamento:** Django (`core/urls.py`), não a API FastAPI. Motivo: usa sessão, CSRF e `login_required` (ver D-04 no roadmap).
- **Autenticação:** `@login_required`. Requisição anônima → redirect de login (302) ou 401, conforme config; o cliente anônimo não deve chamar.
- **CSRF:** obrigatório. O `base.html` já injeta `X-CSRFToken` em requisições HTMX (`htmx:configRequest`).

## Request

| Atributo | Valor |
|----------|-------|
| Método | `POST` |
| Content-Type | `application/x-www-form-urlencoded` (form) |
| Header | `X-CSRFToken: <token>` |

### Corpo

| Campo | Tipo | Obrigatório | Valores aceitos |
|-------|------|-------------|-----------------|
| `theme` | string | sim | `system` \| `light` \| `dark` |

Exemplo:
```
theme=dark
```

## Response

| Cenário | Status | Corpo |
|---------|--------|-------|
| Sucesso | `204 No Content` | vazio |
| `theme` ausente/ inválido | `400 Bad Request` | mensagem curta de erro |
| Não autenticado | `302` (redirect login) ou `401` | conforme config do projeto |
| CSRF ausente/ inválido | `403 Forbidden` | página/erro padrão de CSRF do Django |

> A resposta é intencionalmente sem corpo (204): a troca visual já ocorre no cliente (toggle da classe `dark`); o POST apenas persiste. Não há necessidade de re-render via HTMX.

## Idempotência

- **Idempotente.** Reenviar o mesmo `theme` resulta no mesmo estado (`UserSettings.theme` sobrescrito com o mesmo valor). `get_or_create` + atribuição.

## Timeouts e falhas

- Operação rápida (1 UPDATE/INSERT). Sem dependência externa.
- **Degradação:** se o POST falhar, a escolha visual e o `localStorage` no cliente permanecem; a persistência no perfil simplesmente não acontece nesta sessão. O cliente pode ignorar o erro silenciosamente (a UX não bloqueia).

## Observações de implementação (para o /reversa-coding)

- Validar `theme` contra as choices do modelo antes de gravar.
- Usar `UserSettings.objects.get_or_create(user=request.user)` e então setar `theme`.
- Garantir `csrf_protect` (padrão Django em views não isentas).
