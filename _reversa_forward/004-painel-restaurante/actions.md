# Actions: Painel do Restaurante + Sistema de Comandas

> Identificador: `004-painel-restaurante`
> Data: `2026-05-27`
> Roadmap: `_reversa_forward/004-painel-restaurante/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 15 |
| Paralelizáveis (`[//]`) | 7 |
| Maior cadeia de dependência | 8 (T001 → T003 → T004 → T005 → T006 → T007 → T008 → T010) |

---

## Fase 1 — Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Em `core/models.py`: (1) na classe `Order.Status` TextChoices, inserir `OPEN = 'OPEN', 'Comanda Aberta'` como primeira entrada, antes de `PENDING`; (2) no corpo do modelo `Order`, após o campo `mp_payment_id` e antes de `created_at`, adicionar `table_label = models.CharField(max_length=100, blank=True, default='')` | - | - | `core/models.py` | 🟢 | `[X]` |
| T002 | Criar arquivo `core/migrations/0008_order_comanda_fields.py` com o seguinte conteúdo: dependências `[('core', '0007_store_owner')]`, operação única `migrations.AddField(model_name='order', name='table_label', field=models.CharField(blank=True, default='', max_length=100))`. Obs: `OPEN` no TextChoices não gera operação de migration (sem constraint DB). | T001 | `[//]` | `core/migrations/0008_order_comanda_fields.py` | 🟢 | `[X]` |

---

## Fase 2 — Testes

> Omitida — o projeto não pratica TDD formal. Verificação manual descrita em `onboarding.md`.

---

## Fase 3 — Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Em `core/views.py`, após os views de manager existentes, adicionar duas funções: (1) `comanda_list(request)`: `@login_required`, verifica `user_can_manage_store`, busca `Order.objects.filter(status='OPEN').order_by('-created_at')`, renderiza `'core/manager/comanda_list.html'` com `{'comandas': qs}`; (2) `comanda_create(request)`: `@login_required`, verifica `user_can_manage_store`, no POST valida que `table_label = request.POST.get('table_label','').strip()` não é vazio (se vazio re-renderiza com erro), cria `Order(status='OPEN', table_label=label, customer_name=label, customer_phone='', delivery_address=label, total_amount=Decimal('0.00'))` e redireciona para `redirect('comanda_detail', comanda_id=order.id)` | T001 | `[//]` | `core/views.py` | 🟢 | `[X]` |
| T004 | Em `core/views.py`, adicionar `comanda_detail(request, comanda_id)`: `@login_required`, verifica `user_can_manage_store`, busca `order = get_object_or_404(Order, id=comanda_id, status='OPEN')`, busca `products = Product.objects.filter(is_available=True).order_by('category__name', 'name')`, renderiza `'core/manager/comanda_detail.html'` com `{'order': order, 'products': products, 'pix_data': None}` | T003 | - | `core/views.py` | 🟢 | `[X]` |
| T005 | Em `core/views.py`, adicionar dois views HTMX: (1) `comanda_add_item(request, comanda_id)`: `@require_POST @login_required`, verifica `user_can_manage_store`, busca OPEN order, obtém `product_id = int(request.POST.get('product_id'))` e `quantity = int(request.POST.get('quantity', 1))`, busca produto, cria `OrderItem(order=order, product=product, quantity=quantity, unit_price=product.price)`, recalcula `order.total_amount = sum(i.quantity * i.unit_price for i in order.items.all())`, salva order, retorna `render(request, 'core/manager/_comanda_items.html', {'order': order})`; (2) `comanda_remove_item(request, comanda_id, item_id)`: `@require_POST @login_required`, verifica `user_can_manage_store`, busca OPEN order, faz `order.items.filter(id=item_id).delete()`, recalcula e salva total, retorna `render(request, 'core/manager/_comanda_items.html', {'order': order})` | T004 | - | `core/views.py` | 🟢 | `[X]` |
| T006 | Em `core/views.py`, adicionar `comanda_close(request, comanda_id)`: `@require_POST @login_required`, verifica `user_can_manage_store`, busca OPEN order. Lê `payment_method = request.POST.get('payment_method')`. Se `'presencial'`: `order.status = 'PREPARING'; order.save()`, redireciona para `manager_orders`. Se `'pix'`: se `order.total_amount <= 0`, re-renderiza `comanda_detail.html` com mensagem de erro `'Adicione ao menos um item antes de fechar via PIX'`; senão importa `from .payment import create_pix_payment`, chama `pix_data = create_pix_payment(order)`, seta `order.status = 'PENDING'; order.save()`, renderiza `'core/manager/comanda_detail.html'` com `{'order': order, 'products': Product.objects.filter(is_available=True), 'pix_data': pix_data}` | T005 | - | `core/views.py` | 🟢 | `[X]` |
| T007 | Em `core/urls.py`, adicionar os 6 padrões de URL ao final de `urlpatterns`: `path('dashboard/comandas/', views.comanda_list, name='comanda_list')`, `path('dashboard/comandas/create/', views.comanda_create, name='comanda_create')`, `path('dashboard/comandas/<int:comanda_id>/', views.comanda_detail, name='comanda_detail')`, `path('dashboard/comandas/<int:comanda_id>/add-item/', views.comanda_add_item, name='comanda_add_item')`, `path('dashboard/comandas/<int:comanda_id>/remove-item/<int:item_id>/', views.comanda_remove_item, name='comanda_remove_item')`, `path('dashboard/comandas/<int:comanda_id>/close/', views.comanda_close, name='comanda_close')` | T003 | - | `core/urls.py` | 🟢 | `[X]` |

---

## Fase 4 — Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Criar `templates/core/manager/_comanda_items.html` — partial HTMX. Estrutura: `<div id="comanda-items">` (outerHTML target). Tabela com colunas Produto, Qtd, Unitário, Subtotal, Ação. Para cada `item in order.items.all`: linha com dados do item e formulário `<form hx-post="{% url 'comanda_remove_item' order.id item.id %}" hx-target="#comanda-items" hx-swap="outerHTML">` com botão "Remover" (Tailwind: `text-red-600 hover:text-red-800`). Rodapé da tabela com total formatado `{{ order.total_amount }}`. Se nenhum item: linha com mensagem "Nenhum item adicionado ainda." | T007 | `[//]` | `templates/core/manager/_comanda_items.html` | 🟢 | `[X]` |
| T009 | Criar `templates/core/manager/comanda_list.html` — estende `base_manager.html`, bloco `manager_content`. Header com título "Comandas Abertas" e botão "Nova Comanda" que revela (toggle Hyperscript ou inline) um formulário com campo `table_label` (text input, placeholder "Ex: Mesa 3, Balcão, Delivery João") e botão Criar (`hx-post` ou `action="{% url 'comanda_create' %}" method="post"`). Abaixo: lista de comandas em grid de cards, cada card mostra `comanda.table_label`, `comanda.items.count` itens, total `comanda.total_amount`, e link "Gerenciar" para `{% url 'comanda_detail' comanda.id %}`. Estado vazio: mensagem "Nenhuma comanda aberta no momento." | T007 | `[//]` | `templates/core/manager/comanda_list.html` | 🟢 | `[X]` |
| T010 | Criar `templates/core/manager/comanda_detail.html` — estende `base_manager.html`. Seções: (1) Cabeçalho com `order.table_label` e link "← Voltar para Comandas"; (2) Formulário "Adicionar Item": `<select name="product_id">` com `{% for p in products %}` e campo `<input name="quantity" type="number" min="1" value="1">`, botão com `hx-post="{% url 'comanda_add_item' order.id %}" hx-target="#comanda-items" hx-swap="outerHTML" hx-include="closest form"`; (3) `{% include 'core/manager/_comanda_items.html' %}`; (4) Seção "Fechar Comanda" com dois forms POST para `{% url 'comanda_close' order.id %}`: um com `<input type="hidden" name="payment_method" value="presencial">` e botão "Pagamento Presencial" (verde), outro com `<input type="hidden" name="payment_method" value="pix">` e botão "Fechar via PIX" (azul); (5) Se `pix_data`, exibir seção com QR Code (`<img src="data:image/png;base64,{{ pix_data.qr_code_base64 }}">`) e código copia-e-cola (`{{ pix_data.qr_code }}`). Se `error_msg`, exibir alerta Tailwind vermelho. | T008 | - | `templates/core/manager/comanda_detail.html` | 🟢 | `[X]` |
| T011 | Em `templates/core/manager/base_manager.html`: (1) Na sidebar desktop, após o item "Pedidos" (`manager_orders`), adicionar item "Comandas" com mesmo padrão CSS, link `{% url 'comanda_list' %}`, active class quando `url_name == 'comanda_list'`, ícone SVG de lista (`M9 5H7a2 2 0 00-2 2v12...`); (2) Antes do `<div class="hidden md:flex ...">` da sidebar desktop, inserir botão hamburger mobile: `<button class="md:hidden fixed top-4 left-4 z-50 bg-white p-2 rounded shadow" _="on click toggle .hidden on #mobile-sidebar-panel">` com ícone SVG hamburger; (3) Após o botão, inserir div `<div id="mobile-sidebar-panel" class="hidden fixed inset-0 z-40 md:hidden flex">` contendo: overlay `<div class="fixed inset-0 bg-gray-600 opacity-75" _="on click toggle .hidden on #mobile-sidebar-panel">` e painel lateral `<div class="relative flex-1 flex flex-col max-w-xs w-full bg-white">` com os mesmos itens de nav da sidebar desktop (Visão Geral, Pedidos, Comandas, Catálogo, Configurações, Voltar para Loja) | T007 | `[//]` | `templates/core/manager/base_manager.html` | 🟡 | `[X]` |
| T012 | Em `templates/base.html`, localizar o bloco do link "Meus Pedidos" (`<a href="{% url 'account_orders' %}">Meus Pedidos</a>`) dentro do `{% if user.is_authenticated %}` e substituir por condicional: `{% if user.is_staff %}<a href="{% url 'manager_orders' %}" class="text-indigo-100 hover:text-white font-medium">Pedidos da Loja</a>{% else %}<a href="{% url 'account_orders' %}" class="text-indigo-100 hover:text-white font-medium">Meus Pedidos</a>{% endif %}` | - | `[//]` | `templates/base.html` | 🟢 | `[X]` |
| T013 | Em `templates/core/account/base_account.html`, dentro do `<nav class="space-y-1">` da sidebar, antes do `<form action="{% url 'logout' %}...">`, adicionar bloco condicional para managers: `{% if user.is_staff %}<div class="border-t border-gray-200 pt-4 mt-2"><a href="{% url 'dashboard' %}" class="text-indigo-700 hover:bg-indigo-50 group rounded-md px-3 py-2 flex items-center text-sm font-medium"><svg class="text-indigo-500 flex-shrink-0 -ml-1 mr-3 h-6 w-6" ...ícone de grid/dashboard...></svg><span class="truncate">Painel de Gerência</span></a></div>{% endif %}` | - | `[//]` | `templates/core/account/base_account.html` | 🟢 | `[X]` |
| T014 | Em `core/views.py`, na view `manager_orders`, localizar o queryset principal de `Order` (provavelmente `Order.objects.all()` ou `Order.objects.filter(...)`) e adicionar `.exclude(status='OPEN')` para que comandas abertas não apareçam na lista de pedidos do dashboard | T001 | - | `core/views.py` | 🟢 | `[X]` |

---

## Fase 5 — Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T015 | Localizar o template de atualização de status de pedidos do manager (buscar em `templates/core/manager/` o arquivo que contém o select/dropdown de status — provavelmente `orders.html` ou `_order_row.html`). Identificar onde os valores de `Order.Status` são iterados ou hardcoded no dropdown de atualização. Adicionar condição para excluir `OPEN`: se for loop `{% for s in statuses %}`, envolver com `{% if s.0 != 'OPEN' %}...{% endif %}`; se for hardcoded, simplesmente não incluir a opção OPEN. | T001 | - | `templates/core/manager/orders.html` (ou equivalente) | 🟡 | `[X]` |

---

## Notas de execução

**Verificação manual (2026-05-28):** 28/28 cenários passaram (N-01, N-02, N-03, C-01–C-07, regressões). Bug corrigido durante verificação: `from decimal import Decimal` ausente em `core/views.py` causava NameError 500 na criação de comanda.

---

## Pendências identificadas pelo usuário

| ID | Descrição | Arquivo alvo | Status |
|----|-----------|--------------|--------|
| P001 | Modificações no header — ajustes visuais/funcionais a definir pelo usuário | `templates/base.html` (ou equivalente) | `[X]` |

> Continuação planejada via `/reversa` no Antigravity IDE.

---

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-27 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-05-28 | Verificação manual concluída (28/28 ✅); bug `Decimal` corrigido; pendência P001 registrada | pablo |
| 2026-05-28 | Diferenciação dos menus do header para clientes e administradores concluída (P001 ✅) | Antigravity |
| 2026-05-29 | P001 verificado e validado em produção (Claude Code). Menu admin aparece corretamente para owner da loja (`request.user_can_manage=True`). Causa da falha: processos uvicorn órfãos do dia anterior (sem `--reload`) servindo código desatualizado na porta 8000. Solução: matar processos e subir `uvicorn store_saas.asgi:application --host 127.0.0.1 --port 8000 --reload`. | pablo |
