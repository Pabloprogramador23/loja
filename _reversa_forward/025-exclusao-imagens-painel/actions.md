# Actions: Exclusão de Imagens no Painel

> Identificador: `025-exclusao-imagens-painel`
> Data: `2026-07-13`
> Roadmap: `_reversa_forward/025-exclusao-imagens-painel/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 9 |
| Paralelizáveis (`[//]`) | 3 |
| Maior cadeia de dependência | 4 |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Adicionar os campos booleanos ocultos `clear_logo` e `clear_cover_image` em `StoreSettingsForm` | - | - | `core/forms.py` | 🟢 | `[x]` |
| T002 | Adicionar o campo booleano oculto `clear_image` em `ProductForm` | - | - | `core/forms.py` | 🟢 | `[x]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Criar testes automatizados para validar a deleção física e lógica de imagens no formulário de settings e produto | T001, T002 | - | `core/tests_image_deletion.py` | 🟢 | `[x]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Implementar o método `save()` em `StoreSettingsForm` para apagar fisicamente as mídias do storage e atribuir `None` ao logotipo e/ou capa da loja se marcar limpeza | T001, T003 | - | `core/forms.py` | 🟢 | `[x]` |
| T005 | Implementar o método `save()` em `ProductForm` para apagar fisicamente o arquivo do storage e atribuir `None` à imagem do produto se marcar limpeza | T002, T003 | - | `core/forms.py` | 🟢 | `[x]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T006 | Atualizar template de configurações da loja para incluir inputs ocultos, botões de remoção e popup de confirmação JS no submit | T004 | `[//]` | `templates/core/manager/settings.html` | 🟢 | `[x]` |
| T007 | Atualizar template de produto para incluir input oculto, botão de remoção e popup de confirmação JS no submit | T005 | `[//]` | `templates/core/manager/product_form.html` | 🟢 | `[x]` |
| T008 | Atualizar o template de lista de produtos para exibir o ícone SVG de talheres como placeholder para produtos sem imagem | T005 | `[//]` | `templates/core/partials/product_list.html` | 🟢 | `[x]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T009 | Adicionar logs informativos nas views correspondentes e documentação curta do comportamento | T006, T007 | - | `core/views.py` | 🟢 | `[x]` |

## Notas de execução

<!--
Reservado para /reversa-coding registrar avisos ou observações que surgiram durante a execução.
Não use isso para corrigir ações, edits manuais ficam fora desse arquivo, vão direto no código.
-->

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-07-13 | Versão inicial gerada por `/reversa-to-do` | reversa |
