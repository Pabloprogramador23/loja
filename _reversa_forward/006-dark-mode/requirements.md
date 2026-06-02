# Requirements: Modo Escuro (Dark Mode)

> Identificador: `006-dark-mode`
> Data: `2026-05-29`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Permitir que o usuário visualize a interface da loja em um tema escuro, alternando entre claro e escuro por um controle visível na barra de navegação. A preferência deve ser respeitada nas visitas seguintes. Hoje a interface tem cores claras fixas (hardcoded) no layout global, sem qualquer opção de tema. A feature melhora conforto visual e percepção de modernidade da vitrine, sem alterar regras de negócio.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/architecture.md#Stack Tecnológica` | Frontend usa **HTMX via django-htmx** e arquivos estáticos servidos por **Whitenoise** em produção. Não há framework JS de SPA. | 🟢 |
| `templates/base.html` (código legado, lido ao vivo 2026-05-29) | Layout global carrega **Tailwind via CDN** (`cdn.tailwindcss.com`, marcado *"Dev Only"*) + HTMX + hyperscript. Cores são **hardcoded**: `<body class="bg-gray-50 text-gray-900">`, header `bg-indigo-600`, drawer `bg-white`, footer `bg-gray-800`. Não há toggle de tema nem classe `dark`. | 🟢 |
| `_reversa_sdd/architecture.md#Ausências Notáveis` | Não há sistema de design extraído (`design-system` não foi executado na pipeline reversa); não há tokens de cor centralizados. | 🟡 |
| `_reversa_sdd/deployment.md#Dockerfile` | Tailwind CDN é "Dev Only"; não há etapa de build de CSS (sem `tailwind.config.js`, sem PostCSS). Static via Whitenoise. | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Cliente da vitrine | Navegar produtos com conforto visual, inclusive à noite | Abre a loja, ativa o modo escuro pelo botão no header; ao voltar amanhã, a loja já abre escura |
| Gestor da loja | Operar o painel/comandas em ambiente de pouca luz | Alterna para escuro e o painel do gestor (dashboard, pedidos, comandas, configurações) acompanha; preferência segue o usuário entre dispositivos (salva no perfil) |
| Visitante novo | Ver a loja já no tema que prefere | No primeiro acesso, a loja respeita a preferência do sistema operacional (`prefers-color-scheme`) |

## 4. Regras de negócio novas ou alteradas

<!-- Dark mode é puramente apresentação; não altera regras de domínio confirmadas. -->

1. **RN-01:** A preferência de tema (claro/escuro) é um atributo de **apresentação por usuário/navegador**, sem efeito sobre dados de negócio, pedidos, preços ou tenant. 🟢
   - Origem no legado: n/a (regra nova, não toca `_reversa_sdd/domain.md`)
   - Tipo: nova
2. **RN-02:** Na ausência de preferência salva, o tema inicial **respeita a preferência do sistema operacional** do usuário (`prefers-color-scheme`); se o SO não indicar, assume **claro**. 🟢
   - Tipo: nova
3. **RN-03:** A preferência de tema de um **usuário autenticado** é persistida no **perfil (banco de dados)** e o acompanha entre dispositivos/navegadores. Para **visitantes anônimos** (vitrine pública), a preferência é guardada no `localStorage` do navegador. 🟡
   - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Exibir um controle de alternância de tema (toggle claro/escuro) visível na barra de navegação (`base.html`) | Must | Em qualquer página que estende `base.html`, há um botão acessível por teclado que alterna o tema | 🟢 |
| RF-02 | Ao acionar o toggle, a interface muda imediatamente para o tema selecionado sem recarregar a página | Must | Clique no toggle troca cores de fundo/texto na hora (sem full page reload) | 🟢 |
| RF-03 | Persistir a preferência: no **perfil (banco)** para usuário autenticado; em **`localStorage`** para visitante anônimo | Must | Logado: escolhe escuro, acessa de outro navegador/dispositivo logado e a loja abre escura. Anônimo: escolhe escuro, reabre o mesmo navegador e a loja abre escura | 🟡 |
| RF-04 | Aplicar o tema antes da primeira pintura, evitando "flash" do tema errado (FOUC) | Should | Ao recarregar com escuro salvo, não há lampejo claro perceptível antes do escuro | 🟡 |
| RF-05 | Cobrir os elementos do layout global em modo escuro (body, header, footer, drawer do carrinho, toasts, modais) | Must | Nenhuma área do `base.html` permanece com fundo claro contrastante quando o tema escuro está ativo | 🟢 |
| RF-06 | Cobrir em modo escuro a **vitrine pública** (home, catálogo, produto, carrinho, checkout) **e o painel do gestor** (dashboard, pedidos, comandas, configurações). O admin do Django fica **fora de escopo** | Must | Todas as telas da vitrine e do painel do gestor renderizam legíveis no tema escuro; o admin do Django permanece no visual padrão | 🟢 |
| RF-07 | Para usuário autenticado com preferência no perfil, renderizar a classe de tema no servidor, evitando FOUC sem depender de script cliente | Should | Logado com escuro salvo, o HTML já chega com o tema escuro aplicado | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Compatibilidade | Solução deve operar com **Tailwind via CDN** usando a estratégia `darkMode: 'class'` (classe `dark` no `<html>`), pois não há etapa de build de CSS no projeto | `templates/base.html`, `_reversa_sdd/deployment.md#Dockerfile` | 🟢 |
| Desempenho | Alternância de tema deve ser instantânea (apenas toggle de classe no DOM, sem round-trip ao servidor) | Padrão recomendado para HTMX/Tailwind | 🟡 |
| Acessibilidade | Contraste no tema escuro deve atender WCAG AA para texto; toggle deve ter `aria-label` e ser operável por teclado | Boa prática; sem fonte no legado | 🟡 |
| Manutenibilidade | Evitar duplicar telas; aplicar variantes `dark:` nas mesmas templates em vez de criar templates paralelos | `_reversa_sdd/architecture.md#Ausências Notáveis` (sem tokens centralizados) | 🟡 |
| Privacidade | A preferência de tema do usuário autenticado é persistida no banco vinculada ao usuário; a do anônimo fica só no `localStorage` (não trafega ao servidor). Nenhum dado sensível novo é coletado | Decisão da Sessão 2026-05-29 (§9) | 🟡 |
| Persistência/Migração | Persistir a preferência exige **novo campo** no perfil do usuário e uma **migração Django**. O legado usa o `User` padrão sem modelo de perfil próprio — a localização do campo (User estendido vs. modelo de perfil novo) será decidida no plano | `_reversa_sdd/data-dictionary.md`, `core/models.py` (legado) | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Ativar o modo escuro na vitrine
  Dado que estou na página inicial da loja no tema claro
  Quando clico no controle de alternância de tema no header
  Então o fundo, o texto e os componentes mudam para o tema escuro imediatamente
  E não há recarga completa da página

Cenário: Preferência persiste entre visitas
  Dado que ativei o modo escuro
  Quando fecho e reabro a loja no mesmo navegador
  Então a loja é exibida diretamente no tema escuro

Cenário: Sem flash de tema errado ao recarregar
  Dado que o tema escuro está salvo
  Quando recarrego a página
  Então não vejo um lampejo do tema claro antes do escuro aparecer

Cenário: Voltar ao tema claro
  Dado que estou no tema escuro
  Quando clico novamente no controle de alternância
  Então a interface retorna ao tema claro
  E essa escolha passa a ser a preferência salva
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 Toggle no header | Must | Sem o controle não há feature |
| RF-02 Troca imediata | Must | Expectativa básica de UX |
| RF-03 Persistência | Must | "Respeitar nas próximas visitas" foi pedido explicitamente |
| RF-05 Cobertura do layout global | Must | Layout meio-escuro/meio-claro é defeito visível |
| RF-04 Evitar FOUC | Should | Qualidade percebida; não bloqueia o uso |
| RF-06 Cobertura vitrine + painel do gestor | Must | Escopo confirmado na Sessão 2026-05-29; admin Django fora |
| RF-07 Tema server-side para logado | Should | Elimina FOUC para autenticado; depende da persistência em banco |
| Migração do campo de preferência | Must | Sem o campo, a persistência por perfil (RF-03) não existe |
| Acessibilidade WCAG AA | Should | Recomendado, sem exigência registrada no legado |

## 9. Esclarecimentos

### Sessão 2026-05-29

- **Q:** Quais telas o modo escuro deve cobrir?
  **R:** Vitrine pública **+ painel do gestor** (dashboard, pedidos, comandas, configurações). O admin do Django fica **fora de escopo**.
- **Q:** Como persistir a preferência de tema do usuário?
  **R:** No **perfil do usuário (banco de dados)**, para seguir entre dispositivos. Como a vitrine é pública, visitantes anônimos usam **`localStorage`** como fallback (abordagem híbrida — inferida).
- **Q:** Qual o tema padrão no primeiro acesso, sem preferência salva?
  **R:** **Respeitar o sistema operacional** (`prefers-color-scheme`); na ausência de indicação, claro.

## 10. Lacunas

> Nenhuma lacuna aberta. As três dúvidas iniciais foram resolvidas na Sessão 2026-05-29 (§9). Ponto a confirmar no plano (não bloqueante): **onde** ancorar o campo de preferência — estender o `User` padrão, criar modelo de perfil próprio, ou um `UserSettings` — decisão técnica de `/reversa-plan`.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-29 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-05-29 | Esclarecimentos integrados (escopo, persistência, default); 3 `[DÚVIDA]` resolvidas via `/reversa-clarify` | reversa |
