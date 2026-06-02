# Legacy Impact: 002-cadastro-loja-saas

> Data: `2026-05-26`
> Feature: Auto-onboarding de loja SaaS + acesso ao dashboard por ownership

---

## Arquivos Afetados

| Arquivo afetado | Componente (`_reversa_sdd/`) | Tipo | Severidade | Justificativa |
|-----------------|------------------------------|------|------------|---------------|
| `core/models.py` | `architecture.md#Store (model)` | delta-de-dados | MEDIUM | Campo `owner` OneToOneField adicionado; lojas existentes ficam com owner=NULL |
| `core/migrations/0007_store_owner.py` | — (novo artefato) | delta-de-dados | LOW | Migration DDL que adiciona coluna nullable; sem downtime em banco pequeno |
| `accounts/forms.py` | `code-analysis.md#Módulo 3` (accounts) | componente-novo | LOW | Formulário de registro de loja; arquivo novo sem impacto em código existente |
| `accounts/views.py` | `code-analysis.md#Módulo 3` → `signup_view`, `login_view` | regra-nova + regra-alterada | HIGH | `criar_loja_view` nova; `login_view` redireciona dono para dashboard — muda fluxo padrão pós-login |
| `accounts/urls.py` | `code-analysis.md#Módulo 3` | contrato-novo | LOW | Rota `/criar-loja/` adicionada |
| `core/views.py` | `permissions.md#views` | regra-alterada | HIGH | 9 guards `is_staff` substituídos por `user_can_manage_store()`; semântica de acesso expandida |
| `core/admin.py` | `code-analysis.md#2.8 Admin Django` | regra-alterada | LOW | `StoreAdmin.list_display` e `readonly_fields` atualizados para incluir `owner` |
| `templates/accounts/login.html` | — (template) | contrato-alterado | LOW | Link "Crie sua loja" adicionado |
| `templates/accounts/criar_loja.html` | — (template) | componente-novo | LOW | Tela nova de onboarding |

---

## Diff conceitual por componente

### `Store` (model)

Campo `owner` (OneToOneField → auth.User, null=True) adicionado. Lojas existentes continuam operacionais com `owner=NULL`. O acesso ao dashboard para essas lojas é preservado via condição `is_staff` no helper `user_can_manage_store`.

### `login_view` (accounts/views.py)

Lógica de redirect pós-autenticação alterada. Antes: `next` param → `index`. Agora: `next` param → (se `owned_store`) `dashboard` → `index`. Clientes sem loja associada continuam indo para `index`; donos de loja são redirecionados automaticamente para o dashboard da loja resolvida pelo TenantMiddleware.

### Dashboard guards (core/views.py)

9 verificações `if not request.user.is_staff` substituídas por `if not user_can_manage_store(request)`. O helper avalia `is_staff OR (owned_store == tenant atual)`. A semântica de `is_staff` é preservada como OR, garantindo backward compatibility. Lojas sem `owner` (existentes) continuam acessíveis apenas via `is_staff`.

---

## Regras Preservadas

Regras 🟢 do `_reversa_sdd/domain.md` que continuam intactas após esta feature:

| Regra | Status |
|-------|--------|
| RN-01: Isolamento de Tenant por ContextVar | ✅ preservada |
| RN-02: Resolução de Tenant em três níveis | ✅ preservada |
| RN-03: Auto-atribuição de Tenant em Save | ✅ preservada |
| RN-04: Checkout requer nome, telefone e endereço | ✅ preservada |
| RN-05: Pedido de convidado e vinculação pós-signup | ✅ preservada |
| RN-06: Limite de 3 endereços por usuário por loja | ✅ preservada |
| RN-07: Snapshot de preço no OrderItem | ✅ preservada |
| RN-08: Pedido de balcão sem PIX | ✅ preservada |
| RN-09: Token MercadoPago por tenant | ✅ preservada |
| RN-10: Fallback mock em desenvolvimento | ✅ preservada |

---

## Regras Modificadas

| Regra | Modificação | Impacto |
|-------|-------------|---------|
| RN-12: Acesso ao dashboard — controle binário via `is_staff` | Expandida: `is_staff` permanece como condição suficiente, mas `owned_store == tenant` é adicionado como condição alternativa | Donos de loja agora acessam dashboard sem `is_staff=True`; a semântica binária original é preservada como subconjunto |
