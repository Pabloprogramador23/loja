# Roadmap: Localização Pré-Catálogo (011-D)

> Identificador: `011-fluxo-cliente-redesign`
> Data: `2026-05-31`
> Requirements: `_reversa_forward/011-fluxo-cliente-redesign/requirements.md`
> Escopo desta rodada: **RF-01 apenas** — sub-features 011-A/B/C já implementadas em 012/013/014
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A feature é inteiramente frontend + session — sem nova tabela, sem migration, sem contrato externo.

**Eixo 1 — Banner de localização no catálogo:** ao acessar `/catalog/`, se `session['session_delivery_address']` estiver vazio, exibe um banner fixo no topo da página com campo de texto (endereço manual) e botão "Usar minha localização" (GPS via Geolocation API). O banner pode ser dispensado; o catálogo fica visível atrás (MoSCoW: Should, não bloqueia).

**Eixo 2 — Endpoint de gravação:** `POST /save-location/` recebe `delivery_address`, grava em `request.session['session_delivery_address']` e retorna resposta HTMX que oculta o banner. Sem autenticação requerida.

**Eixo 3 — Pré-preenchimento no checkout:** `cart_detail()` e `checkout()` leem `session['session_delivery_address']` e passam para o contexto do `cart_drawer.html`, onde o `<textarea name="delivery_address">` recebe o `value` da sessão se o usuário ainda não escreveu manualmente.

**Sem model change.** Padrão de sessão é consistente com o carrinho (`cart_{tenant_id}` em `_reversa_sdd/architecture.md#ADR-004`).

## 2. Princípios aplicados

Arquivo `principles.md` não encontrado — sem princípios registrados.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|---------------|--------------------------|-------------|
| D-01 | Armazenar endereço como `session['session_delivery_address']` (chave distinta do POST `delivery_address`) | Sem model change; alinhado com ADR-004 (carrinho em sessão); chave distinta evita colisão com o campo POST do checkout | Cookie standalone (descartado: sem server-side; expira no browser); model `UserAddress` (descartado: overkill para endereço temporário de sessão) | 🟢 |
| D-02 | Banner não-bloqueante no topo de `catalog.html` com dismiss via Hyperscript | MoSCoW RF-01 = Should; bloquear o catálogo aumentaria abandono; Hyperscript já usado no projeto | Modal bloqueante (descartado: RF-01 não é Must); redirect para página dedicada (descartado: adiciona fricção) | 🟢 |
| D-03 | GPS via `navigator.geolocation.getCurrentPosition()` inline no template | Sem dependência nova; API nativa do browser; o endereço resultante é texto livre (reverse geocoding opcional — fora do escopo) | Biblioteca de mapas (descartado: overkill para texto livre) | 🟡 |
| D-04 | `POST /save-location/` como view Django simples (não FastAPI) | Usa sessão Django; sem autenticação requerida; padrão das views existentes | Endpoint FastAPI (descartado: FastAPI não tem acesso à sessão Django sem middleware extra) | 🟢 |
| D-05 | Pré-preenchimento via context em `cart_detail()` + `cart_drawer.html` | `cart_detail` já renderiza o drawer e passa contexto; adicionar `session_address` ao contexto é um delta mínimo | Pré-preenchimento via JS após load (descartado: sem garantia de timing; mais frágil) | 🟢 |

## 4. Premissas

Nenhuma — sem `[DÚVIDA]` no requirements.md.

## 5. Delta arquitetural

| Componente | Arquivo legado | Tipo | Resumo |
|------------|---------------|------|--------|
| `catalog()` | `core/views.py` | regra-alterada | Passa `session_delivery_address` ao contexto do template |
| `cart_detail()` | `core/views.py` | regra-alterada | Passa `session_delivery_address` ao contexto do `cart_drawer.html` |
| `save_location()` | `core/views.py` | componente-novo | View POST que grava endereço na sessão e retorna fragmento HTMX |
| URL `save-location/` | `core/urls.py` | componente-novo | Rota para `save_location` |
| `catalog.html` | `templates/core/catalog.html` | regra-alterada | Banner de localização condicional no topo |
| `cart_drawer.html` | `templates/core/partials/cart_drawer.html` | regra-alterada | `value` do textarea `delivery_address` pré-preenchido da sessão |

## 6. Delta no modelo de dados

- **Sem alteração de model.** Nenhum campo novo, nenhuma migration.
- Dado novo: `session['session_delivery_address']` — string, vive na sessão Django existente.
- Detalhe completo em: `_reversa_forward/011-fluxo-cliente-redesign/data-delta.md`

## 7. Delta de contratos externos

Nenhum — feature 100% interna.

## 8. Plano de migração

1. Adicionar view `save_location()` em `core/views.py`
2. Adicionar URL `path('save-location/', views.save_location, name='save_location')` em `core/urls.py`
3. Atualizar `catalog()` para passar `session_delivery_address` ao contexto
4. Atualizar `cart_detail()` para passar `session_delivery_address` ao contexto
5. Adicionar banner de localização em `catalog.html`
6. Atualizar `cart_drawer.html`: pré-preencher `delivery_address` da sessão

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| GPS negado pelo browser → endereço vazio | Baixo | Alto | Fallback: campo de texto sempre visível; GPS é opcional |
| Endereço de sessão desatualizado (cliente muda de endereço) | Médio | Baixo | Usuário pode editar o campo no checkout normalmente; sessão é sobrescrita no próximo `save-location/` |
| `session_delivery_address` conflito de chave com outro skill | Baixo | Baixo | Chave prefixada `session_delivery_address` é única no codebase |
| Banner exibido para manager ao acessar catálogo | Baixo | Médio | Condicional `{% if not request.user.is_staff %}` no template |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Ao acessar `/catalog/` sem endereço na sessão, banner é exibido
- [ ] Ao preencher e confirmar o endereço, banner some e sessão guarda o valor
- [ ] GPS preenche o campo de texto ao clicar no botão (quando permitido pelo browser)
- [ ] `delivery_address` no `cart_drawer.html` pré-preenchido com o valor da sessão
- [ ] Manager (`is_staff`) não vê o banner
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-31 | Versão inicial — escopo restrito a RF-01 (011-D), 011-A/B/C já implementados | reversa |
