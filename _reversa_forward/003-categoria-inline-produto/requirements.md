# Requirements: Criação Inline de Categoria no Cadastro de Produto

> Identificador: `003-categoria-inline-produto`
> Data: `2026-05-26`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Donos de loja, ao cadastrar ou editar um produto, frequentemente precisam de uma categoria ainda inexistente. Atualmente, o `ProductForm` exibe apenas um `<select>` com as categorias já existentes — sem rota de saída para criar novas (`_reversa_sdd/code-analysis.md#Módulo 3`). Essa feature adiciona um campo inline **"Nova categoria"** no mesmo formulário: se o usuário preencher o campo, a categoria é criada no banco e automaticamente associada ao produto antes de salvar. O dono não sai da tela de cadastro de produto.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/architecture.md#Domínio de Negócio` | `Category` é entidade do domínio isolada por tenant via `TenantAwareModel` | 🟢 |
| `_reversa_sdd/domain.md#RN-01` | Todo acesso a `Category` é filtrado pelo tenant ativo — criação inline deve respeitar esse isolamento | 🟢 |
| `_reversa_sdd/domain.md#RN-03` | `TenantAwareModel.save()` auto-atribui `store` do ContextVar — nenhuma lógica extra necessária na criação da categoria | 🟢 |
| `_reversa_sdd/code-analysis.md#Módulo 3 / Formulários` | `ProductForm` usa `forms.ModelForm` com campo `category` como `forms.Select` — não há fallback para criar categoria nova | 🟢 |
| `_reversa_sdd/code-analysis.md#Módulo 3 / manager_product_create` | View faz `form.save()` direto sem lógica extra de categoria | 🟢 |
| `_reversa_sdd/architecture.md#Stack` | Projeto usa HTMX via `django-htmx` — solução pode ser puramente server-side sem JS extra | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Dono da loja (store owner) | Cadastrar produto novo em categoria ainda não existente | Preenche formulário de produto, digita nome da categoria no campo "Nova categoria", salva tudo de uma vez |
| Dono da loja (store owner) | Editar produto e mover para categoria nova | Acessa formulário de edição, usa campo "Nova categoria" para criar e já selecionar a nova categoria |

## 4. Regras de negócio novas ou alteradas

1. **RN-A:** Se o campo `new_category_name` for preenchido, o sistema cria uma `Category` com aquele nome (associada ao tenant via `TenantAwareModel.save()`) e a usa como `category` do produto, ignorando o valor do `<select>` de categorias existentes. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#RN-03` (auto-atribuição de tenant no save)
   - Tipo: nova

2. **RN-B:** O nome da nova categoria não pode ser vazio (se o campo for enviado em branco, o sistema usa a seleção do `<select>`). 🟢
   - Tipo: nova

3. **RN-C:** Se o nome informado em `new_category_name` já existir para o tenant atual, o sistema associa o produto à categoria existente em vez de criar uma duplicata. 🟡
   - Tipo: nova

4. **RN-D:** O isolamento multi-tenant de `Category` é preservado: a categoria criada inline pertence exclusivamente ao tenant do request, herdado via `TenantAwareModel.save()` e `ContextVar`. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#RN-01`
   - Tipo: preservada

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Campo de texto "Nova categoria" visível no formulário de criação de produto | Must | Campo aparece abaixo do `<select>` de categorias em `product_form.html` | 🟢 |
| RF-02 | Campo de texto "Nova categoria" visível no formulário de edição de produto | Must | Mesmo campo, mesmo comportamento em edição | 🟢 |
| RF-03 | Se `new_category_name` preenchido, categoria é criada e associada ao produto antes de salvar | Must | Produto salvo com a nova categoria; categoria existe no banco com `store` do tenant | 🟢 |
| RF-04 | Se `new_category_name` vazio, comportamento atual é preservado (`<select>` determina a categoria) | Must | Sem regressão no fluxo existente de criação de produto com categoria já existente | 🟢 |
| RF-05 | Nome de categoria já existente é reutilizado — sem erro, sem duplicata | Should | Digitar nome de categoria já existente associa o produto à categoria existente | 🟡 |
| RF-06 | Mensagem de orientação no formulário indicando que o campo "Nova categoria" substitui a seleção acima | Should | Texto de help visível próximo ao campo | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Segurança | Criação de categoria deve respeitar guard `user_can_manage_store(request)` — mesma proteção das views de produto | `_reversa_sdd/permissions.md` + feature 002 | 🟢 |
| Isolamento | Categoria criada inline não vaza para outros tenants | `_reversa_sdd/domain.md#RN-01` + `RN-03` — TenantAwareModel garante por design | 🟢 |
| Simplicidade | O fluxo de criação de categoria deve completar-se dentro do mesmo ciclo de submit do formulário de produto, sem navegação adicional | Feature não deve exigir telas extras ou popups | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Criar produto com categoria nova
  Dado que o dono da loja está no formulário de novo produto
  E não há nenhuma categoria cadastrada
  Quando preenche todos os campos do produto e digita "Pizzas" em "Nova categoria"
  Então o produto é salvo com a categoria "Pizzas" recém-criada
  E a categoria "Pizzas" pertence à loja do dono

Cenário: Criar produto com categoria existente (sem mudança)
  Dado que o dono da loja está no formulário de novo produto
  E já existem categorias cadastradas
  Quando seleciona uma categoria existente no <select> e deixa "Nova categoria" em branco
  Então o produto é salvo com a categoria selecionada, sem criar nada novo

Cenário: Nome duplicado não gera duplicata
  Dado que a categoria "Bebidas" já existe para a loja
  Quando o dono digita "Bebidas" em "Nova categoria"
  Então o produto é vinculado à categoria "Bebidas" existente, sem criar duplicata

Cenário: Categoria criada não vaza para outra loja
  Dado que o dono da Loja A cria a categoria "Especiais" via campo inline
  Quando o dono da Loja B acessa o formulário de produto
  Então "Especiais" não aparece no <select> da Loja B

Cenário: Texto de orientação visível no formulário
  Dado que o dono da loja acessa o formulário de produto
  Quando visualiza a área de categoria
  Então vê um texto de ajuda explicando que preencher o campo "Nova categoria" substitui a seleção acima
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 / RF-02 | Must | Sem o campo a feature não existe |
| RF-03 | Must | Lógica central da feature |
| RF-04 | Must | Sem regressão é inegociável |
| RF-05 | Should | Evita confusão para o usuário, mas duplicatas não quebram nada |
| RF-06 | Should | Melhora UX mas não bloqueia uso |
| RNF Segurança | Must | Isolamento multi-tenant é arquitetural |

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda. Feature sem marcadores `[DÚVIDA]` — pode avançar direto para `/reversa-plan`.

## 10. Lacunas

> Nenhuma lacuna identificada. Feature bem delimitada pelo legado extraído.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-26 | Versão inicial gerada por `/reversa-requirements` | reversa |
