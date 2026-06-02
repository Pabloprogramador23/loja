# Legacy Impact — Modo Escuro (Dark Mode)

> Identificador: `006-dark-mode`
> Data: `2026-05-29`
> Gerado por: `/reversa-coding`

## Resumo

Feature **puramente aditiva**. Introduz um novo modelo (`UserSettings`), um novo endpoint (`POST /set-theme/`), um novo context processor (`theme_preference`) e variantes visuais `dark:` em ~30 templates. **Nenhuma regra de negócio 🟢 CONFIRMADA do legado foi alterada ou removida** — apenas apresentação (CSS) e um novo eixo de preferência por usuário. Sem alteração de schema em tabelas existentes, sem mudança de contrato em integrações externas (MercadoPago intacto).

## Tabela de impacto

| Arquivo afetado | Componente (architecture.md) | Tipo | Severidade | Justificativa |
|-----------------|------------------------------|------|------------|---------------|
| `core/models.py` | Camada de Domínio / Modelos | `componente-novo` | LOW | Adiciona `UserSettings` (OneToOne com `auth.User`); não toca em `TenantAwareModel` nem nos modelos existentes. |
| `core/migrations/0009_usersettings.py` | Persistência (PostgreSQL) | `delta-de-dados` | LOW | `CreateModel` de tabela nova. Nenhuma migração destrutiva; tabelas existentes inalteradas. |
| `core/context_processors.py` | Camada de Apresentação | `componente-novo` | LOW | Novo `theme_preference`; `cart` preservado. Leitura defensiva (anônimo/sem registro → `system`). |
| `store_saas/settings.py` | Configuração | `regra-nova` | LOW | Registra o novo context processor em `TEMPLATES`. Lista anterior preservada. |
| `core/views.py` | Camada de Aplicação (Django views) | `componente-novo` | LOW | Nova view `set_theme` (`@login_required`, `@require_POST`, 204). Views existentes inalteradas. |
| `core/urls.py` | Roteamento Django | `regra-nova` | LOW | Nova rota `set-theme/`. Rotas existentes inalteradas. |
| `core/tests.py` | Testes | `componente-novo` | LOW | 8 testes novos (modelo + endpoint). Testes de tenant preservados. |
| `templates/base.html`, `dashboard_base.html` | Layouts base | `regra-nova` | MEDIUM | Config `darkMode:'class'`, bootstrap anti-FOUC, toggle e classe server-side. Estrutura e blocos preservados. |
| ~28 templates de conteúdo/parciais | Camada de Apresentação | `regra-alterada` (apenas visual) | LOW | Apenas adição de utilitários `dark:`. Nenhuma lógica de template (condicionais, `{% url %}`, dados) modificada. |

## Diff conceitual por componente

### Preferências de Usuário (novo)
Introduz a noção de preferência de apresentação persistida por usuário autenticado. Antes do legado não havia nenhum modelo de perfil/preferências (`accounts/models.py` inexistia). `UserSettings` é **global por usuário** (deliberadamente **não** `TenantAwareModel`): a escolha de tema acompanha a pessoa entre lojas. Visitantes anônimos persistem só em `localStorage` (sem chamada ao backend).

### Endpoint `POST /set-theme/` (novo)
Contrato first-party consumido pelo browser (HTMX/fetch). Roteado pelo Django (não pela API FastAPI) por depender de sessão, CSRF e `login_required`. Resposta 204 sem corpo; idempotente via `get_or_create`. Degrada graciosamente: falha de POST não bloqueia a troca visual no cliente.

### Tematização (apresentação)
Estratégia Tailwind `darkMode: 'class'` com `<html class="dark">`. Precedência de resolução: preferência do servidor (logado) → `localStorage` → `prefers-color-scheme`. Anti-FOUC por script inline síncrono no `<head>`. Parciais trocados via HTMX receberam variantes próprias para não "voltarem ao claro" após swap.

## Preservadas

Todas as regras 🟢 CONFIRMADAS do `domain.md` permanecem intactas (nenhuma linha de lógica correspondente foi tocada):

- **RN-01** Isolamento de Tenant por ContextVar — intacta (`UserSettings` é global, não interfere no `TenantManager`).
- **RN-03** Auto-atribuição de Tenant em Save — intacta.
- **RN-04** Checkout requer nome, telefone e endereço — intacta (`cart_drawer.html` só recebeu classes `dark:`).
- **RN-05** Pedido de convidado e vinculação pós-signup — intacta.
- **RN-06** Limite de 3 endereços por usuário por loja — intacta.
- **RN-07** Snapshot de preço no OrderItem — intacta.
- **RN-08** Pedido de balcão sem PIX, já em preparo — intacta.
- **RN-09** Token MercadoPago por tenant — intacta.
- **RN-10** Fallback mock em desenvolvimento — intacta.
- **RN-12** Acesso ao dashboard manager (controle binário) — intacta.
- **RN-13** KPIs do dashboard — intacta.
- **RN-15** Disponibilidade de produto — intacta.
- **RN-16** Rastreamento de pedido público — intacta.

## Modificadas

Nenhuma. Nenhuma regra de negócio 🟢 foi alterada ou removida por esta feature.
