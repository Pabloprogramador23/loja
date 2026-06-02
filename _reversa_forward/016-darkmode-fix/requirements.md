# Requirements: Dark Mode — Toggle Funcional

> Identificador: `016-darkmode-fix`
> Data: `2026-06-01`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

O sistema possui infraestrutura completa de dark mode — `UserSettings.theme`, context processor `theme_preference`, view `set_theme` e lógica de anti-FOUC no `base.html` — mas o toggle não funciona visualmente porque o Tailwind Play CDN inicializa com `darkMode: 'media'` antes que a config `darkMode: 'class'` seja aplicada.

Como contorno temporário, a classe `dark` foi fixada no `<html>` e o botão de toggle foi removido. Esta feature resolve o problema de forma definitiva, restaurando o toggle e a persistência de preferência por usuário.

Afeta todos os usuários e o restaurante (painel manager).

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/architecture.md#frontend` | Frontend usa Tailwind CDN (Play CDN) sem build step; CSS é gerado no navegador na inicialização | 🟢 |
| `_reversa_sdd/code-analysis.md#usersettings` | `UserSettings.theme` persiste preferência (`light`, `dark`, `system`) por usuário autenticado | 🟢 |
| `_reversa_sdd/code-analysis.md#context_processors` | `theme_preference` expõe `theme_pref` para os templates via context processor | 🟢 |
| `_reversa_sdd/code-analysis.md#set_theme` | View `set_theme` (`POST /set-theme/`) persiste tema no banco; requer `@login_required` | 🟢 |
| `templates/base.html` | `window.tailwind = { config: { darkMode: 'class' } }` pré-inicializa o CDN; anti-FOUC lê serverPref → localStorage → OS | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Cliente anônimo | Usar o app no tema de sua preferência | Abre a loja, alterna para claro, fecha e reabre — tema persiste via localStorage |
| Cliente cadastrado | Ter o tema sincronizado entre dispositivos | Loga em outro dispositivo, preferência salva no banco aparece automaticamente |
| Restaurante (manager) | Usar o painel no tema preferido | Alterna tema no dashboard, persiste na sessão e na próxima visita |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** O sistema DEVE respeitar a preferência explícita do usuário acima da preferência do SO. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#usersettings`
   - Tipo: alterada (atualmente o sistema ignora a preferência explícita)
2. **RN-02:** Usuários não autenticados persistem preferência via `localStorage`; usuários autenticados persistem via `UserSettings.theme`. 🟢
   - Tipo: confirmada (existia antes, mas sem efeito visual)
3. **RN-03:** O valor padrão de tema é `system` (segue preferência do SO) quando nenhuma preferência explícita foi registrada. 🟡
   - Tipo: confirmada

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Botão de toggle de tema visível no header para todos os usuários | Must | Botão presente e clicável em desktop e mobile | 🟢 |
| RF-02 | Clicar no toggle alterna visualmente entre dark e light sem reload | Must | Classes `dark:*` do Tailwind são aplicadas/removidas imediatamente ao clique | 🟢 |
| RF-03 | Preferência de usuário anônimo persiste via localStorage entre sessões | Must | Fechar e reabrir o navegador mantém o tema escolhido | 🟢 |
| RF-04 | Preferência de usuário autenticado persiste no banco via `POST /set-theme/` | Must | Login em outro dispositivo exibe o tema salvo | 🟢 |
| RF-05 | Sem FOUC (flash of unstyled content) ao carregar a página | Should | Tema correto aplicado antes do primeiro paint visível | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Compatibilidade | Funcionar com Tailwind CDN sem necessidade de build step adicional | Projeto não tem Node/npm no container Docker atual | 🟢 |
| Desempenho | Toggle não deve causar layout reflow perceptível | Operação é apenas troca de classe CSS | 🟢 |
| Manutenibilidade | Solução deve ser compatível com futura migração para Tailwind via NPM | [DÚVIDA] Há planos de adicionar build step ao projeto? | 🔴 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Toggle dark → light como anônimo
  Dado que o app está em modo escuro (classe `dark` no <html>)
  E o usuário não está autenticado
  Quando o usuário clica no botão de toggle de tema
  Então a classe `dark` é removida do <html>
  E o app exibe o tema claro imediatamente
  E o localStorage registra `theme = light`

Cenário: Persistência entre sessões (anônimo)
  Dado que o usuário anônimo escolheu tema claro e fechou o navegador
  Quando o usuário reabre o app
  Então o tema claro é aplicado antes do primeiro paint (sem flash)

Cenário: Persistência no banco (autenticado)
  Dado que o usuário está autenticado
  Quando o usuário clica no toggle e o tema muda para claro
  Então um POST é enviado para /set-theme/ com `theme=light`
  E `UserSettings.theme` é atualizado no banco
  E ao logar em outro dispositivo o tema claro é aplicado

Cenário: Fallback quando sem preferência registrada
  Dado que o usuário nunca alterou o tema
  Quando o app carrega
  Então o tema segue a preferência do SO (prefers-color-scheme)
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 Botão de toggle | Must | Sem botão, usuário não tem controle |
| RF-02 Toggle visual imediato | Must | Core da feature; sem isso o app fica fixo num tema |
| RF-03 Persistência localStorage | Must | UX mínima para anônimos |
| RF-04 Persistência no banco | Must | UX para usuários cadastrados |
| RF-05 Anti-FOUC | Should | Melhoria de polish; aceitável ter flash leve inicialmente |

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda. Rode `/reversa-clarify` quando houver `[DÚVIDA]` pendente.

## 10. Lacunas

- 🔴 [DÚVIDA] Há planos de adicionar build step (Node/npm) ao projeto? Isso determinaria se a solução usa CDN corrigida ou migra para Tailwind instalado via NPM.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-01 | Versão inicial — dark mode travado como contorno temporário; botão removido; feature criada para rastrear resolução definitiva | reversa |
