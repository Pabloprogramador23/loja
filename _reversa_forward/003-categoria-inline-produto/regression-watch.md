# Regression Watch: 003-categoria-inline-produto

> Feature: Criação Inline de Categoria no Cadastro de Produto
> Gerado em: `2026-05-26`

---

## Watch Items

| ID | Origem | Regra esperada após mudança | Tipo | Sinal de violação |
|----|--------|-----------------------------|------|-------------------|
| W001 | `_reversa_sdd/domain.md#RN-01` → `core/views.py` | `Category.objects.get_or_create` em `manager_product_create` e `manager_product_edit` usa `TenantManager` — categorias criadas inline pertencem exclusivamente ao tenant ativo | presença | Se re-extração mostrar que a criação de categoria na view não usa o queryset padrão do `TenantManager`, ou se `store` não for atribuído via `TenantAwareModel.save()` |
| W002 | `_reversa_sdd/code-analysis.md#Formulários` → `core/forms.py` | `ProductForm` possui campo extra `new_category_name` (não-model, required=False) | presença | Se re-extração mostrar que o campo foi removido do form ou passou a ser `required=True` quebrando o fluxo sem nova categoria |
| W003 | `_reversa_sdd/code-analysis.md#Dashboard Manager` → `core/views.py` | Quando `new_category_name` está vazio, as views `manager_product_create` e `manager_product_edit` preservam o comportamento original (categoria vem do `<select>`) | redação | Se re-extração mostrar que a lógica de `if nome:` foi removida ou que o campo sempre sobrescreve a seleção mesmo quando vazio |

---

## Observações (regras 🟡 — sem peso de regressão)

- O comportamento de `get_or_create` com `name__iexact` pode criar categorias com capitalização diferente do lookup se o banco for case-sensitive (🟡) — sem âncora confirmada na extração original.

---

## Histórico de re-extrações

> Nenhuma re-extração executada após esta feature. Rode `/reversa` para iniciar o ciclo de verificação.

---

## Arquivadas

> Nenhum item arquivado.
