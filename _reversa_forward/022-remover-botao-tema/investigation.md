# Investigation: Remover botão de tema

> Identificador: `022-remover-botao-tema`
> Data: `2026-06-05`

## Localização exata do botão

`templates/dashboard_base.html`, dentro do bloco `<!-- User Info & Logout -->` (linha 100), antes do bloco de info do usuário:

```html
<button type="button" onclick="toggleTheme()" aria-label="Alternar tema claro e escuro"
    class="w-full flex items-center justify-center gap-2 mb-3 px-4 py-2 ...">
    <svg class="w-5 h-5 block dark:hidden" ...>  <!-- ícone lua -->
    </svg>
    <svg class="w-5 h-5 hidden dark:block" ...>  <!-- ícone sol -->
    </svg>
    <span>Tema</span>
</button>
```

O bloco ocupa as linhas 101–114 do arquivo atual.

## O que NÃO deve ser tocado

| Artefato | Localização | Motivo para preservar |
|----------|-------------|----------------------|
| Função `toggleTheme()` | `dashboard_base.html` `<head>` linhas 28–45 | Infraestrutura — pedido explícito do usuário |
| Script anti-FOUC | `dashboard_base.html` `<head>` linhas 13–26 | Infraestrutura de dark mode |
| `class="dark"` no `<html>` | `dashboard_base.html` linha 2 | Controla o tema visualmente |
| `core/context_processors.py` | `theme_pref` | Backend do dark mode |
| `core/views.py` | `set_theme` view | Endpoint de persistência |
| `core/models.py` | `UserSettings` | Model de preferência |
| `templates/base.html` | inteiro | Não tem botão; fora do escopo |

## Verificação de outros pontos

Grep por `toggleTheme` em todos os templates deve retornar apenas:
- `dashboard_base.html` — a função JS (que permanece)

Se retornar outros templates com `<button onclick="toggleTheme()">`, esses também devem ser removidos.

## Alternativas descartadas

| Alternativa | Razão para descartar |
|-------------|----------------------|
| Esconder o botão com `hidden` ou `display:none` | Mantém código ativo acessível via DOM; inconsistente com a intenção de remover |
| Remover também `toggleTheme()` | Usuário pediu para manter a estrutura de código |
| Feature flag condicional | Complexidade desnecessária para uma remoção definitiva |
