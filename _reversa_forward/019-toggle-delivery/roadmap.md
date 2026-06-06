# Roadmap: Toggle Delivery — Loja Aberta/Fechada

> Identificador: `019-toggle-delivery`
> Data: `2026-06-04`
> Requirements: `_reversa_forward/019-toggle-delivery/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

---

## 1. Resumo da abordagem

Delta mínimo em quatro camadas:

**Modelo:** Campo `Store.delivery_enabled = BooleanField(default=True)` + migration. `default=True` garante que todas as lojas existentes continuam abertas sem qualquer intervenção.

**Context processor:** `context_processors.cart()` já itera sobre `tenant` para calcular taxa de entrega. Adicionar `delivery_enabled: tenant.delivery_enabled if tenant else True` ao dict retornado expõe o flag para **todos** os templates sem nenhum repasse manual.

**Views:** (a) `views.checkout()` ganha a primeira verificação do corpo: se `store.delivery_enabled is False`, chama `_checkout_error()` com mensagem de loja fechada — sem criar nenhum objeto. (b) Nova view `toggle_delivery_view` em `POST /dashboard/toggle-delivery/` que flipa o campo e retorna um partial HTMX com o novo estado do botão. Segue exatamente o mesmo padrão de `update_order_status` (HTMX inline, sem redirect de página).

**Templates:** Quatro pontos de UI — banner no catálogo/home, drawer bloqueado, botão de toggle no dashboard. Todos condicionais em `{{ delivery_enabled }}`.

Nenhuma integração externa, nenhuma migration com dados, nenhum novo modelo.

---

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Utilidade antes de completude | Pedido direto do cliente com uso diário (fechar à noite, abrir de manhã). Uso imediato garantido. | respeita |
| II. Integrações essenciais apenas | Nenhuma integração nova. Puramente interno. | respeita |
| III. Configuração simples, operação autônoma | Toggle a um clique no dashboard — sem variável de ambiente, sem restart, sem conhecimento técnico. | respeita |
| IV. Produto focado, não showcase | Solução mais simples possível: um BooleanField + uma view de toggle. Descartado agendamento automático por horário (complexo, sem pedido explícito). | respeita |

---

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Campo `delivery_enabled` no modelo `Store` (não em tabela separada) | `Store` já concentra todas as configurações da loja (`delivery_fee`, `free_delivery_threshold`, `is_active`). Padrão estabelecido. | Tabela `StoreConfig` separada (over-engineering para um bool), `is_active` reutilizado (destrói a loja no middleware) | 🟢 |
| D-02 | Exposição via context processor existente `cart()` | Já executado em todo request Django; adicionar uma chave não tem custo. Evita `request.tenant.delivery_enabled` espalhado pelos templates. | Context processor separado (desnecessário), template tag (mais verboso) | 🟢 |
| D-03 | Toggle rápido via `POST /dashboard/toggle-delivery/` retornando partial HTMX | Padrão já usado em `update_order_status` (`core/views.py`) — consistência máxima, sem novo paradigma. | Modal de confirmação (atrito desnecessário para ação reversível), redirect de página (quebra UX do dashboard) | 🟢 |
| D-04 | Bloqueio no `checkout()` como **primeira verificação**, antes de qualquer leitura de dados | Falha rápida; nenhum objeto criado em banco se loja fechada. `_checkout_error()` já existe para retornar o drawer com erro. | Bloqueio no context processor (não impede POST direto), middleware (escopo muito amplo) | 🟢 |
| D-05 | Banner no catálogo e home, drawer desabilitado — cliente navega mas não compra | Preserva a experiência de "ver o cardápio" mesmo com loja fechada; cliente pode decidir voltar mais tarde. | Redirecionar para página de erro (agressivo demais, corta a vitrine do restaurante) | 🟡 |
| D-06 | Sem agendamento automático por horário de funcionamento | Fora do escopo pedido; aumentaria complexidade em 10× (timezone, DST, feriados). Princípio IV. | Cron job de abertura/fechamento automático | 🟢 |

---

## 4. Premissas

Nenhuma. Requirements sem `[DÚVIDA]`.

---

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `Store` (modelo) | `core/models.py:16` | regra-nova | Campo `delivery_enabled BooleanField(default=True)` |
| `context_processors.cart` | `core/context_processors.py:4` | regra-alterada | Adiciona chave `delivery_enabled` ao dict retornado |
| `views.checkout` | `core/views.py:173` | regra-alterada | Verifica `store.delivery_enabled` como primeira guarda |
| `views.toggle_delivery_view` | — | componente-novo | View `POST /dashboard/toggle-delivery/` — flip do campo + partial HTMX |
| `StoreSettingsForm` | `core/forms.py:68` | regra-alterada | Adiciona `delivery_enabled` aos `fields` |
| `core/urls.py` | `core/urls.py` | contrato-novo | Rota `path('dashboard/toggle-delivery/', ...)` |
| `templates/core/partials/cart_drawer.html` | template existente | regra-alterada | Aviso + botão desabilitado quando `delivery_enabled=False` |
| `templates/core/catalog.html` | template existente | regra-alterada | Banner de loja fechada quando `delivery_enabled=False` |
| `templates/core/index.html` | template existente | regra-alterada | Idem ao catalog |
| `templates/core/manager/dashboard.html` | template existente | regra-alterada | Botão toggle com estado visual (verde/cinza) |
| `templates/core/manager/partials/delivery_toggle.html` | — | componente-novo | Partial HTMX retornado pelo toggle |

---

## 6. Delta no modelo de dados

- Campo novo em `Store`: `delivery_enabled BooleanField(default=True, null=False)`
- Migration necessária: `0017_store_delivery_enabled`
- Detalhe completo em: `_reversa_forward/019-toggle-delivery/data-delta.md`

---

## 7. Delta de contratos externos

Nenhum. Feature puramente interna.

---

## 8. Plano de migração

Zero-downtime:

1. Aplicar migration `0017_store_delivery_enabled` — `default=True`, sem rewrite de dados
2. Deploy das views e templates (adições puras + alterações backward-compatible)
3. Nenhuma ação manual necessária após deploy

---

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Manager fecha loja por engano | médio | baixo | Toggle é reversível em um clique; estado visível no dashboard com cor contrastante | 
| POST direto em `/checkout/` contornando a UI | médio | baixo | Bloqueio está na view server-side (D-04) — UI desabilitada é só conveniência | 
| `delivery_enabled` não aparece no context processor em algum template sem request de tenant | baixo | baixo | Guard `if tenant else True` no context processor; valor padrão seguro | 

---

## 10. Critério de pronto

- [ ] Migration `0017` aplicada sem erro
- [ ] POST em `/checkout/` com `delivery_enabled=False` não cria Order
- [ ] Banner visível no catálogo com loja fechada
- [ ] Botão do dashboard alterna estado com um clique e reflete visualmente
- [ ] `StoreSettingsForm` salva `delivery_enabled` corretamente
- [ ] `regression-watch.md` gerado

---

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-04 | Versão inicial gerada por `/reversa-plan` | reversa |
