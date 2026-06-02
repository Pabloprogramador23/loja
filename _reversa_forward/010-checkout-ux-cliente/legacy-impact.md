# Legacy Impact: 010-checkout-ux-cliente

> Data: 2026-05-30
> Feature: Melhoria de UX no Checkout do Cliente

## Arquivos Afetados

| Arquivo afetado | Componente (_reversa_sdd_) | Tipo | Severidade | Justificativa |
|-----------------|---------------------------|------|------------|---------------|
| `core/models.py` | `_reversa_sdd/architecture.md#Módulo core` | componente-novo | LOW | `UserProfile` adicionado sem alterar models existentes |
| `core/migrations/0012_userprofile.py` | `_reversa_sdd/architecture.md#delta-de-dados` | delta-de-dados | LOW | Migration aditiva; não altera tabelas existentes |
| `core/views.py` | `_reversa_sdd/code-analysis.md#2.3` | regra-alterada | MEDIUM | `cart_detail`, `checkout`, `save_address` e nova `payment_view` |
| `core/urls.py` | `_reversa_sdd/architecture.md#Rotas Django` | regra-alterada | LOW | Rota `/payment/<id>/` adicionada |
| `core/tests_checkout_ux.py` | — | componente-novo | LOW | Novos testes; sem impacto no legado |
| `templates/core/partials/cart_drawer.html` | `_reversa_sdd/code-analysis.md#2.3` | regra-alterada | MEDIUM | Lógica de exibição do formulário de checkout alterada |
| `templates/core/partials/address_list.html` | `_reversa_sdd/code-analysis.md#2.3` | regra-alterada | MEDIUM | `selectAddress` e feedback de erro alterados |
| `templates/core/payment_pix.html` | `_reversa_sdd/code-analysis.md#2.3` | regra-alterada | MEDIUM | Correção de scroll + placeholder de QR Code indisponível |
| `accounts/forms.py` | `_reversa_sdd/architecture.md#Módulo accounts` | regra-alterada | HIGH | Email obrigatório no cadastro de cliente e de loja |
| `accounts/views.py` | `_reversa_sdd/architecture.md#Módulo accounts` | regra-alterada | MEDIUM | `signup_view` usa `CustomerSignupForm` com email |

## Diff conceitual por componente

### `cart_detail()` — regra-alterada
Antes: retornava apenas `cart` e `addresses` no contexto. Agora: também retorna `profile_phone` lido de `UserProfile.get_or_create`. Impacto: template pode pré-preencher o campo de telefone.

### `checkout()` — regra-alterada
Antes: não persistia o telefone após o pedido. Agora: chama `UserProfile.update_or_create` com o `phone` informado, fora do bloco `transaction.atomic()`.

### `save_address()` — regra-alterada
Antes: capturava qualquer `Exception` silenciosamente (`pass`). Agora: captura `ValidationError` explicitamente e retorna o partial com `address_error` no contexto, tornando o erro visível ao usuário.

### `address_list.html` — regra-alterada
Antes: `selectAddress` montava `"{street}, {number} - {neighborhood}"` sem cidade/estado. Agora: inclui `", {city} - {state}"` e CEP quando disponível. O `onclick` de cada card de endereço foi atualizado para passar a string completa.

### `cart_drawer.html` — regra-alterada
Antes: campo `customer_phone` sempre vazio para usuário autenticado; textarea sempre visível. Agora: phone pré-preenchido com `profile_phone`; textarea oculto (`hidden`) quando usuário tem endereços salvos, com botão "Outro endereço" para revelá-lo via Hyperscript.

### `checkout()` — redirecionamento pós-pedido (regra-alterada)
Antes: retornava `payment_pix.html` completo para `hx-target="#cart-content"`, causando injeção de página inteira dentro do drawer. Agora: salva `payment_data` na sessão e retorna `<script>window.location.href="/payment/<id>/"</script>`, forçando navegação completa do browser para a página de pagamento.

### `payment_view()` — componente-novo
Nova view em `/payment/<id>/` que lê `payment_data` da sessão e renderiza `payment_pix.html` como página completa, isolada do drawer.

### `payment_pix.html` — regra-alterada
Correções de UX: (a) removido `flex justify-center min-h-screen` que impedia scroll em telas pequenas; (b) QR Code com verificação de comprimento mínimo (`|length > 100`) para evitar placeholder colorido quando MercadoPago não está configurado; exibe ícone + mensagem descritiva no lugar.

### `accounts/forms.py` — regra-alterada
Criado `CustomerSignupForm` com campo `email` obrigatório (herdado de `UserCreationForm`). `StoreRegistrationForm` também recebeu campo `email` obrigatório. Sem email, MercadoPago não consegue enviar notificação PIX ao pagador.

### `accounts/views.py` — regra-alterada
`signup_view` substituiu `UserCreationForm` por `CustomerSignupForm`. O email é salvo em `user.email` via `form.save()`, disponível para `payer_email` no checkout.

## Preservadas

Regras 🟢 do `_reversa_sdd/domain.md` que continuam intactas:

- **RN-04** — Checkout valida `customer_name`, `customer_phone` e `delivery_address` (campos obrigatórios preservados)
- **RN-05** — Guest order e vinculação pós-signup (fluxo de visitante não alterado)
- **RN-06** — Limite de 3 endereços por `(user, store)` (regra de negócio preservada no model)
- **RN-07** — Snapshot de preço no `OrderItem` (não tocado)
- **RN-01** — Isolamento de tenant por ContextVar (não tocado)
- **RN-03** — Auto-atribuição de tenant em save (não tocado)

## Modificadas

- **RN-04** (parcialmente alterada) — O checkout agora diferencia comportamento entre usuário autenticado (phone pré-preenchido, endereço selecionável) e visitante (formulário completo). A validação dos campos obrigatórios permanece idêntica.
- **RN-06** (comportamento de erro alterado) — O limite de 3 endereços continua sendo aplicado no model, mas agora o erro é surfaceado ao usuário em vez de ser suprimido silenciosamente.
