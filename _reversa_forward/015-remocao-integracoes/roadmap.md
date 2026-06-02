# Roadmap: Remoção de Integrações Desnecessárias

> Identificador: `015-remocao-integracoes`
> Data: `2026-06-01`
> Requirements: `_reversa_forward/015-remocao-integracoes/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A feature é uma **remoção cirúrgica em duas frentes independentes**: Uber Direct e Google OAuth/allauth. As frentes são independentes entre si e podem ser executadas em qualquer ordem, mas cada uma segue a mesma sequência interna: modelo de dados → lógica de negócio → templates → testes → settings.

**Frente A — Uber Direct:** remover `core/uber_direct.py`, os três modelos (`UberDirectConfig`, `UberDirectDelivery`, `UberDirectDeliveryEvent`), o campo `uber_quote_id` de `Order`, o webhook FastAPI, a task Celery `process_uber_webhook`, os campos no formulário de configurações e simplificar o cálculo de taxa no `checkout()` para usar apenas a taxa estática.

**Frente B — Google OAuth/allauth:** remover o pacote `django-allauth[socialaccount]` e suas dependências (incluindo `django.contrib.sites` e `SITE_ID`), criar `accounts/backends.py` com `EmailAuthBackend` que formaliza o workaround já existente em `accounts/views.py:302` (lookup email→username antes de autenticar), remover a rota `/accounts/` do URL root, limpar o botão Google dos templates de auth mantendo o modal.

**Dependência crítica identificada:** `accounts/views.py` já possui lógica de email→username lookup (`User.objects.get(email=email)` → `authenticate(username=u.username)`). Essa lógica é extraída para `EmailAuthBackend`, tornando o backend customizado trivial de implementar. 🟢

**httpx:** o pacote foi adicionado exclusivamente para o Uber Direct (feat 009). Será removido de `requirements.txt` após confirmar ausência de outros usos. 🟡

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Utilidade antes de completude | Remove código sem uso real pelo cliente (motoboy próprio, sem Google login em uso) | respeita |
| II. Integrações essenciais apenas | Remove duas integrações externas não essenciais; mantém MercadoPago (essencial) | respeita |
| III. Configuração simples, operação autônoma | Elimina 6 variáveis de ambiente opcionais (UBER_*, GOOGLE_*) e SITE_ID | respeita |
| IV. Produto focado, não showcase | Reverte para auth por email/senha simples; taxa de entrega estática | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Criar `accounts/backends.py` com `EmailAuthBackend` | `ModelBackend` padrão autentica por username; o workaround de email→username já existe em `accounts/views.py:302` — formalizar é trivial | Manter allauth sem social provider (manteria tabelas e rotas desnecessárias) | 🟢 |
| D-02 | Remover `httpx` de `requirements.txt` | Adicionado exclusivamente para Uber Direct (feat 009, `dependencies.md`); verificar ausência de outros usos antes de remover | Manter httpx (deixa dependência morta) | 🟡 |
| D-03 | Remover `django.contrib.sites` e `SITE_ID` junto com allauth | `SITE_ID = 1` é obrigatório para allauth (`code-analysis.md#1.2`); sem allauth, a app `sites` não tem uso no projeto | Manter sites (acúmulo desnecessário) | 🟢 |
| D-04 | Manter o modal de auth no checkout (`auth_modal.html`) | UX de autenticar sem sair da página do checkout tem valor independente do Google; remover seria regressão de UX desnecessária | Remover modal e redirecionar para /auth/login/ (regressão UX) | 🟢 |
| D-05 | Remover `uber_quote_id` de `Order` com migration | Campo sem mais uso após remoção do Uber Direct; manter seria schema morto | Manter como nullable (campo morto com custo de schema) | 🟢 |
| D-06 | Remover task Celery `process_uber_webhook` | Sem webhook Uber, a task nunca será disparada; manter seria código morto | Manter com log de deprecação (complexidade sem benefício) | 🟢 |

## 4. Premissas

Nenhuma premissa de `[DÚVIDA]` não resolvida. Todas as dúvidas foram esclarecidas em `/reversa-clarify`.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `core/uber_direct.py` | `_reversa_sdd/inventory.md#core` | componente-extinto | Arquivo removido inteiramente |
| `UberDirectConfig`, `UberDirectDelivery`, `UberDirectDeliveryEvent` | `_reversa_sdd/code-analysis.md#2.6` | componente-extinto | 3 modelos e respectivas tabelas removidos |
| `Order.uber_quote_id` | `_reversa_sdd/code-analysis.md#checkout` | regra-alterada | Campo removido do modelo; checkout não grava mais uber_quote_id |
| `core/tasks.py` → `process_uber_webhook` | `_reversa_sdd/code-analysis.md#2.8` | componente-extinto | Task Celery removida |
| `core/api.py` → webhook Uber | `_reversa_sdd/code-analysis.md#2.7` | contrato-removido | Endpoint `/api/webhooks/uber` removido |
| `core/context_processors.py` | `_reversa_sdd/code-analysis.md#context` | regra-alterada | Lógica de cálculo de taxa simplificada; remove branch Uber Direct |
| `core/views.py` → `checkout()` | `_reversa_sdd/code-analysis.md#checkout` | regra-alterada | Remove lógica de quote Uber; sempre usa taxa estática |
| `core/forms.py` → `StoreSettingsForm` | `_reversa_sdd/inventory.md#core` | regra-alterada | Remove campos de configuração Uber Direct |
| `django-allauth[socialaccount]` | `_reversa_sdd/dependencies.md` | componente-extinto | Pacote removido de requirements.txt e INSTALLED_APPS |
| `AUTHENTICATION_BACKENDS` | `_reversa_sdd/code-analysis.md#1.2` | regra-alterada | Remove `allauth.AuthenticationBackend`; adiciona `accounts.backends.EmailAuthBackend` |
| `accounts/backends.py` | — | componente-novo | Backend customizado de email auth (novo arquivo) |
| `store_saas/urls.py` → `/accounts/` | `_reversa_sdd/code-analysis.md#1.3` | contrato-removido | Rota allauth removida |
| Templates de auth | `_reversa_sdd/inventory.md#templates` | regra-alterada | Botão Google removido; modal mantido com email/senha |
| `store_saas/settings.py` | `_reversa_sdd/code-analysis.md#1.2` | regra-alterada | Remove SITE_ID, ACCOUNT_LOGIN_METHODS, ACCOUNT_SIGNUP_FIELDS, UBER_SANDBOX, UBER_* |

## 6. Delta no modelo de dados

- **Removidos:** 3 modelos Uber Direct (4 tabelas incluindo M2M se houver), 1 campo `uber_quote_id` em `Order`, 6+ tabelas allauth (`account_*`, `socialaccount_*`)
- **Nenhum modelo novo**
- Detalhe completo em: `_reversa_forward/015-remocao-integracoes/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Mudança |
|----------|------|---------|
| `POST /api/webhooks/uber` | HTTP (recebe) | Removido — deixa de existir |
| `GET /accounts/google/login/` | HTTP (redireciona) | Removido — passa a retornar 404 |
| Uber Direct API (`sandbox-api.uber.com`) | HTTP (chama) | Integração encerrada — sem chamadas saindo do sistema |

Nenhum contrato novo. Não há `interfaces/` nessa feature.

## 8. Plano de migração

1. Criar migration de remoção dos 3 modelos Uber Direct e do campo `uber_quote_id` em `Order`
2. Criar migration de remoção das apps allauth (`allauth`, `allauth.account`, `allauth.socialaccount`) — isso remove automaticamente as tabelas `account_*` e `socialaccount_*`
3. Executar `python manage.py migrate` em dev para validar
4. Remover `django-allauth[socialaccount]` e (se sem outros usos) `httpx` de `requirements.txt`
5. Deploy em produção: rodar `migrate` antes de reiniciar o processo (janela de downtime mínima — apenas `ALTER TABLE` e `DROP TABLE`)

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| `httpx` usado em outro lugar além do Uber Direct | Médio (erro de import em runtime) | Baixo (dependencies.md registra como NOVO feat 009) | Buscar `import httpx` e `from httpx` em todo o projeto antes de remover |
| Usuários com conta vinculada ao Google perdem acesso | Alto (impossível logar) | Baixo (cliente único, poucos usuários, sem uso real do Google login) | Garantir que esses usuários tenham senha definida antes do deploy, ou resetar senha |
| `django.contrib.sites` usado por outro pacote além do allauth | Médio (erro de import ou referência quebrada) | Baixo | Buscar `from django.contrib.sites` no código antes de remover |
| Migration allauth falha se houver dados em `socialaccount_*` | Baixo (só impede migrate) | Baixo | Rodar `python manage.py shell` e limpar dados antes, ou usar `--fake` para tabelas já vazias |

## 10. Critério de pronto

- [ ] `python manage.py migrate` executa sem erro em banco limpo e em banco existente
- [ ] `python manage.py runserver` (ou uvicorn) sobe sem `ImportError`
- [ ] Login por email/senha funciona no modal do checkout
- [ ] Checkout calcula e exibe taxa estática corretamente
- [ ] Painel de configurações não exibe campos Uber Direct
- [ ] `GET /accounts/google/login/` retorna 404
- [ ] Suite de testes passa sem erros
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-01 | Versão inicial gerada por `/reversa-plan` | reversa |
