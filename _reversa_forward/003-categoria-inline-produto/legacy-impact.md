# Legacy Impact: 003-categoria-inline-produto

> Data: `2026-05-26`
> Feature: Criação Inline de Categoria no Cadastro de Produto

---

## Arquivos Afetados

| Arquivo afetado | Componente (`_reversa_sdd/`) | Tipo | Severidade | Justificativa |
|-----------------|------------------------------|------|------------|---------------|
| `core/forms.py` | `code-analysis.md#Formulários` → `ProductForm` | regra-alterada | LOW | Campo extra `new_category_name` adicionado; ModelForm continua salvando apenas os campos do `Meta` — campo extra é processado manualmente na view |
| `core/views.py` | `code-analysis.md#Dashboard Manager` → `manager_product_create` | regra-alterada | MEDIUM | Lógica de criação inline de categoria inserida antes do `form.save()`; comportamento com campo vazio preservado |
| `core/views.py` | `code-analysis.md#Dashboard Manager` → `manager_product_edit` | regra-alterada | MEDIUM | Mesma lógica aplicada à edição de produto |
| `templates/core/manager/product_form.html` | — (template) | contrato-alterado | LOW | Bloco de "Nova categoria" adicionado ao formulário; sem alteração de rotas ou contratos |

---

## Diff conceitual por componente

### `ProductForm` (core/forms.py)

Campo não-model `new_category_name` (CharField, required=False) adicionado fora do bloco `Meta`. O `ModelForm.save()` continua ignorando esse campo — é responsabilidade das views extraí-lo de `cleaned_data` e agir sobre ele. Backward compatible: formulários que não enviam o campo funcionam exatamente como antes.

### `manager_product_create` e `manager_product_edit` (core/views.py)

Ambas as views receberam a mesma lógica após `form.is_valid()`:

```python
nome = form.cleaned_data.get('new_category_name', '').strip()
if nome:
    category, _ = Category.objects.get_or_create(name__iexact=nome, defaults={'name': nome})
    form.instance.category = category
```

O `get_or_create` com `name__iexact` usa o `TenantManager` automaticamente — o lookup já está scoped ao tenant do ContextVar. `TenantAwareModel.save()` atribui `store` na criação. Nenhuma quebra do isolamento multi-tenant. Campo vazio → `if nome` não entra → `form.save()` usa a seleção do `<select>`, sem regressão.

### `product_form.html`

Bloco HTML adicional inserido na grade de 6 colunas (`col-span-6 sm:col-span-3`), ao lado do `<select>` de categorias existentes. Help text exibido abaixo do input.

---

## Regras Preservadas

Regras 🟢 do `_reversa_sdd/domain.md` que continuam intactas após esta feature:

| Regra | Status |
|-------|--------|
| RN-01: Isolamento de Tenant por ContextVar | ✅ preservada — `TenantManager` em `get_or_create` garante scope |
| RN-02: Resolução de Tenant em três níveis | ✅ preservada — não tocada |
| RN-03: Auto-atribuição de Tenant em Save | ✅ preservada — `TenantAwareModel.save()` atribui `store` na criação da categoria |
| RN-04 a RN-11 | ✅ preservadas — não relacionadas a esta feature |
| RN-12: Acesso ao Dashboard (expandido para ownership na feature 002) | ✅ preservada — guards `user_can_manage_store` nas views não foram alterados |
| RN-15: Disponibilidade de Produto | ✅ preservada |
| RN-18: Produto Aleatório na Home | ✅ preservada |

---

## Regras Modificadas

> Nenhuma regra 🟢 do `_reversa_sdd/domain.md` foi alterada ou removida por esta feature. As views de produto receberam lógica nova adicionada, não substituída.
