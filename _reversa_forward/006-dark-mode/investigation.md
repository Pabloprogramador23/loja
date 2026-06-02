# Investigation — Modo Escuro (Dark Mode)

> Identificador: `006-dark-mode`
> Data: `2026-05-29`

## Contexto técnico observado (legado)

- **Tailwind via Play CDN** (`https://cdn.tailwindcss.com`) carregado em `templates/base.html` (comentado "Dev Only") e em `templates/dashboard_base.html`. Não há `tailwind.config.js`, PostCSS ou etapa de build (`_reversa_sdd/deployment.md#Dockerfile`).
- **HTMX 1.9.10** + **hyperscript 0.9.12** para interatividade; sem framework SPA.
- **Whitenoise** serve estáticos em produção (`_reversa_sdd/architecture.md#Stack Tecnológica`).
- Layouts base: `base.html` (global, `<html>` próprio) é estendido por `core/manager/base_manager.html` e `core/account/base_account.html`. `dashboard_base.html` é standalone.
- Autenticação: `auth.User` padrão do Django; **não há** `AUTH_USER_MODEL` custom nem modelo de perfil (`accounts/models.py` inexistente).

## Alternativas avaliadas

### Estratégia de tema (Tailwind)

| Alternativa | Prós | Contras | Veredito |
|-------------|------|---------|----------|
| `darkMode: 'class'` (escolhida) | Permite toggle manual; nativa; funciona no Play CDN via `tailwind.config` inline | Exige aplicar variantes `dark:` nas templates | ✅ Escolhida |
| `darkMode: 'media'` | Zero JS; segue o SO automaticamente | **Não** permite o usuário forçar um tema (contraria RF-01/RF-02) | ❌ |
| CSS custom properties + folha própria | Independente do Tailwind | Reescreve estilos à mão; foge do padrão do projeto | ❌ |
| Build Tailwind com purge + `dark:` | CSS enxuto, pronto para prod | Introduz toolchain de build inexistente (fora de escopo) | ⏭️ Futuro |

### Persistência

| Alternativa | Prós | Contras | Veredito |
|-------------|------|---------|----------|
| `UserSettings` (OneToOne) + `localStorage` p/ anônimo (escolhida) | Segue logado entre dispositivos; cobre anônimo; aditivo | Migração + endpoint | ✅ Escolhida (decisão §9) |
| Só `localStorage` | Simplíssimo, sem backend | Não segue entre dispositivos (contraria a decisão do usuário) | ❌ |
| Custom User model com campo `theme` | Campo "em casa" | Migrar User em projeto existente é alto risco | ❌ |
| Cookie lido no servidor | Server-side sem modelo | Mais frágil que `localStorage` para o caso anônimo; limites de cookie | ❌ |

### Anti-FOUC

- Padrão consolidado: **script inline síncrono no `<head>`**, antes do CSS, que adiciona/remove a classe `dark` em `document.documentElement` lendo (nesta ordem) o valor renderizado pelo servidor (logado), `localStorage`, e `window.matchMedia('(prefers-color-scheme: dark)')`. Para o usuário logado, a classe também é renderizada server-side via context processor (D-06), de modo que o HTML já chega correto.

## Padrões aplicáveis

- **Tailwind dark mode (class strategy):** `<html class="dark">` + utilitários `dark:bg-*`, `dark:text-*`.
- **Progressive enhancement:** toggle funciona com JS mínimo (hyperscript já presente); persistência de logado degrada para `localStorage` se o endpoint falhar.
- **HTMX partial awareness:** parciais trocadas por swap não recarregam o `<html>`; por isso elas próprias precisam das variantes `dark:` para não "voltarem claras".

## Pontos de atenção para o /reversa-to-do

- Decidir o app de hospedagem do `UserSettings` (`core` vs. `accounts`).
- Mapear a lista concreta de templates do escopo (vitrine + `manager/*` + `account/*` + parciais).
- Definir paleta `dark:` consistente (sugestão: superfícies `dark:bg-gray-900/800`, texto `dark:text-gray-100`, header mantém `indigo` com ajuste).
- Tratar leitura defensiva de `UserSettings` para usuários sem registro.

## Fontes

- Código legado lido ao vivo (2026-05-29): `templates/base.html`, `templates/dashboard_base.html`, `templates/core/manager/base_manager.html`, `templates/core/account/base_account.html`, `core/models.py`.
- Extração reversa: `_reversa_sdd/architecture.md`, `_reversa_sdd/deployment.md`, `_reversa_sdd/data-dictionary.md`.
- Tailwind CSS — Dark Mode (class strategy): documentação oficial do framework.
