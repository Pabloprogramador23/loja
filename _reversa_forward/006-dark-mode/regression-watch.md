# Regression Watch — Modo Escuro (Dark Mode)

> Identificador: `006-dark-mode`
> Data: `2026-05-29`
> Gerado por: `/reversa-coding`

Esta feature é **aditiva**: a seção "Modificadas" do `legacy-impact.md` está vazia, logo **não há watch items de regressão sobre regras 🟢 pré-existentes alteradas/removidas**. Os itens abaixo são do tipo `presença`: registram os novos invariantes 🟢 CONFIRMADOS (implementados e testados nesta rodada) que uma re-extração futura via `/reversa` deve continuar encontrando — sinalizando se a feature regrediu ou foi removida.

## Watch items

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|------------------------------|---------------------|-------------------|
| W001 | `core/models.py` → `UserSettings` | Existe modelo `UserSettings` OneToOne com `auth.User` (`related_name='settings'`, `on_delete=CASCADE`), campo `theme` com choices `system/light/dark` e default `system`. **Não** é `TenantAwareModel` (preferência global por usuário). | presença | `domain.md`/`data-dictionary.md` re-extraídos não mencionam `UserSettings`, ou o descrevem como tenant-aware, ou o default deixa de ser `system`. |
| W002 | `core/views.py` → `set_theme` + `core/urls.py` | Existe endpoint `POST /set-theme/` com `@login_required` + `@require_POST`, validação de `theme` contra as choices, resposta `204`, idempotente via `get_or_create`. | presença | Endpoint ausente nas specs re-extraídas, ou perdeu `login_required`/validação/idempotência, ou passou a responder com corpo. |
| W003 | `core/context_processors.py` → `theme_preference` + `store_saas/settings.py` | Context processor `theme_preference` registrado, com leitura defensiva (anônimo/sem registro → `system`). | presença | `theme_preference` não registrado em `TEMPLATES`, ou leitura deixa de ser defensiva (quebra para usuário sem `UserSettings`). |
| W004 | `templates/base.html`, `templates/dashboard_base.html` (`<head>`) | Bootstrap anti-FOUC com precedência **servidor (logado) → `localStorage` → `prefers-color-scheme`**, e `tailwind.config = { darkMode: 'class' }`. | redação | A ordem de precedência muda, o anti-FOUC some (flash de tema ao carregar) ou `darkMode:'class'` deixa de ser configurado. |
| W005 | Parciais HTMX (`category_pills`, `product_list`, `cart_drawer`, `order_modal`, `address_list`, `_comanda_items`, `order_row`) | Parciais trocados por swap mantêm variantes `dark:` próprias (não dependem só do `<html>.dark`). | presença | Parcial re-extraído/alterado perde as variantes `dark:` e "volta ao claro" após swap. |

## Observações

Itens fora do peso de regressão (gaps conhecidos 🟡, registrados para acompanhamento, não bloqueiam):

- 🟡 Linhas da tabela em `templates/core/dashboard.html` são injetadas por `/api/orders` (HTML server-side, fora dos templates) e ainda **não** têm variantes `dark:`. Idem o parcial de `/api/orders/<id>/track`.
- 🟡 Em `manager_create_order.html`, o `filterCategory()` (JS) manipula `bg-gray-100/bg-gray-900` diretamente nas pills de categoria, podendo sobrepor as variantes `dark:` do estado ativo/inativo.

## Histórico de re-extrações

### Re-extração 2026-05-29 17:00

> Modo: refresh incremental (atualização focada dos artefatos `_reversa_sdd/` afetados pela 006, seguida da verificação de regressão).

| ID | Veredito | Observação |
|----|----------|------------|
| W001 | 🟢 verde | `UserSettings` preservado em `data-dictionary.md`, `domain.md#RN-19` e `erd-complete.md`: OneToOne com `auth.User` (`related_name='settings'`, CASCADE), `theme` choices `system/light/dark` default `system`, explicitamente **não** tenant-aware. Bate integralmente. |
| W002 | 🟢 verde | Endpoint `POST /set-theme/` presente em `code-analysis.md#2.9` e `domain.md#RN-19`: `@login_required` + `@require_POST`, validação de `theme`, resposta `204`, idempotente via `get_or_create`. |
| W003 | 🟢 verde | Context processor `theme_preference` documentado em `code-analysis.md#2.9`, registrado em `store_saas/settings.py`, leitura defensiva (anônimo/sem registro → `system`). |
| W004 | 🟢 verde | Anti-FOUC com precedência servidor (logado) → `localStorage` → `prefers-color-scheme` e `darkMode:'class'` registrados em `architecture.md` (Camada de Apresentação) e `domain.md#RN-19`. |
| W005 | 🟢 verde | `architecture.md` lista os parciais HTMX que carregam variantes `dark:` próprias para não reverterem ao claro após swap. Gap conhecido de `/api/orders` permanece registrado como observação 🟡 (fora do peso de regressão). |

**Resultado:** 5/5 verdes. Nenhuma regressão semântica. (1º verde de cada item — arquivamento exige 3 verdes consecutivos.)

## Arquivadas

_(Vazio.)_
