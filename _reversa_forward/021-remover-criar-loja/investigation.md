# Investigation: Remover opção "Criar Loja"

> Identificador: `021-remover-criar-loja`
> Data: `2026-06-05`

## Contexto

O fluxo de auto-cadastro de loja (`criar_loja_view` + `StoreRegistrationForm`) foi implementado originalmente como mecanismo de onboarding SaaS — permitindo que qualquer visitante criasse sua própria Store com subdomínio. Para o modelo de operação atual do produto (lojas criadas manualmente pelo admin), esse fluxo é desnecessário e representa um vetor de abuso.

## Análise dos pontos de impacto

### 1. `accounts/urls.py` — Rota
```python
path('criar-loja/', views.criar_loja_view, name='criar_loja'),
```
- Nome da URL: `criar_loja`
- Referenciado em templates via `{% url 'criar_loja' %}` — apenas em `login.html:55`
- Não há `reverse('criar_loja')` em nenhum arquivo `.py` (confirmado via grep)

### 2. `accounts/views.py` — View
```python
def criar_loja_view(request):
    # Cria User + Store em transaction.atomic()
    # Usa StoreRegistrationForm
    # Após sucesso: auth_login + redirect('dashboard')
```
- Dependência direta: `StoreRegistrationForm`, `Store.objects.create()`
- Não é chamada por nenhuma outra view
- `auth_login` após criação redireciona para `dashboard` (staff) — esse comportamento não tem equivalente no fluxo de cliente

### 3. `accounts/forms.py` — Form e validators
```python
RESERVED_SUBDOMAINS = {...}
subdomain_validator = RegexValidator(...)

class StoreRegistrationForm(UserCreationForm):
    store_name, subdomain  # campos extras
    def clean_subdomain(self): ...  # valida unicidade
```
- `RESERVED_SUBDOMAINS` e `subdomain_validator` **não são usados** por `CustomerSignupForm` nem `CheckoutSignupForm`
- Portanto são dead code após a remoção do form

### 4. Template `criar_loja.html`
- 112 linhas, formulário standalone com seções "Dados de acesso" e "Dados da loja"
- Não é incluído (`{% include %}`) por nenhum outro template
- Não é estendido por nenhum outro template

### 5. `templates/accounts/login.html` — Link de entrada
```html
<div class="border-t dark:border-gray-700 pt-2">
    <a href="{% url 'criar_loja' %}" ...>🏪 Crie sua loja</a>
</div>
```
- Linhas 54-58 do arquivo
- Único ponto de entrada visual para o fluxo de criação de loja

## Padrão de remoção recomendado

Django não exige nenhum passo especial para remover rotas — basta deletar o `path()` e o Django para de registrar a URL. Referências via `{% url 'nome' %}` em templates que ainda existirem vão levantar `NoReverseMatch` em runtime, por isso a remoção do link no `login.html` deve acontecer **antes** ou **junto** com a remoção da rota.

## Alternativas avaliadas e descartadas

| Alternativa | Razão para descartar |
|-------------|----------------------|
| Proteger a rota com `@login_required` + `is_superuser` | Mantém código morto e cria falsa impressão de feature ativa |
| Retornar 410 Gone | Exige view de placeholder; desnecessário para rota sem SEO relevante |
| Manter form para uso interno no admin | Django Admin cria Store diretamente via ModelAdmin sem precisar desse form |

## Referências

- Django URL dispatcher: remoção de `path()` → 404 automático
- Django Admin: `Store` registrado em `core/admin.py` permite CRUD completo sem form customizado
