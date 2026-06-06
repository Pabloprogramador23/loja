# Roadmap: Remover botão de alternância de tema claro/escuro

> Identificador: `022-remover-botao-tema`
> Data: `2026-06-05`
> Requirements: `_reversa_forward/022-remover-botao-tema/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

Remoção cirúrgica de um único elemento HTML — o `<button>` de alternância de tema — do sidebar de `dashboard_base.html` (linhas 101–114). Nenhum outro arquivo é tocado.

O botão chama `toggleTheme()`, função JS que persiste a preferência em `localStorage` e, para usuários autenticados, dispara `POST /set-theme/`. Ao remover o botão, essa função passa a não ter invocador na UI, mas **permanece no código** (no `<head>` do mesmo template) conforme solicitado. O script anti-FOUC, o context processor `theme_pref`, o model `UserSettings` e a view `set_theme` não são tocados.

O impacto prático é: o gestor não terá mais como trocar o tema pelo painel. A preferência salva anteriormente em banco continua sendo aplicada pelo anti-FOUC a cada acesso.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| Non-destructive sobre legado | Remove apenas o elemento visual; toda infraestrutura de código permanece intacta | respeita |
| Isolamento de tenant | Nenhum dado de tenant é afetado | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Remover apenas o `<button>` HTML (linhas 101–114 de `dashboard_base.html`) | Escopo mínimo solicitado pelo usuário | Remover também `toggleTheme()` | 🟢 |
| D-02 | Manter a função JS `toggleTheme()` no `<head>` | Usuário pediu explicitamente para preservar a estrutura de código | Remover como dead code | 🟢 |
| D-03 | Não tocar `base.html` | Não há botão de tema lá; fora do escopo | n/a | 🟢 |

## 4. Premissas

Nenhuma — requirements.md sem `[DÚVIDA]`.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| Sidebar do painel (botão Tema) | `templates/dashboard_base.html` | regra-alterada | Elemento `<button onclick="toggleTheme()">` removido do sidebar |

## 6. Delta no modelo de dados

- Resumo das mudanças: **nenhuma** — nenhum model, migration ou banco de dados afetado.
- Detalhe completo em: `_reversa_forward/022-remover-botao-tema/data-delta.md`

## 7. Delta de contratos externos

Nenhum — `POST /set-theme/` continua existindo e acessível; apenas a UI que o invocava foi removida.

## 8. Plano de migração

n/a — sem migration de banco.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Outros templates do painel invocam `toggleTheme()` como botão e não foram mapeados | médio | baixo | RF-05: grep por `toggleTheme` em todos os templates antes de encerrar |
| Remoção acidental de linhas adjacentes ao botão (logout, info de usuário) | médio | baixo | Ler o bloco completo antes de editar; verificar que logout continua presente |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Sidebar do painel não exibe botão de tema
- [ ] Função `toggleTheme()` ainda presente no `<head>` do `dashboard_base.html`
- [ ] Nenhum arquivo `.py` modificado (git diff limpo em `.py`)
- [ ] `base.html` sem alterações
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-05 | Versão inicial gerada por `/reversa-plan` | reversa |
