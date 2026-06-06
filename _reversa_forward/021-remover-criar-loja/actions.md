# Actions: Remover opção "Criar Loja" do sistema

> Identificador: `021-remover-criar-loja`
> Data: `2026-06-05`
> Roadmap: `_reversa_forward/021-remover-criar-loja/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 7 |
| Paralelizáveis (`[//]`) | 3 |
| Maior cadeia de dependência | 3 (T001 → T003 → T005) |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Remover link "🏪 Crie sua loja" de `login.html` — deletar o bloco `<div class="border-t ...">` que contém o `<a href="{% url 'criar_loja' %}">` (linhas 54-58) | - | `[//]` | `templates/accounts/login.html` | 🟢 | `[X]` |
| T002 | Deletar o arquivo `templates/accounts/criar_loja.html` | - | `[//]` | `templates/accounts/criar_loja.html` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Remover a rota `path('criar-loja/', ...)` de `accounts/urls.py` e o import/referência à `criar_loja_view` na mesma linha | T001, T002 | - | `accounts/urls.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Remover a função `criar_loja_view` completa de `accounts/views.py` (linhas 11-34, incluindo o bloco `if request.user.is_authenticated`, `from .forms import StoreRegistrationForm`, etc.) | T003 | - | `accounts/views.py` | 🟢 | `[X]` |
| T005 | Remover `StoreRegistrationForm` de `accounts/forms.py` (linhas 71-106) e os auxiliares `RESERVED_SUBDOMAINS` (linhas 6-10) e `subdomain_validator` (linhas 12-15), que não são usados por nenhum outro form | T004 | - | `accounts/forms.py` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T006 | Executar grep de validação: `grep -r "criar_loja" --include="*.py" --include="*.html" .` na raiz do projeto — confirmar zero ocorrências | T005 | - | *(verificação)* | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T007 | Gerar `regression-watch.md` para esta feature, listando os pontos críticos a monitorar: rota `/criar-loja/` deve retornar 404, `/signup/` e `/login/` devem continuar funcionais | T006 | `[//]` | `_reversa_forward/021-remover-criar-loja/regression-watch.md` | 🟢 | `[X]` |

## Notas de execução

*(reservado para /reversa-coding)*

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-05 | Versão inicial gerada por `/reversa-to-do` | reversa |
