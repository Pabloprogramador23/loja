# Investigation: 002-cadastro-loja-saas

> Data: `2026-05-26`

---

## 1. OneToOneField reverso no Django — comportamento de acesso

O acesso reverso de `User → Store` via `OneToOneField` em Django **levanta `RelatedObjectDoesNotExist`** (subclasse de `ObjectDoesNotExist`) quando o User não possui Store associado — diferente de um `ForeignKey` reverso, que retornaria um Manager vazio sem levantar exceção.

**Forma segura recomendada:**
```python
store = getattr(request.user, 'owned_store', None)
# retorna None se não tiver loja, sem exceção
```

Alternativa explícita:
```python
try:
    store = request.user.owned_store
except ObjectDoesNotExist:
    store = None
```

O `related_name='owned_store'` (singular) é o padrão Django para OneToOne e comunica a semântica claramente.

---

## 2. Criação atômica User + Store

O padrão Django para operações que devem ser indivisíveis é `transaction.atomic()` como context manager. Qualquer exceção levantada dentro do bloco reverte todas as operações:

```python
from django.db import transaction, IntegrityError

with transaction.atomic():
    user = form.save()          # cria User
    Store.objects.create(       # cria Store vinculada
        name=form.cleaned_data['store_name'],
        subdomain=form.cleaned_data['subdomain'],
        owner=user,
        is_active=True,
    )
```

Se `Store.objects.create()` falhar por `IntegrityError` (subdomínio duplicado ou constraint de unicidade), o `user` criado dentro do bloco também é revertido automaticamente.

**Ponto de atenção:** a validação de unicidade do subdomínio deve acontecer no `clean_subdomain()` do form (antes do save), tanto para feedback de UX quanto para evitar depender de captura de `IntegrityError` como fluxo normal.

---

## 3. Validação de subdomínio

**Formato aceito:** letras minúsculas, números e hífens; não pode começar nem terminar com hífen.

```python
from django.core.validators import RegexValidator

subdomain_validator = RegexValidator(
    regex=r'^[a-z0-9][a-z0-9\-]*[a-z0-9]$',
    message='Use apenas letras minúsculas, números e hífens. Não pode começar ou terminar com hífen.'
)
```

**Subdomínios reservados** — devem ser bloqueados no `clean_subdomain()`:

```python
RESERVED_SUBDOMAINS = {
    'www', 'api', 'admin', 'mail', 'smtp', 'ftp',
    'catalog', 'checkout', 'cart', 'dashboard',
    'account', 'order', 'orders', 'static', 'media',
}

def clean_subdomain(self):
    subdomain = self.cleaned_data.get('subdomain', '').lower()
    if subdomain in RESERVED_SUBDOMAINS:
        raise ValidationError('Subdomínio reservado. Escolha outro nome.')
    if Store.objects.filter(subdomain=subdomain).exists():
        raise ValidationError('Este subdomínio já está em uso.')
    return subdomain
```

---

## 4. Redirect pós-login — preservação do parâmetro `next`

O `login_view` atual suporta `next` (redirect após login exigido por `@login_required`). A nova lógica deve manter esse comportamento intacto e adicionar detecção de `owned_store` apenas como fallback:

```python
# Ordem de prioridade no redirect pós-login:
next_url = request.POST.get('next') or request.GET.get('next')
if next_url:
    return redirect(next_url)                          # 1. next param (preserva @login_required)
if getattr(user, 'owned_store', None):
    return redirect('dashboard')                       # 2. dono de loja → dashboard
return redirect('index')                               # 3. cliente comum → home
```

---

## 5. Guard do dashboard — helper vs decorator

**Opção escolhida: helper function `user_can_manage_store(request)`**

```python
def user_can_manage_store(request):
    if request.user.is_staff:
        return True
    if request.tenant is None:
        return False
    return getattr(request.user, 'owned_store', None) == request.tenant
```

**Por que não decorator customizado:** um decorator `@manager_required` seria mais elegante para uso repetido, mas exigiria importação circular potencial entre `core.views` e `core.decorators`, além de introduzir uma abstração que não existia no legado. Para 9 views já modificadas, o helper inline é suficiente e mais explícito.

**Por que não grupos Django:** o sistema atual não usa grupos (`auth.Group`) em nenhum ponto. Introduzir grupos exigiria criação de dados na migration e lógica de atribuição no `criar_loja_view` — over-engineering para o escopo atual.

---

## 6. Alternativas avaliadas e descartadas

| Alternativa | Motivo da rejeição |
|-------------|-------------------|
| `UserProfile` model separado com FK para Store | Tabela extra desnecessária; OneToOne no lado Store é suficiente e mais simples |
| Grupos Django para papel "Manager" | Requer dados criados em migration; overhead sem benefício no escopo atual |
| Token de convite pós-cadastro | Over-engineering para MVP single-owner |
| Email obrigatório no cadastro de loja | Não solicitado no requirements; evita atrito desnecessário no onboarding |
