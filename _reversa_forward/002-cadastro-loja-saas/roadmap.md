# Roadmap: Cadastro de Loja SaaS (Auto-onboarding)

> Identificador: `002-cadastro-loja-saas`
> Data: `2026-05-26`
> Requirements: `_reversa_forward/002-cadastro-loja-saas/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A feature se divide em três frentes sequenciais, todas no stack Django existente, sem novas dependências e sem tocar endpoints FastAPI.

**Frente 1 — Modelo de dados:** adicionar `owner = OneToOneField(User, null=True)` em `core/models.py:Store`. Uma migration simples que não altera nenhuma outra tabela e mantém lojas existentes com `owner=NULL`.

**Frente 2 — Auto-onboarding:** novo arquivo `accounts/forms.py` com `StoreRegistrationForm` estendendo `UserCreationForm` com campos `store_name` e `subdomain` (validados por regex + lista de reservados). Nova view `criar_loja_view` em `accounts/views.py` cria `User` + `Store` em bloco atômico, autentica automaticamente e redireciona para `/dashboard/`. Rota `/criar-loja/` adicionada em `accounts/urls.py`. Novo template `templates/accounts/criar_loja.html`.

**Frente 3 — Login inteligente + dashboard por ownership:** `login_view` em `accounts/views.py` recebe bloco pós-autenticação que verifica `getattr(user, 'owned_store', None)` — se existir, redireciona para `/dashboard/`. Todas as 9 verificações `if not request.user.is_staff` nas views do dashboard em `core/views.py` são substituídas por chamada a um helper central `user_can_manage_store(request)` que avalia `is_staff OR (tenant existe AND user == tenant.owner)`. Template `templates/accounts/login.html` recebe link "Crie sua loja".

Nenhum endpoint FastAPI é alterado. Zero dependências novas.

---

## 2. Princípios aplicados

> Arquivo `.reversa/principles.md` não encontrado — nenhum princípio registrado para este projeto.

---

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | `owner` como `OneToOneField(null=True)` em `Store` | Unicidade 1-para-1 garantida no banco; `null=True` preserva lojas existentes sem dono | ForeignKey (permite múltiplas lojas — rejeitado pelo requirements); UserProfile separado (tabela extra desnecessária) | 🟢 |
| D-02 | `on_delete=SET_NULL` no campo `owner` | Se o usuário dono for deletado, a loja sobrevive e pode ser reatribuída via admin; CASCADE apagaria toda a loja | CASCADE (risco de perda de dados da loja) | 🟢 |
| D-03 | `StoreRegistrationForm` em novo `accounts/forms.py` | Coesão com módulo de autenticação; `core/forms.py` já concentra formulários de gestão da loja operando no contexto de tenant | Adicionar em `core/forms.py` (misturaria contextos distintos) | 🟢 |
| D-04 | Helper `user_can_manage_store(request)` em `core/views.py` | Centraliza autorização de dashboard em um ponto; elimina duplicação em 9 views; fácil de auditar | Decorator customizado (overhead para MVP); grupos Django (requer configuração não existente no legado) | 🟢 |
| D-05 | `getattr(user, 'owned_store', None)` no `login_view` | `OneToOneField` reverso levanta `RelatedObjectDoesNotExist` — não retorna None — se acessado diretamente em user sem loja | `try/except RelatedObjectDoesNotExist` (verboso); campo booleano no User (redundante) | 🟡 |
| D-06 | Validação de subdomínio via `clean_subdomain()` no form + `RegexValidator` | Feedback no formulário antes do save; lista de reservados extensível sem migration | Só no model (feedback tardio, sem mensagem clara no form) | 🟢 |

---

## 4. Premissas

> Nenhuma premissa adotada a partir de `[DÚVIDA]` — todas as dúvidas foram resolvidas em `/reversa-clarify` em 2026-05-26.

---

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `Store` (model) | `_reversa_sdd/code-analysis.md#Módulo 2` → `core/models.py` | regra-alterada | Campo `owner` OneToOneField adicionado (null=True) |
| `accounts` — forms | — (arquivo novo) | componente-novo | `accounts/forms.py` com `StoreRegistrationForm` |
| `accounts` — views | `_reversa_sdd/code-analysis.md#Módulo 3` → `accounts/views.py` | regra-alterada | `criar_loja_view` nova + `login_view` alterado (redirect pós-login) |
| `accounts` — urls | `accounts/urls.py` | contrato-alterado | Rota `/criar-loja/` adicionada |
| `core/views.py` — dashboard (9 views) | `_reversa_sdd/permissions.md#views` → `core/views.py` | regra-alterada | Guard `is_staff` substituído por `user_can_manage_store()` |
| Template `login.html` | `templates/accounts/login.html` | contrato-alterado | Link "Crie sua loja" adicionado |
| Template `criar_loja.html` | — (arquivo novo) | componente-novo | Tela de cadastro de loja |

---

## 6. Delta no modelo de dados

- Campo `owner` (`OneToOneField → auth.User`, `null=True`, `blank=True`, `related_name='owned_store'`, `on_delete=SET_NULL`) adicionado ao model `Store`
- Uma migration nova: `core/migrations/0007_store_owner.py`
- Detalhe completo em: `_reversa_forward/002-cadastro-loja-saas/data-delta.md`

---

## 7. Delta de contratos externos

> Nenhum contrato externo afetado. A feature adiciona apenas views Django (HTML/formulário) e não cria nem modifica endpoints FastAPI.

---

## 8. Plano de migração

1. Aplicar a nova migration (`python manage.py migrate`) — adiciona coluna `owner_id` nullable em `core_store` sem lock prolongado
2. Lojas existentes ficam com `owner_id=NULL`; acesso ao dashboard dessas lojas permanece via `is_staff` (garantido pelo OR no helper)
3. Nenhum backfill necessário — política definida em `requirements.md` §9

---

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Acesso direto a `user.owned_store` sem `getattr` levanta exceção em vez de None | Médio — erro 500 no login_view | Médio | Usar `getattr(user, 'owned_store', None)` em todos os pontos de acesso | 
| Dashboard de loja sem `owner` torna-se inacessível se `is_staff` não for preservado no helper | Alto — regressão de acesso para lojas existentes | Baixo | Helper inclui `OR is_staff`; coberto pelo cenário Gherkin RF-06 |
| Subdomínio conflitando com rota Django existente (ex: `catalog`, `checkout`, `cart`) | Médio — URL ambígua, comportamento imprevisível | Baixo | Lista de reservados expandida para incluir slugs de rotas do sistema |
| Usuário já autenticado acessa `/criar-loja/` | Baixo — cria segunda conta sem loja ou sobrescreve sessão | Médio | Redirecionar para `/` se `request.user.is_authenticated` no início da view |

---

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Migration aplicada sem erro em banco limpo e em banco com dados existentes
- [ ] Criação de loja via `/criar-loja/` resulta em User + Store criados + redirect para `/dashboard/`
- [ ] Login de dono de loja redireciona para `/dashboard/`; login de cliente vai para `/`
- [ ] Dashboard acessível para dono sem `is_staff`
- [ ] Dashboard inacessível para cliente sem ownership e sem `is_staff`
- [ ] Superuser com `is_staff` acessa dashboard normalmente
- [ ] `regression-watch.md` gerado

---

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-26 | Versão inicial gerada por `/reversa-plan` | reversa |
