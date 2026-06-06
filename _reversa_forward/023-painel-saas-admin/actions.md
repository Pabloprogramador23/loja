# Actions: Painel SaaS Admin

> Identificador: `023-painel-saas-admin`
> Data: `2026-06-05`
> Roadmap: `_reversa_forward/023-painel-saas-admin/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 18 |
| Paralelizáveis (`[//]`) | 9 |
| Maior cadeia de dependência | 5 (T001 → T007 → T008 → T013 → T017) |

---

## Fase 1 — Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Criar `core/saas_urls.py` com urlpatterns vazios (stub) e registrar o prefixo `path('saas/', include('core.saas_urls'))` em `store_saas/urls.py`, antes do `include('core.urls')` | - | - | `core/saas_urls.py`, `store_saas/urls.py` | 🟢 | `[X]` |
| T002 | Criar diretório `templates/core/saas/` e o template base `templates/core/saas/saas_base.html` estendendo `dashboard_base.html`, sobrescrevendo o título e adicionando um badge/header "⚙ Painel SaaS" para distinguir visualmente do dashboard do lojista | - | `[//]` | `templates/core/saas/saas_base.html` | 🟡 | `[X]` |

---

## Fase 2 — Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Escrever testes de proteção de rota em `core/tests_saas.py`: (a) superuser acessa `/saas/` → 200; (b) usuário com `is_staff=True` e `is_superuser=False` → redirect para `/dashboard/`; (c) anônimo → redirect para `/login/` | T001 | `[//]` | `core/tests_saas.py` | 🟢 | `[X]` |
| T004 | Escrever testes de métricas de listagem: criar 2 lojas, criar N pedidos em cada, verificar que `total_orders` e `orders_today` retornam valores corretos por loja (usar `timezone.localdate()` como hoje) | T001 | `[//]` | `core/tests_saas.py` | 🟢 | `[X]` |
| T005 | Escrever testes de `SaasCreateStoreForm`: (a) dados válidos cria User + Store; (b) subdomínio duplicado falha com erro de validação; (c) campos obrigatórios ausentes falham | T001 | `[//]` | `core/tests_saas.py` | 🟡 | `[X]` |
| T006 | Escrever teste de toggle `is_active`: (a) desativar loja → `is_active=False`; (b) tentar desativar loja cujo `owner == request.user` → bloqueado (guard de proteção) | T001 | `[//]` | `core/tests_saas.py` | 🟢 | `[X]` |

---

## Fase 3 — Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T007 | Criar `core/saas_views.py` com `SuperuserRequiredMixin`: método `dispatch()` verifica `request.user.is_authenticated` (senão redirect `/login/`), depois `is_superuser` (senão redirect `/dashboard/`), depois chama `set_current_tenant(None)` para zerar o ContextVar antes de qualquer query | T001 | - | `core/saas_views.py` | 🟢 | `[X]` |
| T008 | Implementar `saas_dashboard` view em `core/saas_views.py` usando `Store.objects.annotate(total_orders=Count('order'), orders_today=Count('order', filter=Q(order__created_at__date=today)))` — calcular também `active_count` e `inactive_count` para os contadores do topo; passar tudo no context | T007 | - | `core/saas_views.py` | 🟢 | `[X]` |
| T009 | Implementar `saas_store_toggle` view (POST + HTMX) em `core/saas_views.py`: busca Store por `pk`, recusa desativar se `store.owner == request.user` (retorna 403 com mensagem), togla `is_active`, salva, retorna o partial `saas/partials/store_toggle.html` com o objeto store atualizado | T007 | - | `core/saas_views.py` | 🟢 | `[X]` |
| T010 | Implementar `SaasCreateStoreForm` em `core/forms.py` com campos `store_name`, `subdomain`, `manager_email`, `manager_password`; método `clean_subdomain()` valida unicidade; método `save()` executa `transaction.atomic()` criando `User.objects.create_user(...)` com `is_staff=True` e `Store.objects.create(name=..., subdomain=..., owner=user, is_active=True)` com `store_id` atribuído explicitamente | T001 | `[//]` | `core/forms.py` | 🟢 | `[X]` |
| T011 | Implementar `saas_store_create` view (GET/POST, class-based) em `core/saas_views.py` usando `SaasCreateStoreForm`; no POST válido redireciona para `/saas/` com mensagem de sucesso via `messages.success` | T007, T010 | - | `core/saas_views.py` | 🟡 | `[X]` |
| T012 | Implementar `saas_store_detail` view em `core/saas_views.py`: busca Store por `pk`, busca últimos 10 pedidos com `Order.objects.filter(store=store).order_by('-created_at')[:10]` (ContextVar já está None pelo mixin), mascara token MP com `token[-6:]` se existir | T007 | - | `core/saas_views.py` | 🟡 | `[X]` |

---

## Fase 4 — Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T013 | Criar `templates/core/saas/dashboard.html` estendendo `saas_base.html`: contadores ativos/inativos no topo, tabela com colunas (Nome, Subdomínio, Status, Pedidos hoje, Pedidos totais, Criada em, Ações), botão "Ver loja" com `target="_blank"`, botão "Nova loja" | T002, T008 | - | `templates/core/saas/dashboard.html` | 🟢 | `[X]` |
| T014 | Criar partial `templates/core/saas/partials/store_toggle.html`: badge de status + botão HTMX `hx-post="/saas/lojas/<id>/toggle/"` `hx-swap="outerHTML"` `hx-target="this"` — retornado pelo `saas_store_toggle` para atualizar o badge sem reload | T009 | `[//]` | `templates/core/saas/partials/store_toggle.html` | 🟢 | `[X]` |
| T015 | Criar `templates/core/saas/store_create.html` estendendo `saas_base.html`: formulário com campos `store_name`, `subdomain`, `manager_email`, `manager_password`, botão submit "Criar loja", link de volta para `/saas/` | T002, T011 | `[//]` | `templates/core/saas/store_create.html` | 🟡 | `[X]` |
| T016 | Criar `templates/core/saas/store_detail.html` estendendo `saas_base.html`: seção de dados cadastrais, seção do owner, token MP mascarado (`****{{ store.mercadopago_access_token|slice:"-6:" }}`), taxa de entrega, tabela com últimos 10 pedidos (id, cliente, status, total, data) | T002, T012 | `[//]` | `templates/core/saas/store_detail.html` | 🟡 | `[X]` |
| T017 | Preencher `core/saas_urls.py` com todos os patterns finais: `path('', saas_dashboard, name='saas_dashboard')`, `path('lojas/nova/', saas_store_create, name='saas_store_create')`, `path('lojas/<int:pk>/', saas_store_detail, name='saas_store_detail')`, `path('lojas/<int:pk>/toggle/', saas_store_toggle, name='saas_store_toggle')` | T008, T009, T011, T012 | - | `core/saas_urls.py` | 🟢 | `[X]` |

---

## Fase 5 — Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T018 | Adicionar `allauth` URL pattern em `store_saas/urls.py` se ainda não existir — verificar e garantir que o `allauth.urls` não conflita com `/saas/`; ajustar ordem de includes se necessário | T001 | `[//]` | `store_saas/urls.py` | 🟡 | `[X]` |
| T018b | Gerar `_reversa_forward/023-painel-saas-admin/regression-watch.md` listando os pontos de regressão a vigiar: TenantMiddleware (isolamento), saas_dashboard queries, toggle is_active, criação Store+User | T017 | - | `_reversa_forward/023-painel-saas-admin/regression-watch.md` | 🟢 | `[X]` |

---

## Notas de execução

<!-- Reservado para /reversa-coding registrar avisos ou observações que surgirem durante a execução. -->

- **Atenção T009/T012:** `set_current_tenant(None)` zera o ContextVar, então `Order.objects.filter(store=store)` funciona globalmente. O mixin garante isso antes de qualquer query da view.
- **Atenção T010:** `Store` não herda de `TenantAwareModel` — `store_id` não precisa vir do ContextVar; atribuir diretamente em `Store.objects.create(...)`.
- **Atenção T018:** O ID T018b foi usado por colisão de numeração (T018 já alocado) — manter ambos, não reciclar.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-05 | Versão inicial gerada por `/reversa-to-do` | reversa |
