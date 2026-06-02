# Actions: Bugfix — Nome do Produto no Card de Destaques

> Identificador: `005-bugfix-product-name`
> Data: `2026-05-29`
> Tipo: `bugfix`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 1 |
| Paralelizáveis (`[//]`) | 0 |
| Arquivos modificados | 1 |

---

## Sintoma

Na seção "Destaques" da página inicial (`/`), o nome de cada produto aparecia como texto literal `{{ product.name }}` em vez do valor real do campo. O preço e a descrição renderizavam corretamente.

**Print de evidência:** reportado pelo usuário em 2026-05-29 durante testes manuais pós-deploy da feature 004.

---

## Causa Raiz

A tag de template Django estava **quebrada em duas linhas** no arquivo `templates/core/index.html`:

```html
<!-- ANTES — inválido: {{ quebrado em duas linhas -->
<h3 ...">{{
    product.name }}</h3>
```

O tokenizador de templates do Django não reconheceu o par `{{ }}` por causa do newline entre `{{` e `product.name`, tratando-o como texto literal.

---

## Fase única — Correção

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Em `templates/core/index.html`, linha 143: juntar `{{` e `product.name }}` em uma única linha: `{{ product.name }}` | - | - | `templates/core/index.html` | 🟢 | `[X]` |

---

## Verificação

Após correção, o servidor foi reiniciado e os nomes dos produtos passaram a renderizar corretamente nos cards de destaque da página inicial.

---

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-29 | Bug identificado durante navegação manual pós-feature 004; correção aplicada (T001) | pablo + Claude Code |
