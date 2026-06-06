# Legacy Impact: Integração Real MercadoPago (Sandbox)

> Identificador: `017-mercadopago-sandbox`
> Data execução: `2026-06-02`
> Referência arquitetural: `_reversa_sdd/architecture.md`

---

## Arquivos afetados

| Arquivo afetado | Componente (`_reversa_sdd/`) | Tipo | Severidade | Justificativa |
|-----------------|------------------------------|------|------------|---------------|
| `core/models.py` | `architecture.md#Domínio de Negócio` / `Order` | delta-de-dados | LOW | Campo `customer_email` adicionado; não quebra nenhuma regra existente |
| `core/migrations/0016_add_customer_email_to_order.py` | `architecture.md#Domínio de Negócio` | delta-de-dados | LOW | Migração Django para o campo novo; compatível com dados existentes via default `''` |
| `core/views.py` | `architecture.md#Padrões Arquiteturais` / `views.checkout` | regra-alterada | MEDIUM | `customer_email` agora persistido no Order; corrige bug de dado descartado; correção colateral em `_checkout_error` |
| `core/payment.py` | `architecture.md#Integrações Externas` / MercadoPago | regra-alterada | MEDIUM | Mock guard movido antes da chamada à API; `float` → `str`; payer email/name suportam guest |
| `.env.example` | `architecture.md#Stack Tecnológica` | configuração | LOW | `SITE_URL` documentado |
| `core/tests_payment_sandbox.py` | — | componente-novo | LOW | 7 testes novos cobrindo o comportamento corrigido |

---

## Diff conceitual por componente

### `Order` (modelo de dados)

Campo `customer_email` adicionado após `customer_phone`. Permite persistir o email do cliente (guest ou autenticado) junto ao pedido, desacoplando a função de pagamento da necessidade de ter um `User` vinculado. Não altera nenhuma relação existente.

### `create_checkout_pro_preference()` (`core/payment.py`)

**Antes:** usava `order.user.email` e `order.user.get_full_name()` diretamente — lançava `AttributeError` para pedidos de convidado (`order.user = None`). `unit_price` era `float`.

**Depois:** usa `order.customer_email or (order.user.email if order.user else '')` para email e `order.customer_name` como fallback para nome. `unit_price` agora é `str` para evitar arredondamento IEEE 754.

### `create_pix_payment()` (`core/payment.py`)

**Antes:** guard de mock (`token.startswith("TEST-0000") or status == 403`) era avaliado **após** a chamada à API, mascarando silenciosamente erros de credencial real. `transaction_amount` era `float`.

**Depois:** guard de mock (`token.startswith("TEST-0000")`) avaliado **antes** de instanciar o SDK. Tokens reais chegam à API; HTTP 403 real retorna `None` com log. `transaction_amount` agora é `str`.

### `_checkout_error()` (`core/views.py`)

**Antes:** não passava `session_delivery_address` ao contexto, causando `VariableDoesNotExist` no template `cart_drawer.html`.

**Depois:** inclui `session_delivery_address: request.session.get('session_delivery_address', '')` no contexto.

---

## Regras preservadas

As seguintes regras 🟢 do `_reversa_sdd/domain.md` continuam intactas após esta feature:

- **RN-09**: Token MP por tenant (`order.store.mercadopago_access_token or settings.MERCADOPAGO_ACCESS_TOKEN`) — preservado em ambas as funções
- **RN-10**: Mock ativa com `TEST-0000` — preservado; apenas o 403 foi removido do trigger
- **RN-04**: Checkout requer name, phone e address — sem alteração
- **RN-05**: Guest order linking via `session['guest_order_id']` — sem alteração
- **RN-14**: Webhook HMAC + transição PENDING → PREPARING — sem alteração

---

## Regras modificadas

- **RN-10** (parcial): Mock de PIX não ativa mais para HTTP 403 com token real. A regra original dizia "se token `TEST-0000` **ou** API retorna 403". Agora é apenas "se token `TEST-0000`". O comportamento com token real e 403 muda de mock silencioso para `None` (erro visível).
- **RN-11**: Email do pagador PIX para convidados agora usa `order.customer_email` em vez de `guest@placeholder.invalid` quando disponível. Placeholder permanece apenas como último fallback.
