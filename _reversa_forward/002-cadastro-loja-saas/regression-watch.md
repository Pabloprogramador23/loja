# Regression Watch: 002-cadastro-loja-saas

> Feature: Auto-onboarding de loja SaaS + acesso ao dashboard por ownership
> Gerado em: `2026-05-26`

---

## Watch Items

| ID | Origem | Regra esperada após mudança | Tipo | Sinal de violação |
|----|--------|-----------------------------|------|-------------------|
| W001 | `_reversa_sdd/domain.md#RN-12` → `core/views.py` | `user_can_manage_store(request)` retorna True se `is_staff=True` OU se `user.owned_store == request.tenant` | presença | Se a re-extração mostrar que o dashboard ainda usa apenas `is_staff` sem checar ownership, ou se o helper for removido |
| W002 | `_reversa_sdd/domain.md#RN-12` → backward compat | Superusers com `is_staff=True` continuam acessando o dashboard de qualquer loja sem ownership | presença | Se re-extração mostrar que `is_staff` foi removido do OR do helper |
| W003 | `_reversa_sdd/code-analysis.md#Módulo 3` → `accounts/views.py#login_view` | Após login bem-sucedido, usuários com `owned_store` são redirecionados para `dashboard`; os sem loja vão para `index` | redação | Se re-extração mostrar que `login_view` redireciona todos para `index` sem checar `owned_store` |
| W004 | `_reversa_sdd/architecture.md#Store (model)` → `core/models.py` | `Store` possui campo `owner` do tipo OneToOneField para `auth.User`, nullable | presença | Se re-extração não identificar o campo `owner` em `Store` ou classificar como ForeignKey |

---

## Observações (regras 🟡 / 🔴 — sem peso de regressão)

- A criação atômica de User + Store em `criar_loja_view` via `transaction.atomic()` é inferida (🟡) — se a re-extração mostrar ausência do bloco atômico, investigue mas não trate como regressão crítica.
- O comportamento de `login_view` para usuários com `is_authenticated` acessando `/criar-loja/` (redirect para `/`) é novo (🟡) — sem âncora na extração original.

---

## Histórico de re-extrações

> Nenhuma re-extração executada após esta feature. Rode `/reversa` para iniciar o ciclo de verificação.

---

## Arquivadas

> Nenhum item arquivado.
