# Actions: Toggle de Métodos de Pagamento

> Identificador: `024-toggle-metodos-pagamento`
> Data: `2026-06-08`
> Roadmap: `_reversa_forward/024-toggle-metodos-pagamento/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 10 |
| Paralelizáveis (`[//]`) | 6 |
| Maior cadeia de dependência | 4 (T001 → T005 → T008 → T010) |

---

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Adicionar os três campos ao modelo `Store` em `core/models.py`: `payment_online_enabled`, `payment_cash_enabled`, `payment_card_enabled` — todos `BooleanField(default=True)` — posicionados após `delivery_enabled` | - | `[//]` | `core/models.py` | 🟢 | `[X]` |
| T002 | Gerar a migration com `makemigrations core --name store_payment_method_toggles` e aplicar com `migrate` | T001 | - | `core/migrations/0018_store_payment_method_toggles.py` | 🟢 | `[X]` |

---

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Escrever testes para o guard do checkout: método desabilitado retorna erro sem criar Order; todos desabilitados bloqueia; método habilitado prossegue | T002 | `[//]` | `core/tests_toggle_payment_methods.py` | 🟢 | `[X]` |
| T004 | Escrever testes para o context processor: 3 novas chaves com valores corretos do tenant; sem tenant retorna True | T002 | `[//]` | `core/tests_toggle_payment_methods.py` | 🟡 | `[X]` |

---

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T005 | Atualizar `context_processors.cart()`: +3 chaves `payment_online_enabled`, `payment_cash_enabled`, `payment_card_enabled` lidas de `request.tenant` de forma defensiva | T001 | `[//]` | `core/context_processors.py` | 🟡 | `[X]` |
| T006 | Inserir guard em `views.checkout()` após leitura de `payment_method`: dict `allowed_methods` + bloco de todos desabilitados + bloco de método específico desabilitado | T001 | `[//]` | `core/views.py` | 🟢 | `[X]` |
| T007 | Atualizar `StoreSettingsForm`: +3 campos em `fields` + labels em português + widgets `CheckboxInput` com classes Tailwind dark mode | T001 | `[//]` | `core/forms.py` | 🟢 | `[X]` |

---

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Atualizar template do drawer do carrinho: seletores condicionais com `{% if %}`, valor padrão do hidden input dinâmico, `#entrega-options` visível por padrão quando online desabilitado, aviso quando todos desabilitados | T005 | - | `templates/core/partials/cart_drawer.html` | 🟢 | `[X]` |
| T009 | Atualizar template de settings: seção "Métodos de Pagamento" com 3 checkboxes + aviso amarelo quando token MP ausente | T007 | - | `templates/core/manager/settings.html` | 🟡 | `[X]` |

---

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T010 | Gerar `regression-watch.md`, `legacy-impact.md`, `progress.jsonl` e atualizar `actions.md` — 9/9 testes passando confirmado | T008, T009 | - | `_reversa_forward/024-toggle-metodos-pagamento/` | 🟢 | `[X]` |

---

## Notas de execução

- **T003**: Correção necessária — mock de `process_new_order.delay` adicionado em `test_enabled_method_proceeds_normally` (Redis não disponível fora do Docker).
- **T008**: Template `cart_drawer.html` tem lógica Hyperscript para seleção de método. A condicionalidade foi implementada mantendo a compatibilidade com todos os cenários de combinação de flags.

---

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-08 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-06-08 | Todas as ações marcadas `[X]` — execução concluída por `/reversa-coding` | reversa |
