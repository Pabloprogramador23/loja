# Roadmap: Painel do Restaurante + Sistema de Comandas

> Identificador: `004-painel-restaurante`
> Data: `2026-05-27`
> Requirements: `_reversa_forward/004-painel-restaurante/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A feature estende o modelo `Order` existente com dois campos: um novo status `OPEN` (comanda em aberto) e um campo `table_label` (identificador textual livre como "Mesa 3"). Com isso, o sistema de comandas reutiliza toda a infraestrutura já existente — `TenantManager`, `OrderItem`, `create_pix_payment`, dashboard de pedidos — sem introduzir um novo modelo.

Seis novas views são adicionadas em `core/views.py` sob o prefixo `/dashboard/comandas/`, seguindo o mesmo padrão das views de manager já existentes (`user_can_manage_store` + `@login_required`). A interatividade de adicionar e remover itens usa HTMX com partial template, exatamente como o `update_order_status` e o modal de detalhes já fazem.

Para fechar a comanda via PIX, a view reutiliza diretamente `core/payment.create_pix_payment` — nenhuma mudança no módulo de pagamento.

As correções de navegação são três edições cirúrgicas de template: `base.html` (header), `base_account.html` (sidebar de conta) e `base_manager.html` (sidebar do painel + mobile off-canvas).

Uma migration Django adiciona `table_label` como `CharField` e registra `OPEN` no campo `status` (sem constraint DB, apenas a nível de choices).

## 2. Princípios aplicados

> `principles.md` não existe neste projeto. Seção mantida como registro.

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| Multi-tenancy via TenantManager | Todas as queries de comanda passam pelo `TenantManager` — isolamento automático | respeita |
| HTMX como padrão de interatividade | Add/remove item usa partial HTMX, sem SPA | respeita |
| Delta mínimo sobre o legado | Nenhum modelo novo, nenhuma dependência nova | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Adicionar `OPEN` ao `Order.Status` TextChoices em vez de criar modelo `Comanda` separado | Reutiliza ORM, TenantManager, OrderItem, dashboard de pedidos e PIX sem duplicar infraestrutura | Modelo `Comanda` separado (mais código, mais risco de dessincronização com o fluxo de Order) | 🟢 |
| D-02 | Adicionar `table_label = CharField(max_length=100, blank=True)` a `Order` | Campo simples, sem FK, texto livre conforme RN-05. Para pedidos não-comanda fica em branco. | FK para modelo `Table` (over-engineering para o escopo atual) | 🟢 |
| D-03 | Fechar comanda presencial: `OPEN → PREPARING` direto, sem PIX | Consistente com o balcão atual (`manager_create_order`). Nenhum código de pagamento acionado. | Novo status `CLOSED_PRESENTIAL` (desnecessário — PREPARING já significa "em produção") | 🟢 |
| D-04 | Fechar comanda via PIX: chamar `create_pix_payment` e mover para `PENDING` | Reutiliza 100% do módulo `core/payment.py` sem modificações. Webhook existente cuida da aprovação. | Novo endpoint de pagamento (over-engineering) | 🟢 |
| D-05 | HTMX para add/remove item: retornar partial `_comanda_items.html` com swap `outerHTML` | Padrão já usado no projeto (`hx-target`, `hx-trigger`). Sem full page reload. | Alpine.js com estado local (introduziria dependência nova) | 🟡 |
| D-06 | `comanda_remove_item` aceita POST (não DELETE) | Django CSRF + forms HTML não suportam DELETE nativamente sem JS; POST com action param é o padrão do projeto | DELETE HTTP via fetch JS (quebra o padrão HTMX do projeto) | 🟢 |
| D-07 | Mobile sidebar em `base_manager.html` via Hyperscript (já carregado em `base.html`) | `hyperscript.org` já está na página via CDN. Zero dependência nova. Toggle off-canvas com `_="on click toggle .hidden on #mobile-sidebar"` | Alpine.js x-show, Tailwind JS plugin | 🟡 |

## 4. Premissas

> Nenhum marcador `[DÚVIDA]` restante no `requirements.md`. Sem premissas não confirmadas.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `Order.Status` | `core/models.py:79-84` | regra-alterada | Novo valor `OPEN = 'OPEN', 'Comanda Aberta'` inserido antes de PENDING |
| `Order` | `core/models.py:78-106` | componente-novo | Novo campo `table_label = CharField(max_length=100, blank=True)` |
| `views.py` (manager) | `core/views.py:184-450` | componente-novo | 6 novas views: `comanda_list`, `comanda_create`, `comanda_detail`, `comanda_add_item`, `comanda_remove_item`, `comanda_close` |
| `core/urls.py` | `core/urls.py:1-30` | contrato-novo | 6 novas rotas sob `/dashboard/comandas/` |
| `base_manager.html` | `templates/core/manager/base_manager.html` | regra-alterada | Item "Comandas" na sidebar + off-canvas mobile |
| `base.html` (header nav) | `templates/base.html:38-42` | regra-alterada | "Meus Pedidos" para `is_staff` aponta para `manager_orders` |
| `base_account.html` (sidebar) | `templates/core/account/base_account.html:44` | regra-alterada | Bloco "Painel de Gerência" condicional `is_staff` |
| `comanda_list.html` | *(novo)* | componente-novo | Template da lista de comandas abertas |
| `comanda_detail.html` | *(novo)* | componente-novo | Template da tela de comanda individual |
| `_comanda_items.html` | *(novo)* | componente-novo | Partial HTMX para a lista de itens + total |
| Migration `0008` | *(novo)* | componente-novo | Adiciona `table_label` e registra `OPEN` no histórico de migrações |

## 6. Delta no modelo de dados

- Resumo das mudanças: 1 campo novo em `Order`, 1 valor novo em `Status` TextChoices, 1 migration.
- Detalhe completo em: `_reversa_forward/004-painel-restaurante/data-delta.md`

## 7. Delta de contratos externos

> Nenhum contrato externo novo. O fechamento via PIX reutiliza a integração MercadoPago existente (`core/payment.py`) sem modificações. O webhook de aprovação (`api.py`) já trata `PENDING → PREPARING` e continuará funcionando normalmente para comandas fechadas via PIX.

## 8. Plano de migração

1. Editar `core/models.py`: inserir `OPEN` em `Status` e adicionar campo `table_label`
2. Gerar migration: `python manage.py makemigrations core`
3. Aplicar migration: `python manage.py migrate`
4. Adicionar 6 views em `core/views.py`
5. Adicionar 6 rotas em `core/urls.py`
6. Criar templates: `comanda_list.html`, `comanda_detail.html`, `_comanda_items.html`
7. Editar `base_manager.html`: item "Comandas" + mobile sidebar
8. Editar `base.html`: link "Meus Pedidos" condicional para `is_staff`
9. Editar `base_account.html`: bloco "Painel de Gerência" para `is_staff`
10. Teste manual seguindo `onboarding.md`

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| `update_order_status` aceita qualquer status — manager poderia mover um pedido normal de volta para `OPEN` | Médio | Baixo | A view `update_order_status` usa dropdown com valores do `Status.choices` — `OPEN` não deve aparecer nas opções do formulário de atualização de status no dashboard de pedidos |
| Comanda com zero itens sendo fechada via PIX geraria pagamento de R$ 0,00 | Médio | Baixo | `comanda_close` valida que `order.total_amount > 0` antes de chamar `create_pix_payment`; exibe erro se total for zero |
| `table_label` em branco em comandas (campo opcional) dificulta identificação na lista | Baixo | Médio | `comanda_create` valida que o campo não seja vazio antes de criar; label é obrigatório apenas para comandas |
| Webhook aprova comanda fechada via PIX corretamente? | Médio | Baixo | Sim — comanda PIX vira `PENDING` (mesmo que checkout online). Webhook já trata `PENDING → PREPARING`. Nenhuma mudança necessária. |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Cenários do `onboarding.md` testados manualmente (criar comanda, adicionar item, remover item, fechar presencial, fechar PIX)
- [ ] Regressão: cliente sem `is_staff` não vê "Painel de Gerência" na sidebar de conta
- [ ] Regressão: link "Meus Pedidos" do header continua levando clientes para `/account/orders/`

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-27 | Versão inicial gerada por `/reversa-plan` | reversa |
