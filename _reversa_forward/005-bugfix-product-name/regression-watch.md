# Regression Watch: 005-bugfix-product-name

> Gerado em: 2026-05-29
> Feature: Bugfix — Nome do Produto no Card de Destaques

## Itens monitorados

| ID | O que verificar | Arquivo | Sinal de regressão |
|----|----------------|---------|-------------------|
| W001 | `{{ product.name }}` em linha única no card de destaque | `templates/core/index.html` | Tag quebrada em duas linhas (`{{\n    product.name }}`) |
| W002 | Loop `{% for product in featured_products %}` com variável `product` consistente em todo o bloco | `templates/core/index.html` | Variável de loop renomeada sem atualizar todas as referências |

## Histórico de re-extrações

| Data | Veredito W001 | Veredito W002 | Observações |
|------|--------------|--------------|-------------|
| 2026-05-29 | 🟢 Corrigido | 🟢 OK | Bugfix aplicado nesta data |
