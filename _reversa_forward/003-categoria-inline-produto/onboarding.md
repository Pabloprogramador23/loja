# Onboarding: 003-categoria-inline-produto

> Data: `2026-05-26`
> Pré-requisito: servidor rodando em `http://127.0.0.1:8000/` com usuário dono de loja logado

---

## Passo a passo para testar

### Cenário 1 — Criar produto com categoria nova

1. Acesse `http://127.0.0.1:8000/manager/products/create/` (ou o caminho equivalente de "Novo Produto" no dashboard)
2. Preencha **Nome do Produto**, **Preço** e demais campos obrigatórios
3. No campo **"Nova categoria"**, digite um nome que ainda não existe na sua loja (ex.: "Sobremesas")
4. Clique em **Salvar**
5. Verifique que o produto foi salvo listado sob a categoria "Sobremesas"
6. Acesse novamente o formulário de criação de produto — "Sobremesas" deve aparecer agora no `<select>` de categorias

### Cenário 2 — Criar produto com categoria existente (sem mudança de comportamento)

1. Acesse o formulário de novo produto
2. Selecione uma categoria existente no `<select>`
3. Deixe o campo **"Nova categoria"** em branco
4. Clique em **Salvar**
5. Produto salvo com a categoria selecionada — sem criar categoria nova

### Cenário 3 — Nome de categoria já existente

1. Acesse o formulário de novo produto
2. No campo **"Nova categoria"**, digite o nome de uma categoria já existente (ex.: "Bebidas")
3. Clique em **Salvar**
4. Produto salvo com a categoria "Bebidas" existente — sem duplicata no banco

### Cenário 4 — Editar produto e trocar para categoria nova

1. Na lista de produtos, clique em **Editar** em um produto existente
2. No campo **"Nova categoria"**, digite um nome novo
3. Salve
4. Produto agora aparece vinculado à nova categoria

---

## Verificação de isolamento multi-tenant

Se tiver acesso a duas lojas diferentes (dois usuários donos de lojas diferentes):

1. Crie a categoria "Especiais" na **Loja A**
2. Faça login na **Loja B** (ou acesse em outra sessão)
3. Abra o formulário de produto da Loja B
4. Confirme que "Especiais" **não aparece** no `<select>` da Loja B
