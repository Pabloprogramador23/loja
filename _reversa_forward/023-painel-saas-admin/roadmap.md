# Roadmap: Painel SaaS Admin

> Identificador: `023-painel-saas-admin`
> Data: `2026-06-05`
> Requirements: `_reversa_forward/023-painel-saas-admin/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A feature é inteiramente aditiva — nenhum arquivo existente precisa ser removido ou ter lógica central alterada. O delta é composto por:

1. **Novo arquivo de views** `core/saas_views.py` com um mixin `SuperuserRequiredMixin` que verifica `is_superuser` e zera o ContextVar de tenant (chamando `set_current_tenant(None)`) antes de qualquer query, anulando o filtro automático do `TenantManager`.
2. **Novo arquivo de URLs** `core/saas_urls.py` montado sob o prefixo `/saas/` em `store_saas/urls.py`.
3. **Novo formulário** `SaasCreateStoreForm` em `core/forms.py` que cria `Store` + `User` Manager atomicamente, atribuindo `store_id` de forma explícita (sem depender do `TenantAwareModel.save()`).
4. **Novos templates** em `templates/core/saas/` estendendo `dashboard_base.html` com indicador visual de "contexto SaaS".

Nenhuma migração de banco é necessária. Todas as métricas são calculadas via `Store.objects.annotate(...)` — consultas que partem do modelo `Store` (que não é `TenantAwareModel`) e portanto nunca passam pelo `TenantManager`.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Utilidade antes de completude | Pablo (dono do SaaS) precisa cadastrar e desativar lojas agora — uso imediato e concreto após remoção de `criar_loja` | respeita |
| II. Integrações essenciais apenas | Nenhuma integração externa nova | respeita |
| III. Configuração simples, operação autônoma | Painel web acessível pelo superusuário sem dependência técnica | respeita |
| IV. Produto focado, não showcase | Abordagem mais simples: mixin + views Django + templates HTMX já presentes no projeto | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Zerар ContextVar de tenant com `set_current_tenant(None)` no `SuperuserRequiredMixin` | `TenantManager.get_queryset()` retorna queryset global quando `get_current_tenant()` retorna `None`. É o único ponto de controle correto. | Criar manager separado `global_objects`; usar `_base_manager` interno do Django; bypass via raw SQL | 🟢 |
| D-02 | Métricas calculadas por `Store.objects.annotate(Count('order'), ...)` | `Store` não herda de `TenantAwareModel` — `Store.objects` é o manager padrão do Django, sem filtro de tenant. Annotations via FK reversa (`order__store`) são JOINs SQL nativos, sem passar pelo `TenantManager`. | Subquery por loja em loop Python (N+1); cache Redis; task Celery de agregação | 🟢 |
| D-03 | `SuperuserRequiredMixin` como class-based (não decorator) | Consistência com o padrão emergente do projeto; facilita reutilização em múltiplas views sem repetição | Decorator funcional `@superuser_required` | 🟡 |
| D-04 | Criação de loja em `transaction.atomic()` criando `User` + `Store` + atribuição de `owner` | `RN-SaaS-03` exige que `store_id` seja atribuído explicitamente, não via `TenantAwareModel.save()`. O `atomic()` garante que nem User nem Store fiquem órfãos em caso de falha. | Criar Store primeiro e User depois sem atomic; usar sinal `post_save` | 🟢 |
| D-05 | Toggle `is_active` via `POST` HTMX sem JavaScript custom | Padrão já estabelecido no projeto (delivery toggle da feature 019 usa HTMX `hx-post`). Toggle retorna HTML parcial com o botão atualizado. | Endpoint JSON + fetch JS; formulário com redirect | 🟢 |
| D-06 | Prefixo `/saas/` montado como include separado em `store_saas/urls.py` | Mantém isolamento de namespace; facilita adicionar rotas SaaS no futuro sem tocar `core/urls.py` | Adicionar diretamente em `core/urls.py` com condição `if is_superuser` | 🟢 |

## 4. Premissas

> Nenhuma premissa de [DÚVIDA] pendente. Todas as dúvidas foram resolvidas antes do plano.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| URL Root | `_reversa_sdd/architecture.md#Padrões Arquiteturais` → `store_saas/urls.py` | contrato-novo | Adicionar `path('saas/', include('core.saas_urls'))` |
| Views Django | `_reversa_sdd/code-analysis.md#2.9 Dashboard Manager` → `core/views.py` | componente-novo | Novo arquivo `core/saas_views.py` com 4 views + 1 mixin |
| Forms | `_reversa_sdd/code-analysis.md#Módulo 2` → `core/forms.py` | componente-novo | `SaasCreateStoreForm` no mesmo arquivo (ou arquivo separado `core/saas_forms.py`) |
| Templates | `_reversa_sdd/architecture.md#Camada de Apresentação` → `templates/` | componente-novo | 4 templates em `templates/core/saas/` |
| Permissions | `_reversa_sdd/permissions.md#Matriz de Permissões` | regra-alterada | Nova entrada para rotas `/saas/*` com verificação `is_superuser` |

## 6. Delta no modelo de dados

Nenhuma migração necessária. O modelo `Store` já possui todos os campos necessários: `name`, `subdomain`, `owner`, `is_active`, `created_at`, `delivery_fee`, `mercadopago_access_token`.

O painel lê e escreve apenas em modelos existentes via queries cross-tenant controladas.

- Resumo das mudanças: nenhum campo novo, nenhuma tabela nova
- Detalhe completo em: `_reversa_forward/023-painel-saas-admin/data-delta.md`

## 7. Delta de contratos externos

Não há contratos externos afetados. O painel SaaS é puramente interno — sem novas chamadas a APIs externas, sem novos webhooks, sem mudanças no contrato da API FastAPI.

## 8. Plano de migração

n/a — nenhuma migration de banco necessária. A feature entra via `python manage.py migrate` sem novas migrações.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| `set_current_tenant(None)` não resetar o ContextVar corretamente se o middleware usar `.set()` com token (não atribuição direta) | Alto — queries vazariam dados cross-tenant | Baixo | Verificar implementação de `set_current_tenant` em `core/middleware.py` antes de codar; usar o token de reset do ContextVar se necessário |
| Subdomínio duplicado no cadastro de nova loja causar IntegrityError sem feedback | Médio — UX ruim | Médio | `SaasCreateStoreForm` valida unicidade de `subdomain` com `Store.objects.filter(subdomain=...).exists()` antes do `save()` |
| Toggle `is_active=False` desativar a loja do próprio superusuário (Pablo) | Alto — bloqueia acesso ao painel | Baixo | Guard na view: não permitir desativar a loja cujo `owner == request.user` |
| Senha do Manager criado pelo painel enviada em claro nos logs do Django | Baixo — ambiente controlado | Baixo | Usar `User.objects.create_user()` (que chama `set_password()`) e não logar o request POST |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Acessar `/saas/` com superuser exibe listagem com todas as lojas e métricas corretas
- [ ] Toggle ativo/inativo funciona e reflete no acesso à loja pelo subdomínio
- [ ] Criar loja pelo formulário gera Store + Manager funcional
- [ ] Acessar `/saas/` com `is_staff=True` e `is_superuser=False` redireciona para `/dashboard/`
- [ ] Nenhum test existente quebrado
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-05 | Versão inicial gerada por `/reversa-plan` | reversa |
