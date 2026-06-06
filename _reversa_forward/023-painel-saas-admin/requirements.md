# Requirements: Painel SaaS Admin

> Identificador: `023-painel-saas-admin`
> Data: `2026-06-05`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Criar uma área administrativa exclusiva para o superusuário do sistema SaaS acessível em `/saas/`, separada do dashboard do lojista (`/dashboard/`) e do Django Admin (`/admin/`). O painel oferece visão global de todos os tenants (lojas), métricas agregadas por loja, e ações de gestão (ativar/desativar, criar loja, impersonar contexto). Resolve a ausência de uma interface de controle cross-tenant após a remoção do formulário `criar_loja.html` (feature 021) e o fato de que o superusuário hoje só gerencia tenants via `/admin/`, que tem limitações de contexto em localhost.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/architecture.md#Domínio de Negócio` | `Store` é a unidade de tenant; identificada por `subdomain`; `is_active` controla disponibilidade | 🟢 |
| `_reversa_sdd/permissions.md#Papéis Identificados` | Superuser = `is_superuser=True`; único papel com acesso cross-tenant no Django Admin | 🟢 |
| `_reversa_sdd/permissions.md#Controle de Acesso no Admin Django` | `StoreAdmin` sem filtro de tenant; `TenantAdmin` filtra pelo ContextVar — superuser sem header vê tudo | 🟡 |
| `_reversa_sdd/code-analysis.md#2.1 Multi-tenancy` | `TenantManager.get_queryset()` retorna queryset sem filtro quando `get_current_tenant()` retorna `None` | 🟢 |
| `_reversa_sdd/architecture.md#Padrões Arquiteturais` | Roteamento ASGI: Django serve paths sem `/api`; nova área `/saas/` entra no Django normalmente | 🟢 |
| `_reversa_sdd/domain.md#Glossário` | `TenantAwareModel.save()` preenche `store` do ContextVar — criação de loja não pode ter tenant ativo | 🟢 |
| `_reversa_sdd/permissions.md#Matriz de Permissões — Views Django` | Não existe rota `/saas/` — a criação é net-new | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| **Pablo (Superuser / Dono do SaaS)** | Monitorar todas as lojas cadastradas e agir sobre elas sem abrir o Django Admin | Acessa `/saas/`, vê lista com métricas de todas as lojas, desativa uma loja inadimplente com um clique |
| **Pablo (Superuser / Dono do SaaS)** | Cadastrar um novo cliente no SaaS após a remoção do formulário público `criar_loja` | Acessa `/saas/lojas/nova/`, cria Store + usuário Manager associado |
| **Pablo (Superuser / Dono do SaaS)** | Investigar um problema em loja específica | Acessa detalhe da loja, vê últimos pedidos e configurações sem precisar trocar de contexto |

## 4. Regras de negócio novas ou alteradas

1. **RN-SaaS-01:** O acesso a qualquer rota `/saas/*` requer `request.user.is_superuser == True`. Usuários com apenas `is_staff=True` são redirecionados para `/dashboard/`. Usuários não autenticados são redirecionados para `/login/`. 🟢
   - Origem no legado: `_reversa_sdd/permissions.md#Papéis Identificados`
   - Tipo: nova

2. **RN-SaaS-02:** As views do painel SaaS consultam dados cross-tenant explicitamente usando `Store.objects.all()` e querysets sem filtro de tenant (ContextVar `None` ou bypass explícito). Nenhuma view do painel SaaS chama `set_current_tenant()`, evitando contaminação de contexto. 🟢
   - Origem no legado: `_reversa_sdd/code-analysis.md#2.1 Multi-tenancy`
   - Tipo: nova

3. **RN-SaaS-03:** A criação de nova loja pelo painel SaaS cria simultaneamente: (a) um registro `Store` com `subdomain` único e `is_active=True`, e (b) um `User` com `is_staff=True` vinculado como `owner` da loja. O `store_id` é atribuído explicitamente — não via `TenantAwareModel.save()` — pois não há tenant ativo no contexto da criação. 🟡
   - Origem no legado: `_reversa_sdd/domain.md#RN-03` (auto-atribuição de tenant em save — comportamento que deve ser contornado aqui)
   - Tipo: nova

4. **RN-SaaS-04:** Desativar uma loja (`is_active=False`) impede a resolução do tenant pelo `TenantMiddleware` (que filtra `is_active=True`), tornando a loja inacessível a clientes imediatamente. A ação é reversível pelo painel. 🟡
   - Origem no legado: `_reversa_sdd/domain.md#RN-02` (resolução de tenant usa `is_active=True`)
   - Tipo: nova

5. **RN-SaaS-05:** As métricas exibidas por loja são calculadas em tempo real via agregação SQL (`Count`, `annotate`) na listagem. Sem cache. Justificativa: o projeto opera com dezenas de lojas; uma query com `annotate` em PostgreSQL sobre centenas de registros é sub-milissegundo. Cache só se justifica acima de 500 lojas ativas — revisitar nesse momento. 🟢
   - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Listagem global de lojas em `/saas/` com colunas: nome, subdomínio, status (ativa/inativa), contagem de pedidos totais, pedidos hoje, data de criação | Must | Página carrega com todas as lojas; contador de pedidos hoje usa `timezone.localdate()` (padrão da feature 020) | 🟢 |
| RF-02 | Ativar/desativar loja com botão na listagem (toggle `is_active`) sem sair da página | Must | Após o toggle, o status visual muda imediatamente; acessar a loja pelo subdomínio reflete o novo estado | 🟢 |
| RF-03 | Página de detalhe de loja em `/saas/lojas/<id>/` com: dados cadastrais, owner, token MP (mascarado), taxa de entrega, últimos 10 pedidos | Should | Dados exibidos correspondem ao banco; token MP exibido como `TEST-****...****` | 🟡 |
| RF-04 | Formulário de criação de nova loja em `/saas/lojas/nova/` criando `Store` + `User` Manager simultaneamente | Must | Após submit válido, loja aparece na listagem; o Manager consegue acessar `/dashboard/` com as credenciais criadas | 🟡 |
| RF-05 | Proteção de rota: qualquer acesso a `/saas/*` sem `is_superuser` resulta em redirect (não 403) | Must | Usuário com `is_staff=True` e sem `is_superuser` é redirecionado para `/dashboard/`; anônimo para `/login/` | 🟢 |
| RF-06 | Contador de lojas ativas e inativas no topo da listagem | Should | Os números somam o total de registros `Store` no banco | 🟡 |
| RF-07 | **Fora de escopo desta feature.** Impersonação de tenant foi descartada: risco de ação acidental em nome do lojista, complexidade de sessão não justificada no volume atual. Substituto: botão "Ver loja" abre o subdomínio público da loja em nova aba | Could | Botão presente na listagem; abre `http://<subdomain>.dominio/` em nova aba | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Segurança | Nenhuma rota `/saas/*` acessível sem `is_superuser`; falha silenciosa (redirect) não expõe a existência do painel | `_reversa_sdd/permissions.md#Papéis Identificados` | 🟢 |
| Segurança | Token MercadoPago nunca exibido em claro no HTML; mascarar como `****` exceto últimos 4 chars | `_reversa_sdd/architecture.md#Integrações Externas` | 🟢 |
| Consistência visual | O painel SaaS usa o mesmo `dashboard_base.html` como base, com sidebar/header adaptados para indicar o contexto SaaS (não confundir com o dashboard do lojista) | `_reversa_sdd/code-analysis.md#2.8 Templates` | 🟡 |
| Isolamento | As views SaaS não chamam `set_current_tenant()` — consultas são globais e explícitas; nenhum dado de cliente de loja vaza para outro contexto | `_reversa_sdd/architecture.md#Isolamento Multi-Tenant via ContextVar` | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Superuser acessa listagem de lojas
  Dado que estou autenticado como superuser
  Quando acesso "/saas/"
  Então vejo uma tabela com todas as lojas cadastradas
  E cada linha exibe nome, subdomínio, status, pedidos totais e pedidos hoje

Cenário: Superuser desativa uma loja
  Dado que estou na listagem "/saas/"
  E existe uma loja ativa chamada "pizzapablo"
  Quando clico no toggle de status da loja "pizzapablo"
  Então o status da loja muda para "inativa" na listagem
  E ao acessar o subdomínio "pizzapablo" um cliente recebe 404

Cenário: Superuser cria nova loja
  Dado que estou em "/saas/lojas/nova/"
  Quando preencho nome "Burger King", subdomínio "burgerking", email do manager "bk@email.com", senha
  E submeto o formulário
  Então sou redirecionado para "/saas/"
  E "burgerking" aparece na listagem como ativa
  E fazer login com as credenciais criadas e acessar "/dashboard/" funciona

Cenário: Staff sem superuser tenta acessar painel SaaS
  Dado que estou autenticado com is_staff=True e is_superuser=False
  Quando acesso "/saas/"
  Então sou redirecionado para "/dashboard/"
  E não vejo nenhuma mensagem de erro expondo a existência do painel

Cenário: Anônimo tenta acessar painel SaaS
  Dado que não estou autenticado
  Quando acesso "/saas/"
  Então sou redirecionado para "/login/"
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 — Listagem global | Must | Visibilidade mínima do SaaS — sem isso não há gestão possível |
| RF-02 — Toggle ativo/inativo | Must | Ação operacional crítica: desligar loja inadimplente ou com problema |
| RF-04 — Criar nova loja | Must | Formulário público foi removido na feature 021; única forma de onboarding |
| RF-05 — Proteção de rota | Must | Requisito de segurança não negociável |
| RF-03 — Detalhe da loja | Should | Útil para suporte, mas a listagem já cobre o caso primário |
| RF-06 — Contadores no topo | Should | UX de conveniência, baixo custo de implementação |
| RF-07 — Impersonar loja | Could | Útil mas requer cuidado com segurança de sessão |

## 9. Esclarecimentos

| # | Dúvida original | Decisão | Data |
|---|----------------|---------|------|
| D-01 | RF-07: impersonação — escopo e mecânica não definidos | Descartada desta feature. Risco de ação acidental supera o benefício. Substituto: botão "Ver loja" em nova aba. Impersonação pode ser feature separada futura. | 2026-06-05 |
| D-02 | RN-SaaS-05: cache de métricas — threshold não definido | Sem cache. Agregação SQL em tempo real é suficiente até ~500 lojas ativas. Revisar quando esse volume for atingido. | 2026-06-05 |

## 10. Lacunas

> Nenhuma lacuna aberta. Todas as dúvidas resolvidas na seção 9.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-05 | Versão inicial gerada por `/reversa-requirements` | reversa |
