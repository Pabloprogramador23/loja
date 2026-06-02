# Actions: Localização Pré-Catálogo (011-D)

> Identificador: `011-fluxo-cliente-redesign`
> Data: `2026-05-31`
> Roadmap: `_reversa_forward/011-fluxo-cliente-redesign/roadmap.md`
> Escopo: RF-01 apenas — 011-A/B/C implementadas em 012/013/014

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 9 |
| Paralelizáveis (`[//]`) | 4 |
| Maior cadeia de dependência | 4 (T001 → T005 → T006 → T008) |

---

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Adicionar view `save_location(request)` em `core/views.py`: aceita POST com campo `delivery_address`; grava `request.session['session_delivery_address']` com o valor (string strip, máx 500 chars); retorna `HttpResponse('')` com status 200 para que HTMX possa ocultar o banner via `hx-swap="outerHTML"` | - | - | `core/views.py` | 🟢 | `[X]` |
| T002 | Adicionar `path('save-location/', views.save_location, name='save_location')` em `core/urls.py` | T001 | - | `core/urls.py` | 🟢 | `[X]` |

---

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Escrever testes para `save_location()`: (a) POST com endereço válido → `session['session_delivery_address']` atualizado, resposta 200; (b) POST com campo vazio → sessão recebe `''`; (c) endereço muito longo (>500 chars) → truncado ou rejeitado | T002 | `[//]` | `core/tests_location.py` | 🟢 | `[X]` |
| T004 | Escrever teste para `catalog()`: (a) sem endereço na sessão → `context['session_delivery_address'] == ''`; (b) com endereço na sessão → context reflete o valor | T001 | `[//]` | `core/tests_location.py` | 🟢 | `[X]` |

---

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T005 | Atualizar `catalog()` em `core/views.py`: adicionar `session_delivery_address = request.session.get('session_delivery_address', '')` e incluir no dicionário de contexto do `render()` | T001 | - | `core/views.py` | 🟢 | `[X]` |
| T006 | Atualizar `cart_detail()` em `core/views.py`: adicionar `session_delivery_address = request.session.get('session_delivery_address', '')` ao contexto passado ao template `cart_drawer.html` | T005 | - | `core/views.py` | 🟢 | `[X]` |

---

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T007 | Adicionar banner de localização em `catalog.html` logo após o `{% block content %}`: condicional `{% if not session_delivery_address and not request.user.is_staff %}`; conteúdo: campo `<input name="delivery_address">`, botão "Usar minha localização" (chama `navigator.geolocation` via `<script>` inline mínimo), botão "Confirmar" (hx-post=`{% url 'save_location' %}` hx-target=`#location-banner` hx-swap=`outerHTML`), botão "Agora não" (Hyperscript dismiss); envolver tudo em `<div id="location-banner">` | T002, T005 | `[//]` | `templates/core/catalog.html` | 🟢 | `[X]` |
| T008 | Atualizar `cart_drawer.html`: no `<textarea name="delivery_address">`, adicionar `value`-equivalent via conteúdo do elemento usando `{% if not request.POST.delivery_address %}{{ session_delivery_address }}{% endif %}` para pré-preenchimento não-destrutivo (POST tem prioridade sobre sessão) | T006 | `[//]` | `templates/core/partials/cart_drawer.html` | 🟢 | `[X]` |

---

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T009 | Gerar `legacy-impact.md` listando os 4 arquivos modificados com tipo de mudança; gerar `regression-watch.md` com watch items: (1) banner exibido para cliente sem endereço, (2) banner ausente para is_staff, (3) `session_delivery_address` persistido após POST, (4) pré-preenchimento no cart_drawer | T007, T008 | - | `_reversa_forward/011-fluxo-cliente-redesign/` | 🟢 | `[X]` |

---

## Notas de execução

<!-- Reservado para /reversa-coding registrar avisos durante a execução. -->

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-31 | Versão inicial gerada por `/reversa-to-do` | reversa |
