# Actions: Remoção de Integrações Desnecessárias

> Identificador: `015-remocao-integracoes`
> Data: `2026-06-01`
> Roadmap: `_reversa_forward/015-remocao-integracoes/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 22 |
| Paralelizáveis (`[//]`) | 12 |
| Maior cadeia de dependência | 4 (T003 → T007 → T010 → T017) |

---

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Auditar uso de `httpx` no projeto: buscar `import httpx` e `from httpx` em todo código Python e registrar resultado em "Notas de execução" | - | `[//]` | `core/uber_direct.py` (origem) | 🟡 | `[X]` |
| T002 | Auditar uso de `django.contrib.sites` no projeto: buscar `from django.contrib.sites` e `django.contrib.sites` em todo código Python e registrar resultado em "Notas de execução" | - | `[//]` | `store_saas/settings.py` (origem) | 🟡 | `[X]` |
| T003 | Criar migration `0015_remove_uber_direct` em `core/migrations/`: remover modelos `UberDirectConfig`, `UberDirectDelivery`, `UberDirectDeliveryEvent` e campo `uber_quote_id` de `Order` | - | - | `core/migrations/0015_remove_uber_direct.py` | 🟢 | `[X]` |

---

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Remover arquivos e/ou classes de teste relacionados ao Uber Direct em `core/tests_*.py` (buscar por `UberDirect`, `uber_direct`, `uber_quote`) | - | `[//]` | `core/tests_uber.py` | 🟡 | `[X]` |
| T005 | Remover testes de Google OAuth e allauth social login de `accounts/tests.py` (buscar por `google`, `socialaccount`, `allauth`) | - | `[//]` | `accounts/tests.py` | 🟡 | `[X]` |

---

## Fase 3, Núcleo

### Frente A — Uber Direct

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T006 | Remover `core/uber_direct.py` inteiramente (confirmar T001 antes de deletar o arquivo) | T001 | - | `core/uber_direct.py` | 🟢 | `[X]` |
| T007 | Em `core/models.py`: remover classes `UberDirectConfig`, `UberDirectDelivery`, `UberDirectDeliveryEvent` e o campo `uber_quote_id` de `Order` | T003 | - | `core/models.py` | 🟢 | `[X]` |
| T008 | Em `core/tasks.py`: remover a task `process_uber_webhook` e seus imports de `uber_direct` | T006 | - | `core/tasks.py` | 🟢 | `[X]` |
| T009 | Em `core/api.py`: remover o endpoint de webhook Uber Direct e seus imports de `uber_direct` | T006 | - | `core/api.py` | 🟢 | `[X]` |
| T010 | Em `core/views.py` → `checkout()`: remover toda a lógica de cotação Uber (`session['uber_quote_*']`, `uber_quote_id`); taxa de entrega passa a ser sempre `effective_fee = store.delivery_fee` (respeitando threshold) | T007 | - | `core/views.py` | 🟢 | `[X]` |
| T011 | Em `core/context_processors.py`: remover branch de cálculo de taxa via Uber Direct; manter apenas o cálculo estático `delivery_fee` + `free_delivery_threshold` | T007 | `[//]` | `core/context_processors.py` | 🟢 | `[X]` |
| T012 | Em `core/forms.py` → `StoreSettingsForm`: remover todos os campos de configuração Uber Direct (`client_id`, `client_secret`, `customer_id`, `is_active`) | T007 | `[//]` | `core/forms.py` | 🟢 | `[X]` |

### Frente B — Allauth / Google OAuth

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T013 | Criar `accounts/backends.py` com `EmailAuthBackend(ModelBackend)`: busca `User` por `email`, verifica senha com `check_password`, herda `user_can_authenticate` do `ModelBackend` | - | `[//]` | `accounts/backends.py` | 🟢 | `[X]` |
| T014 | Em `store_saas/settings.py`: remover `allauth`, `allauth.account`, `allauth.socialaccount`, `allauth.socialaccount.providers.google` e `django.contrib.sites` de `INSTALLED_APPS`; substituir `AUTHENTICATION_BACKENDS` por `['django.contrib.auth.backends.ModelBackend', 'accounts.backends.EmailAuthBackend']`; remover `SITE_ID`, `ACCOUNT_LOGIN_METHODS`, `ACCOUNT_SIGNUP_FIELDS` e variáveis `UBER_*`, `GOOGLE_*` | T013 | - | `store_saas/settings.py` | 🟢 | `[X]` |
| T015 | Em `store_saas/urls.py`: remover `path('accounts/', include('allauth.urls'))` | T014 | `[//]` | `store_saas/urls.py` | 🟢 | `[X]` |
| T016 | Em `accounts/views.py`: remover qualquer `from allauth` import; garantir que o workaround email→username (`User.objects.get(email=email)`) que existia para suprir o ModelBackend é substituído pelo novo `EmailAuthBackend` (o workaround pode ser removido se o backend estiver em `AUTHENTICATION_BACKENDS`) | T013 | - | `accounts/views.py` | 🟢 | `[X]` |

---

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T017 | Em templates de auth: remover botão/link "Entrar com Google" e qualquer `{% load socialaccount %}` de `auth_modal.html`, `modal_login.html`, `login.html`, `signup.html` | T014 | - | `templates/accounts/` | 🟢 | `[X]` |
| T018 | Em template de configurações da loja: remover seção visual de Uber Direct (campos de formulário, botões, textos explicativos) | T012 | `[//]` | `templates/core/` (settings template) | 🟢 | `[X]` |
| T019 | Em `requirements.txt`: remover linha `django-allauth[socialaccount]`; se T001 confirmar uso exclusivo no Uber Direct, remover também `httpx` | T006, T014, T001 | - | `requirements.txt` | 🟡 | `[X]` |
| T020 | Em `.env.example` (se existir): remover variáveis `UBER_CLIENT_ID`, `UBER_CLIENT_SECRET`, `UBER_CUSTOMER_ID`, `UBER_SANDBOX`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | T014 | `[//]` | `.env.example` | 🟡 | `[X]` |

---

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T021 | Se T002 confirmou que `django.contrib.sites` não tem outro uso: remover de `INSTALLED_APPS` (já incluído em T014 se confirmado; esta ação só existe se T014 manteve a app por precaução) | T002, T014 | `[//]` | `store_saas/settings.py` | 🟡 | `[X]` |
| T022 | Varredura final: grep por `uber_direct`, `UberDirect`, `allauth`, `socialaccount`, `UBER_`, `GOOGLE_CLIENT` no código Python e templates; limpar qualquer referência residual encontrada | T008, T009, T016, T017 | `[//]` | (varredura global) | 🟢 | `[X]` |

---

## Notas de execução

- **T001:** `httpx` usado exclusivamente em `core/uber_direct.py` — removido de `requirements.txt`
- **T002:** `django.contrib.sites` usado exclusivamente em `store_saas/settings.py` como dependência do allauth — removido junto com allauth em T014
- **T005:** `accounts/tests.py` não continha referências a Google OAuth ou allauth — nenhuma ação necessária
- **T011:** `core/context_processors.py` já não continha lógica Uber Direct — nenhuma modificação necessária
- **T020:** `.env.example` não existe no projeto — ação ignorada
- **T022:** Resíduos encontrados em `core/tests.py` (classe `UberDirectModelTest`) e `core/tests_checkout.py` (3 testes Uber) — removidos

---

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-01 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-06-01 | Todas as 22 ações executadas por `/reversa-coding` | reversa |
