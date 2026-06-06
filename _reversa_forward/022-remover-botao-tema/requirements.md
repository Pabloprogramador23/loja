# Requirements: Remover botão de alternância de tema claro/escuro

> Identificador: `022-remover-botao-tema`
> Data: `2026-06-05`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

O sistema possui um botão de alternância de tema (claro ↔ escuro) no sidebar do painel do gestor (`dashboard_base.html`). Por decisão de produto, esse botão deve ser removido dos templates por ora, mas toda a infraestrutura de código do dark mode deve permanecer intacta: modelos (`UserSettings`), view (`set_theme`), context processor (`theme_pref`), script anti-FOUC, função JS `toggleTheme()`, e classes Tailwind `dark:` em todos os elementos. Somente o elemento HTML `<button>` que invoca `toggleTheme()` é removido.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/domain.md#RN-19` | `UserSettings.theme` persiste preferência (`system`\|`light`\|`dark`) por usuário; aplicação via Tailwind `darkMode:'class'` + anti-FOUC + context processor `theme_pref` | 🟢 |
| `_reversa_sdd/inventory.md#Estrutura de Diretórios` | `templates/dashboard_base.html` — sidebar do painel do gestor contém botão "Tema" com `onclick="toggleTheme()"` (linhas 101–114) | 🟢 |
| `_reversa_sdd/inventory.md#Estrutura de Diretórios` | `templates/base.html` — template base do cliente **não possui botão** de tema; apenas o script anti-FOUC | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Pablo (gestor/admin) | Não ver mais o botão de alternância de tema no sidebar | Acessa o painel → sidebar exibe nav, info de usuário e logout, sem botão "Tema" |
| Cliente da loja | Não afetado — nunca teve botão de tema na vitrine | n/a |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** O gestor não pode mais alternar o tema pela interface do painel. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#RN-19` (preferência de tema por usuário)
   - Tipo: alterada (restrição de interface — a preferência em banco continua existindo, mas não há mais como alterá-la pelo painel)

2. **RN-02:** Toda a infraestrutura de dark mode permanece funcional e ativa. 🟢
   - `UserSettings`, `set_theme` view, `theme_pref` context processor, script anti-FOUC, função JS `toggleTheme()`, classes Tailwind `dark:` — nada disso é tocado.
   - Tipo: preservada (explicitamente fora do escopo de remoção)

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Remover o elemento `<button>` de alternância de tema do `dashboard_base.html` (linhas 101–114) | Must | O sidebar do painel não exibe botão com ícone de lua/sol nem texto "Tema" | 🟢 |
| RF-02 | Manter o script `toggleTheme()` em `dashboard_base.html` intacto | Must | Função JS ainda existe no `<head>` do dashboard_base.html após a remoção | 🟢 |
| RF-03 | Não modificar `base.html` (template da vitrine) | Must | `base.html` permanece byte-a-byte idêntico ao estado atual | 🟢 |
| RF-04 | Não modificar nenhum arquivo Python (models, views, context_processors, urls) | Must | Grep por `set_theme`, `theme_pref`, `UserSettings` continua retornando os mesmos arquivos | 🟢 |
| RF-05 | Verificar se há outros templates do painel que referenciam `toggleTheme()` como botão | Should | Grep por `toggleTheme` em todos os templates — se houver outros botões em templates do painel, removê-los também | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Regressão | O anti-FOUC (preferência de tema aplicada antes do render) continua funcionando | Script no `<head>` de `dashboard_base.html` não é tocado | 🟢 |
| Regressão | O painel continua respeitando a preferência de tema salva em banco | `theme_pref` do context processor alimenta a classe `dark` no `<html>` — não alterado | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Botão removido do sidebar do painel
  Dado que o gestor está no painel (/dashboard/)
  Quando a página é renderizada
  Então não existe nenhum botão com ícone de lua, sol ou texto "Tema" no sidebar

Cenário: Infraestrutura dark mode intacta
  Dado que a feature foi aplicada
  Quando se inspeciona o HTML do painel
  Então a função JS toggleTheme() existe no <head>
  E a classe "dark" no <html> reflete a preferência salva do usuário

Cenário: Vitrine do cliente não afetada
  Dado que a feature foi aplicada
  Quando um cliente acessa a vitrine (/)
  Então o header e o layout do cliente são idênticos ao estado anterior

Cenário: Nenhum arquivo Python modificado
  Dado que a feature foi aplicada
  Quando se executa git diff em arquivos .py
  Então não há nenhuma linha alterada em arquivos Python
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 Remover botão do dashboard_base | Must | É o único objetivo da feature |
| RF-02 Manter toggleTheme() | Must | Parte da infraestrutura — usuário pediu explicitamente para não tocar |
| RF-03 Não tocar base.html | Must | Não há botão lá; mencionado para deixar explícito |
| RF-04 Não tocar Python | Must | Usuário pediu explicitamente para manter estrutura de código |
| RF-05 Grep outros templates | Should | Garantia de completude |

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda. Rode `/reversa-clarify` quando houver `[DÚVIDA]` pendente.

## 10. Lacunas

Nenhuma lacuna — escopo definido com precisão pelo usuário.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-05 | Versão inicial gerada por `/reversa-requirements` | reversa |
