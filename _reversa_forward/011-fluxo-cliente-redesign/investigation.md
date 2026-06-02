# Investigation: Localização Pré-Catálogo (011-D)

> Gerado pelo reversa-plan em 2026-05-31
> Escopo: RF-01 da spec-mãe 011-fluxo-cliente-redesign

---

## 1. Contexto técnico do legado

### 1.1 View `catalog()` — `core/views.py:47`

```python
def catalog(request):
    categories = Category.objects.all()
    products = Product.objects.filter(is_available=True)
    category_id = request.GET.get('category_id')
    ...
    return render(request, 'core/catalog.html', {...})
```

Não passa endereço de sessão ao contexto. Delta: adicionar `session_delivery_address = request.session.get('session_delivery_address', '')`.

### 1.2 View `cart_detail()` — referenciada em `cart_drawer.html`

`cart_drawer.html` é renderizado por `cart_detail` (via HTMX GET em `hx-get="{% url 'cart_detail' %}"` na linha 2 do template). O `delivery_address` no `<textarea>` usa atualmente `{{ request.POST.delivery_address|default:'' }}`. Para pré-preencher da sessão, basta passar `session_delivery_address` ao contexto e usar como default secundário.

### 1.3 Sessão Django — padrão do projeto (ADR-004)

O carrinho já usa `request.session[f'cart_{tenant_id}']`. A mesma mecânica se aplica para `session['session_delivery_address']`. Em dev (SQLite) a sessão é armazenada no banco; em prod (PostgreSQL + Redis como session backend, se configurado) é transparente.

### 1.4 `catalog.html` — ponto de inserção do banner

O template atual tem seção de filtros por categoria no topo. O banner de localização vai **antes** dessa seção, condicional a `{% if not session_delivery_address and not request.user.is_staff %}`.

### 1.5 Geolocation API

`navigator.geolocation.getCurrentPosition(success, error)` retorna `Position.coords.latitude` e `Position.coords.longitude`. Para transformar em endereço texto, seria necessário reverse geocoding (ex: Nominatim/OpenStreetMap). **Fora do escopo:** por ora, GPS preenche as coordenadas brutas como string; o usuário pode editar antes de confirmar.

---

## 2. Alternativas avaliadas

### 2.1 Modal bloqueante (descartada)

Bloquear o catálogo até ter endereço aumenta abandono, especialmente em mobile. MoSCoW classifica RF-01 como `Should`, não `Must`. Banner não-bloqueante com dismiss é o padrão de UX adequado.

### 2.2 Página dedicada `/localizacao/` (descartada)

Adiciona um passo extra no fluxo. O banner inline no catálogo é transparente — o usuário vê o cardápio enquanto o banner solicita o endereço.

### 2.3 Armazenar em cookie client-side (descartado)

Sem acesso server-side fácil; expira pelo browser; não segue o padrão já estabelecido de sessão Django.

### 2.4 Reverse geocoding real-time (fora do escopo)

Transformar coordenadas GPS em endereço legível requereria integração com API externa (Nominatim, Google Maps, etc.). Fora do escopo desta feature — coordenadas brutas são aceitáveis como fallback de texto.

---

## 3. Padrões aplicáveis

| Padrão | Aplicação nesta feature |
|--------|------------------------|
| **Session storage para dados temporários** | Consistente com `cart_{tenant_id}` (ADR-004) |
| **HTMX para interações inline** | `hx-post="/save-location/"` + `hx-target="#location-banner"` + `hx-swap="outerHTML"` |
| **Hyperscript para UI local** | Dismiss do banner via `_="on click add .hidden to #location-banner"` |
| **Guard de staff** | `{% if not request.user.is_staff %}` — manager não vê banner |

---

## 4. Arquivos impactados (rascunho para legacy-impact.md)

| Arquivo | Tipo de mudança |
|---------|----------------|
| `core/views.py` — `catalog()` | regra-alterada |
| `core/views.py` — `cart_detail()` | regra-alterada |
| `core/views.py` — `save_location()` | componente-novo |
| `core/urls.py` | componente-novo (nova rota) |
| `templates/core/catalog.html` | regra-alterada |
| `templates/core/partials/cart_drawer.html` | regra-alterada |

**Não impactados:**
- `core/models.py` — sem model change
- `core/migrations/` — sem migration
- `core/api.py` — FastAPI não gerencia sessão Django
