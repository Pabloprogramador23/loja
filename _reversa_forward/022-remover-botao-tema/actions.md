# Actions: Remover botão de alternância de tema claro/escuro

> Identificador: `022-remover-botao-tema`
> Data: `2026-06-05`
> Roadmap: `_reversa_forward/022-remover-botao-tema/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 4 |
| Paralelizáveis (`[//]`) | 0 |
| Maior cadeia de dependência | 3 (T001 → T002 → T003) |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Executar grep por `onclick="toggleTheme()"` em todos os templates para mapear todos os botões existentes antes de editar | - | - | *(verificação)* | 🟢 | `[X]` |

## Fase 2, Testes

*(omitida — feature é remoção de elemento HTML; sem lógica a testar)*

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T002 | Remover o bloco `<button type="button" onclick="toggleTheme()" ...>...</button>` (incluindo os dois `<svg>` internos e o `<span>Tema</span>`) do sidebar de `dashboard_base.html`. Preservar intacto o bloco `<!-- User Info & Logout -->` restante (info do usuário + form de logout) | T001 | - | `templates/dashboard_base.html` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Verificar que `toggleTheme()` ainda está declarada no `<head>` de `dashboard_base.html` e que o logout continua presente no sidebar — grep por `toggleTheme` e `logout` no arquivo | T002 | - | `templates/dashboard_base.html` | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Gerar `regression-watch.md` listando: botão ausente do sidebar, `toggleTheme()` presente no `<head>`, nenhum `.py` alterado | T003 | - | `_reversa_forward/022-remover-botao-tema/regression-watch.md` | 🟢 | `[X]` |

## Notas de execução

*(reservado para /reversa-coding)*

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-05 | Versão inicial gerada por `/reversa-to-do` | reversa |
