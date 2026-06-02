# Actions: Modo Escuro (Dark Mode)

> Identificador: `006-dark-mode`
> Data: `2026-05-29`
> Roadmap: `_reversa_forward/006-dark-mode/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 23 |
| Paralelizáveis (`[//]`) | 15 |
| Maior cadeia de dependência | 6 (T001 → T003 → T004 → T010 → T012 → T022) |

## Fase 1, Preparação

<!-- Modelo, migração, configuração de tema e bootstrap. -->

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Criar modelo `UserSettings` em `core/models.py`: OneToOne com `auth.User` (`related_name='settings'`, `on_delete=CASCADE`), campo `theme = CharField(max_length=10, choices=[('system','Sistema'),('light','Claro'),('dark','Escuro')], default='system')` e `updated_at = DateTimeField(auto_now=True)`. **Não** herdar de `TenantAwareModel` | - | `[//]` | `core/models.py` | 🟡 | `[X]` |
| T002 | Gerar a migração do novo modelo: `python manage.py makemigrations core` (esperado `core/migrations/0009_usersettings.py`, dependência `0008_order_comanda_fields`, operação única `CreateModel`) | T001 | - | `core/migrations/0009_usersettings.py` | 🟡 | `[X]` |
| T003 | Criar context processor `theme_preference(request)` em `core/context_processors.py` que retorna `{'theme_pref': <UserSettings.theme do usuário logado, ou 'system'>}` com leitura defensiva (`get_or_create`/`getattr`); registrá-lo em `store_saas/settings.py` → `TEMPLATES[0]['OPTIONS']['context_processors']` | T001 | `[//]` | `core/context_processors.py`, `store_saas/settings.py` | 🟡 | `[X]` |
| T004 | No `<head>` de `templates/base.html`: adicionar `<script>tailwind.config = { darkMode: 'class' }</script>` após o CDN do Tailwind; adicionar script inline de bootstrap anti-FOUC (ordem: `theme_pref` server-side → `localStorage['theme']` → `prefers-color-scheme`) que aplica a classe `dark` em `document.documentElement`; renderizar a classe inicial no `<html>` via `theme_pref` | T003 | `[//]` | `templates/base.html` | 🟢 | `[X]` |
| T005 | Replicar a mesma configuração de `darkMode`, bootstrap anti-FOUC e classe server-side no `<head>`/`<html>` de `templates/dashboard_base.html` (layout standalone) | T003 | `[//]` | `templates/dashboard_base.html` | 🟢 | `[X]` |

## Fase 2, Testes

<!-- O legado pratica testes (core/tests*.py); cobrir modelo e endpoint. -->

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T006 | Teste de `UserSettings`: default `theme == 'system'`, restrição OneToOne (um registro por usuário), choices válidas | T001 | - | `core/tests.py` | 🟡 | `[X]` |
| T007 | Teste do endpoint `POST /set-theme/`: sucesso retorna 204 e grava; `theme` inválido → 400; anônimo é barrado (`login_required`); idempotência (mesmo valor reenviado) | T009 | - | `core/tests.py` | 🟡 | `[X]` |

## Fase 3, Núcleo

<!-- View, rota, toggle e tematização do chrome global. -->

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Criar view `set_theme(request)` em `core/views.py`: `@login_required`, `@require_POST`, valida `theme` contra as choices, `UserSettings.objects.get_or_create(user=request.user)` + grava, responde `HttpResponse(status=204)` | T001 | - | `core/views.py` | 🟢 | `[X]` |
| T009 | Registrar a rota `path('set-theme/', views.set_theme, name='set_theme')` em `core/urls.py` | T008 | - | `core/urls.py` | 🟢 | `[X]` |
| T010 | No `<body>` de `templates/base.html`: adicionar botão de toggle de tema no header (com `aria-label`, operável por teclado; hyperscript/JS que alterna a classe `dark`, grava `localStorage` e, se `user.is_authenticated`, faz `POST /set-theme/` com CSRF) e aplicar variantes `dark:` no chrome global (body, header, footer, drawer do carrinho, toast container, botão flutuante mobile) | T004, T009 | - | `templates/base.html` | 🟢 | `[X]` |
| T011 | No `<body>` de `templates/dashboard_base.html`: adicionar toggle equivalente e variantes `dark:` no chrome (body, sidebar/topbar) | T005, T009 | - | `templates/dashboard_base.html` | 🟢 | `[X]` |

## Fase 4, Integração

<!-- Tematização das telas de conteúdo; áreas independentes podem rodar em paralelo. -->

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T012 | Variantes `dark:` na vitrine principal | T010 | `[//]` | `templates/core/index.html`, `catalog.html`, `partials/category_pills.html`, `partials/product_list.html` | 🟡 | `[X]` |
| T013 | Variantes `dark:` no carrinho (drawer e respostas de adição) | T010 | `[//]` | `templates/core/partials/cart_drawer.html`, `add_to_cart_response.html`, `order_modal.html` | 🟡 | `[X]` |
| T014 | Variantes `dark:` no checkout e pagamento PIX | T010 | `[//]` | `templates/core/partials/checkout_error.html`, `checkout_success.html`, `payment_pix.html` | 🟡 | `[X]` |
| T015 | Variantes `dark:` nas telas de pedidos do cliente | T010 | `[//]` | `templates/core/order_track.html`, `my_orders.html`, `account/orders.html`, `account/order_detail.html` | 🟡 | `[X]` |
| T016 | Variantes `dark:` na área "Minha Conta" (layout + telas + endereços) | T010 | `[//]` | `templates/core/account/base_account.html`, `account/dashboard.html`, `account/addresses.html`, `partials/address_list.html` | 🟡 | `[X]` |
| T017 | Variantes `dark:` no painel do gestor (layout + visão geral + pedidos) | T010 | `[//]` | `templates/core/manager/base_manager.html`, `dashboard.html`, `orders.html`, `partials/order_row.html` | 🟡 | `[X]` |
| T018 | Variantes `dark:` na gestão de catálogo e configurações | T010 | `[//]` | `templates/core/manager/products.html`, `product_form.html`, `settings.html` | 🟡 | `[X]` |
| T019 | Variantes `dark:` nas comandas (gestor) e criação de pedido | T010 | `[//]` | `templates/core/manager/comanda_list.html`, `comanda_detail.html`, `_comanda_items.html`, `manager_create_order.html` | 🟡 | `[X]` |
| T020 | Variantes `dark:` no dashboard standalone (layout `dashboard_base.html`) | T011 | `[//]` | `templates/core/dashboard.html` | 🟡 | `[X]` |
| T021 | Variantes `dark:` nas telas públicas de autenticação | T010 | `[//]` | `templates/accounts/login.html`, `signup.html`, `criar_loja.html` | 🟡 | `[X]` |

## Fase 5, Polimento

<!-- Acessibilidade/contraste e regressão de parciais HTMX. -->

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T022 | Revisar contraste (WCAG AA para texto) e consistência da paleta `dark:` nas telas-chave (home, checkout, painel do gestor), ajustando tons inconsistentes | T012, T014, T017 | - | `templates/core/index.html`, `partials/payment_pix.html`, `manager/dashboard.html` | 🟡 | `[X]` |
| T023 | Verificar que parciais trocadas via HTMX não "voltam ao claro" após swap (o `<html>.dark` permanece, mas as parciais precisam das variantes); corrigir variantes faltantes | T013, T016, T017 | `[//]` | `templates/core/partials/`, `templates/core/manager/partials/` | 🟡 | `[X]` |

## Notas de execução

<!--
Reservado para /reversa-coding registrar avisos ou observações que surgiram durante a execução.
Não use isso para corrigir ações, edits manuais ficam fora desse arquivo, vão direto no código.
-->

- **T001 já existia:** o modelo `UserSettings` foi encontrado pronto em `core/models.py` (resíduo da sessão anterior interrompida). Usa `TextChoices` em vez de `choices=[...]` inline — funcionalmente idêntico ao spec. Marcado como concluído sem reescrita.
- **Validação:** `python manage.py check` limpo, 18 testes passam (8 novos: 3 de modelo + 5 de endpoint), migração `0009` aplica, 14 templates-chave compilam sem erro de sintaxe.
- 🟡 **Observação (fora de escopo dos alvos):** as linhas da tabela em `templates/core/dashboard.html` são injetadas por HTMX a partir de `/api/orders` (HTML server-side fora dos templates). Ainda sem variantes `dark:`. O mesmo vale para o parcial de `/api/orders/<id>/track`. Recomenda-se ajuste futuro nesses geradores de HTML da API.
- 🟡 **Observação (T019/POS):** em `manager_create_order.html`, `filterCategory()` (JS) alterna `bg-gray-100/bg-gray-900` nas pills diretamente, podendo sobrepor as variantes `dark:` do estado ativo/inativo. Telas usáveis; refino exigiria JS ciente do tema.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-29 | Versão inicial gerada por `/reversa-to-do` | reversa |
