# Roadmap: Modo Escuro (Dark Mode)

> Identificador: `006-dark-mode`
> Data: `2026-05-29`
> Requirements: `_reversa_forward/006-dark-mode/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A loja já usa **Tailwind via CDN** e **HTMX** (`_reversa_sdd/architecture.md#Stack Tecnológica`), com cores claras hardcoded em `templates/base.html`. A abordagem adota a estratégia nativa do Tailwind `darkMode: 'class'`: a classe `dark` no elemento `<html>` ativa as variantes `dark:` aplicadas in-place nas templates do escopo. Um **script de bootstrap inline** no `<head>` resolve o tema antes da primeira pintura (anti-FOUC), na ordem: preferência do usuário logado (renderizada pelo servidor) → `localStorage` → `prefers-color-scheme`. Para persistir a escolha de um usuário **autenticado**, cria-se um modelo novo **`UserSettings`** (OneToOne com `auth.User`), já que o legado usa o `User` padrão do Django sem modelo de perfil. Visitantes **anônimos** persistem só em `localStorage`. Um endpoint Django `POST /set-theme/` grava a preferência do logado. O toggle vai no header do `base.html` (que é estendido por `base_manager.html` e `base_account.html`, cobrindo vitrine + painel + conta) e também no `dashboard_base.html`, que é um layout standalone.

## 2. Princípios aplicados

> `.reversa/principles.md` não existe neste projeto — nenhum princípio formal a verificar. (`setup.json` tem `principles.enabled: true`, mas nenhum princípio foi definido via `/reversa-principles`.)

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| n/a | Nenhum princípio definido | — |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Usar `darkMode: 'class'` configurado inline via `tailwind.config = {...}` logo após o script do Tailwind CDN | É a estratégia nativa do Tailwind e funciona com o Play CDN sem build; alinha com o stack atual sem introduzir toolchain | `darkMode: 'media'` (não permite toggle manual); reescrever CSS à mão; introduzir build PostCSS (fora de escopo) | 🟢 |
| D-02 | Dois pontos de injeção da classe `dark` + bootstrap: `templates/base.html` e `templates/dashboard_base.html` | `base.html` é estendido por `base_manager.html` e `base_account.html` (verificado: `{% extends 'base.html' %}`), cobrindo vitrine, painel e conta; `dashboard_base.html` tem `<html>` próprio | Injetar em cada template (redundante); ignorar `dashboard_base.html` (deixaria buraco claro) | 🟢 |
| D-03 | Criar modelo `UserSettings` (OneToOne `auth.User`) com campo `theme ∈ {system, light, dark}`, default `system` | O legado usa `auth.User` padrão (sem AUTH_USER_MODEL custom em `core/models.py`/`accounts`); não dá para adicionar campo direto. Modelo de settings dedicado é o delta menos invasivo e extensível | Custom User model (migração de alto risco em projeto existente); guardar só em `localStorage` (não segue entre dispositivos — contraria decisão §9) | 🟡 |
| D-04 | Endpoint `POST /set-theme/` (view Django, `@login_required`, CSRF) que grava `UserSettings.theme` e responde 204 | HTMX já envia CSRF (`base.html`); persistência de logado precisa de round-trip; manter no Django (não na API FastAPI) por usar sessão/CSRF/`login_required` | Endpoint na API FastAPI (`/api/*`) — exigiria auth própria, mais atrito; sem endpoint (perderia persistência server-side) | 🟢 |
| D-05 | Script de bootstrap inline no `<head>`, antes do CSS, resolvendo: server-render (logado) → `localStorage` → `prefers-color-scheme` | Evita FOUC (RF-04). Inline e síncrono garante classe aplicada antes da primeira pintura | Resolver via HTMX/após load (causa flash); cookie lido no servidor para anônimo (mais complexo que `localStorage`) | 🟡 |
| D-06 | Context processor expõe a preferência do usuário logado para os templates base renderizarem a classe no `<html>` server-side | Cumpre RF-07 (sem flash para logado) sem depender de JS | Middleware dedicado (overkill); renderizar só via JS (não cumpre RF-07) | 🟡 |
| D-07 | Aplicar variantes `dark:` in-place nas templates do escopo, sem criar templates paralelos | Manutenibilidade (RNF); sem tokens centralizados no legado (`_reversa_sdd/architecture.md#Ausências Notáveis`) | Templates duplicados por tema (dobra manutenção) | 🟢 |

## 4. Premissas

| Premissa | Origem (`requirements.md` seção) | Risco se errada |
|----------|----------------------------------|-----------------|
| Visitantes **anônimos** usam `localStorage` como fallback de persistência (a decisão de "perfil no banco" só cobre logados, mas a vitrine é pública) | §9 Esclarecimentos / RN-03 (🟡 inferido) | Baixo — se o desejado for "anônimo não persiste", basta remover o ramo `localStorage`; nenhuma migração afetada |
| O `dashboard_base.html` ainda está em uso (não é só legado morto) | §5/§6 (template inventory) | Médio — se estiver morto, o esforço de tematizá-lo é desperdiçado, mas não quebra nada |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| Camada de apresentação (templates Django + Tailwind CDN) | `_reversa_sdd/architecture.md#Stack Tecnológica` | regra-alterada | Adiciona `darkMode:'class'`, classe `dark` no `<html>`, toggle no header e variantes `dark:` nas templates do escopo |
| Preferências de usuário (`UserSettings`) | `core/models.py` (legado, `auth.User` padrão) | componente-novo | Novo modelo OneToOne para persistir tema do usuário logado |
| View de troca de tema (`set_theme`) | `core/views.py` / `core/urls.py` (legado) | contrato-novo | Novo endpoint HTTP `POST /set-theme/` (detalhe em `interfaces/set-theme.md`) |
| Context processor de tema | `store_saas/settings.py` (`TEMPLATES.OPTIONS.context_processors`) | componente-novo | Expõe preferência do logado para render server-side da classe |

## 6. Delta no modelo de dados

- Resumo das mudanças: **novo modelo** `UserSettings` (OneToOne com `auth.User`, campo `theme` CharField com choices `system|light|dark`, default `system`). Uma migração nova. Nenhum campo removido ou alterado no legado. Não é `TenantAwareModel` — a preferência é por usuário, não por loja.
- Detalhe completo em: `_reversa_forward/006-dark-mode/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| `set-theme` | HTTP (first-party, consumido pelo browser via HTMX/fetch) | `_reversa_forward/006-dark-mode/interfaces/set-theme.md` |

## 8. Plano de migração

1. Definir `UserSettings` em um app apropriado (`core/models.py` ou novo `accounts/models.py` — decisão de implementação no `/reversa-to-do`).
2. `python manage.py makemigrations` → gera a migração do novo modelo.
3. `python manage.py migrate` (dev SQLite; prod PostgreSQL).
4. Sem backfill: ausência de `UserSettings` para um usuário equivale ao default `system` (o código deve tratar `getattr`/`get_or_create` defensivamente).
5. Nenhuma migração de dados destrutiva; a feature é aditiva.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| **Tailwind via CDN é "Dev Only"** — em produção não há purge/build, e variantes `dark:` extras crescem o CSS em runtime | médio | alto | Já é dívida técnica do legado (`_reversa_sdd/deployment.md`); a feature não piora a estratégia, mas registrar que um build Tailwind seria o ideal futuro |
| FOUC (flash do tema errado) ao recarregar | médio | médio | Script de bootstrap inline e síncrono no `<head>` (D-05) + render server-side para logado (D-06) |
| Superfície grande de templates a tematizar (vitrine + painel ≈ 30+ arquivos) | médio | alto | Priorizar `base.html` e telas mais visíveis; tratar parciais HTMX (que trocam fragmentos) para não voltarem claras num swap |
| Parciais carregadas via HTMX herdarem cor clara após swap | médio | médio | Garantir que as parciais (`partials/*`, `manager/partials/*`) também usem variantes `dark:`, pois o swap não recarrega o `<html>` |
| `dashboard_base.html` ser código morto | baixo | médio | Confirmar uso antes de tematizar (premissa §4); custo isolado |
| Contraste insuficiente no escuro (acessibilidade) | médio | médio | Seguir paleta `dark:` consistente (ex.: `dark:bg-gray-900 dark:text-gray-100`) e revisar telas-chave |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Re-extração reversa executada e sem regressão vermelha (recomendado, não obrigatório)
- [ ] Toggle alterna tema sem reload em vitrine e painel do gestor
- [ ] Preferência de logado persiste entre navegadores; de anônimo persiste no mesmo navegador
- [ ] Sem FOUC perceptível ao recarregar com tema escuro salvo

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-29 | Versão inicial gerada por `/reversa-plan` | reversa |
