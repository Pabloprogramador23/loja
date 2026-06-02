# Investigation: 003-categoria-inline-produto

> Data: `2026-05-26`

---

## Alternativas avaliadas

### Opção A — Campo inline no form (escolhida)
Adicionar `new_category_name` como campo não-model no `ProductForm`. Lógica de criação na view antes do `form.save()`.

**Pros:** Nenhuma nova rota, nenhum JS, backward compatible, lógica centralizada.
**Contras:** O campo aparece no form mas não é salvo automaticamente pelo ModelForm — requer handling manual na view.

### Opção B — Endpoint HTMX dedicado
Criar `POST /manager/categorias/criar/` que retorna um `<option>` novo para ser injetado no `<select>` via `hx-swap`.

**Pros:** UX mais fluida (sem reload da página).
**Contras:** Nova rota, nova view, JS/HTMX obrigatório, mais artefatos para manter. Complexidade desnecessária para o caso de uso.

### Opção C — Página separada de gerenciamento de categorias
Link no dashboard para uma tela CRUD de categorias, similar ao que existe para produtos.

**Pros:** Mais completo a longo prazo.
**Contras:** Não resolve o problema imediato (criar categoria sem sair da tela de produto). Pode ser uma feature futura complementar.

---

## Padrão aplicado: "Extra field in ModelForm"

Django suporta campos extras em `ModelForm` que não correspondem a campos do modelo. O campo é incluído em `form.cleaned_data` mas ignorado pelo `form.save()`. A view extrai o valor e executa a lógica necessária antes do save.

Documentação relevante: Django ModelForm — [campos que não são do modelo](https://docs.djangoproject.com/en/5.0/topics/forms/modelforms/#adding-other-fields-to-modelform)

---

## Comportamento de `get_or_create` com `TenantManager`

`get_or_create` chama internamente `get_queryset().filter(**kwargs)` para o lookup e `create(**defaults)` se não encontrado. Como `TenantManager` injeta `.filter(store=tenant)` no queryset, o lookup já é scoped. O `create` passa pelos kwargs (sem `store`, que não está nos kwargs) e o `TenantAwareModel.save()` preenche `store` do ContextVar.

**Atenção:** usar `name__iexact` no lookup e `defaults={'name': nome_original}` garante busca case-insensitive mas preserva a capitalização original na criação.
