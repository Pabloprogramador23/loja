# Actions: Cadastro de Loja SaaS (Auto-onboarding)

> Identificador: `002-cadastro-loja-saas`
> Data: `2026-05-26`
> Roadmap: `_reversa_forward/002-cadastro-loja-saas/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 10 |
| Paralelizáveis (`[//]`) | 6 |
| Maior cadeia de dependência | 5 (T001 → T002 → T005 → T007 → T008) |

---

## Fase 1 — Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Adicionar campo `owner = OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=SET_NULL, related_name='owned_store')` na classe `Store` em `core/models.py`, logo após o campo `updated_at` | - | - | `core/models.py` | 🟢 | `[X]` |
| T002 | Criar arquivo de migration `core/migrations/0007_store_owner.py` com operação `AddField` para o campo `owner` conforme especificado em `data-delta.md` | T001 | - | `core/migrations/0007_store_owner.py` | 🟢 | `[X]` |

---

## Fase 2 — Testes

> Omitida — o projeto não pratica TDD formal. Verificação manual descrita em `onboarding.md`.

---

## Fase 3 — Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Criar arquivo novo `accounts/forms.py` com `StoreRegistrationForm` estendendo `UserCreationForm`: adicionar campos `store_name` (CharField, max 255) e `subdomain` (CharField, max 100, com `RegexValidator` para `[a-z0-9][a-z0-9\-]*[a-z0-9]`); implementar `clean_subdomain()` que rejeita valores da lista `RESERVED_SUBDOMAINS` com mensagem "Subdomínio reservado" e verifica unicidade no banco com mensagem "Este subdomínio já está em uso" | - | `[//]` | `accounts/forms.py` | 🟢 | `[X]` |
| T004 | Criar template `templates/accounts/criar_loja.html` estendendo `base.html`: exibir formulário com os 5 campos (username, password1, password2, store_name, subdomain), botão de envio e link de volta para `/login/` | - | `[//]` | `templates/accounts/criar_loja.html` | 🟡 | `[X]` |
| T005 | Adicionar view `criar_loja_view` em `accounts/views.py`: (1) redirecionar para `/` se `request.user.is_authenticated`; (2) instanciar `StoreRegistrationForm`; (3) no POST válido, criar `User` + `Store` em `transaction.atomic()` com `owner=user, is_active=True`; (4) chamar `login(request, user)`; (5) redirecionar para `'dashboard'` | T002, T003 | `[//]` | `accounts/views.py` | 🟢 | `[X]` |
| T006 | Em `core/views.py`: (1) adicionar função helper `user_can_manage_store(request)` retornando `True` se `request.user.is_staff` ou se `getattr(request.user, 'owned_store', None) == request.tenant`; (2) substituir todos os blocos `if not request.user.is_staff` nas views `dashboard`, `manager_orders`, `update_order_status`, `order_details_modal`, `manager_products`, `manager_product_create`, `manager_product_edit`, `manager_settings`, `manager_create_order` por `if not user_can_manage_store(request)` | T002 | `[//]` | `core/views.py` | 🟢 | `[X]` |
| T007 | Em `accounts/views.py`, modificar `login_view`: após `login(request, user)` bem-sucedido, aplicar ordem de redirect — (1) `next` param se presente; (2) `redirect('dashboard')` se `getattr(user, 'owned_store', None)` existir; (3) `redirect('index')` como fallback | T005 | - | `accounts/views.py` | 🟡 | `[X]` |

---

## Fase 4 — Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Adicionar rota `path('criar-loja/', views.criar_loja_view, name='criar_loja')` em `accounts/urls.py` e importar a view | T005 | `[//]` | `accounts/urls.py` | 🟢 | `[X]` |
| T009 | Adicionar link "Crie sua loja" no template `templates/accounts/login.html`, visível apenas para usuários não autenticados, apontando para `{% url 'criar_loja' %}` | - | `[//]` | `templates/accounts/login.html` | 🟡 | `[X]` |

---

## Fase 5 — Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T010 | Em `core/admin.py`, localizar o `ModelAdmin` de `Store` e adicionar `owner` em `list_display` e `readonly_fields` para que o superuser veja o dono de cada loja no painel | T001 | - | `core/admin.py` | 🟡 | `[X]` |

---

## Notas de execução

<!-- Reservado para /reversa-coding registrar avisos durante a execução. -->

---

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-26 | Versão inicial gerada por `/reversa-to-do` | reversa |
