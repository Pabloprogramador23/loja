# Requirements: Autenticação Social no Checkout (011-A)

> Identificador: `012-auth-social-checkout`
> Data: `2026-05-30`
> Spec-mãe: `_reversa_forward/011-fluxo-cliente-redesign/requirements.md`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

O checkout atual permite compra anônima (guest): qualquer pessoa finaliza pedido sem conta, com vinculação retroativa frágil via `session['guest_order_id']`. Esta feature elimina o guest checkout e exige identificação no momento de clicar "Finalizar Pedido". Um modal apresenta duas rotas: (A) Google OAuth2 via `django-allauth` — cria sessão Django ao autenticar com conta Google; (B) cadastro/login tradicional com nome, e-mail, celular e senha, mais recuperação de senha por e-mail. Em ambos os casos, o carrinho é preservado e associado à conta sem limpeza, e o fluxo segue direto para pagamento. O painel do manager e a auth de staff (`is_staff`) não são afetados.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/domain.md#RN-05` | Guest checkout: `order.user=null`, `session['guest_order_id']` para vinculação retroativa frágil — **será removido** | 🟢 |
| `_reversa_sdd/code-analysis.md#Módulo accounts` | `signup_view` usa `UserCreationForm`; `login_view` usa `AuthenticationForm`; ambos redirecionam para `index` — **serão estendidos** | 🟢 |
| `_reversa_sdd/code-analysis.md#Módulo accounts` | Vinculação de pedido guest ocorre no `signup_view` via `session['guest_order_id']` — **lógica será movida para o checkout** | 🟢 |
| `_reversa_sdd/architecture.md#ADR-004` | Carrinho em sessão Django (`cart_{tenant_id}`); sem persistência em banco | 🟢 |
| `_reversa_sdd/architecture.md#ADR-005` | ADR-005 formalizou guest checkout + vinculação pós-signup — **este ADR será substituído por ADR-007** | 🟢 |
| `_reversa_sdd/code-analysis.md#Módulo accounts` | `CustomerSignupForm` (feature 010) já tem email obrigatório e celular — **reusável como base** | 🟢 |
| `_reversa_sdd/architecture.md#Stack` | `django-allauth` não está instalado; `social-auth-app-django` não está instalado — nova dependência necessária | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Novo cliente (nunca teve conta) | Fazer primeiro pedido | Monta carrinho → clica "Finalizar" → vê modal → escolhe Google → conta criada → segue para pagamento |
| Cliente recorrente com conta Google | Pedir novamente | Monta carrinho → clica "Finalizar" → vê modal (já tem conta) → Google login instantâneo → segue para pagamento |
| Cliente recorrente com e-mail/senha | Pedir novamente | Monta carrinho → clica "Finalizar" → modal → aba "Entrar" → preenche e-mail/senha → segue para pagamento |
| Novo cliente sem Google | Criar conta com e-mail | Modal → aba "Cadastrar" → preenche nome, e-mail, celular, senha → conta criada → segue para pagamento |
| Cliente esqueceu a senha | Recuperar acesso | Modal → aba "Entrar" → "Esqueci minha senha" → recebe e-mail → redefine → faz login |
| Manager (staff) | Não é afetado | Login via `/accounts/login/` continua igual; nenhuma mudança no painel |

## 4. Regras de negócio novas ou alteradas

1. **RN-22:** O botão "Finalizar Pedido" no drawer do carrinho exige usuário autenticado. Se não autenticado, exibe modal de identificação em vez de prosseguir para o checkout. 🟢
   - Origem: substitui `_reversa_sdd/domain.md#RN-05` (guest checkout eliminado)
   - Tipo: alterada (quebra retrocompatibilidade: guest checkout deixa de existir)

2. **RN-23:** O modal de identificação oferece três abas: "Google", "Entrar" (login com e-mail/senha) e "Cadastrar" (novo cadastro). O usuário deve completar uma delas antes de prosseguir. Não há opção de continuar sem conta. 🟡
   - Tipo: nova

3. **RN-24:** Login via Google usa `django-allauth` com provider `google`. Ao autenticar, o sistema: (a) cria `User` se e-mail não existe; (b) faz login na sessão Django; (c) associa o carrinho atual ao usuário sem limpá-lo; (d) fecha o modal e prossegue para o checkout. 🟡
   - Tipo: nova

4. **RN-25:** Cadastro tradicional coleta: nome completo (`first_name` + `last_name`), e-mail, celular (`UserProfile.phone`), senha. Após salvar, faz login automático na sessão Django, associa carrinho e prossegue. O e-mail deve ser único por `User`. 🟢
   - Origem: `CustomerSignupForm` (feature 010) como base — adicionar `first_name`, `last_name` e celular
   - Tipo: nova

5. **RN-26:** Login tradicional no modal usa e-mail (não username) como identificador. O campo username continua existindo no `User` mas é gerado automaticamente a partir do e-mail. 🟡
   - Tipo: nova

6. **RN-27:** Recuperação de senha: link "Esqueci minha senha" abre o fluxo padrão Django (`PasswordResetView`) via e-mail. O e-mail enviado usa o template padrão do Django (customizável depois). 🟢
   - Tipo: nova (funcionalidade ausente no legado)

7. **RN-28:** Associação do carrinho ao usuário após login/cadastro no modal: os itens do carrinho em sessão (`cart_{tenant_id}`) são preservados sem modificação. Como o carrinho é session-bound e a sessão Django persiste após `login()`, nenhuma migração de dados é necessária — a sessão mantém os itens automaticamente. 🟢
   - Origem: `_reversa_sdd/architecture.md#ADR-004` (carrinho em sessão)
   - Tipo: nova

8. **RN-29:** O modal de identificação é um overlay HTMX carregado via `hx-get` quando o usuário clica "Finalizar Pedido" sem estar autenticado. O modal redireciona para o checkout após autenticação via `window.location.href` (mesmo padrão da feature 010). 🟡
   - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Botão "Finalizar Pedido": se não autenticado, exibe modal de identificação; se autenticado, prossegue direto para checkout | Must | Usuário autenticado não vê o modal; não autenticado vê o modal antes de qualquer ação de checkout | 🟢 |
| RF-02 | Modal com três abas: Google / Entrar / Cadastrar | Must | Modal abre com aba Google selecionada por padrão; navegação entre abas sem fechar o modal | 🟡 |
| RF-03 | Google OAuth2 via `django-allauth`: cria conta se não existe, faz login se existe, preserva carrinho | Must | Clicar em "Continuar com Google" redireciona para OAuth Google; após autorizar, sessão Django ativa e carrinho intacto | 🟡 |
| RF-04 | Cadastro tradicional: nome completo, e-mail, celular, senha (com confirmação); salva `UserProfile.phone` | Must | Formulário valida campos; e-mail único; cria `User` + `UserProfile`; login automático; carrinho intacto | 🟢 |
| RF-05 | Login tradicional no modal: campo e-mail + senha; autenticação via `authenticate()` do Django | Must | Credenciais corretas → sessão Django + carrinho intacto; incorretas → mensagem de erro inline sem fechar o modal | 🟢 |
| RF-06 | Link "Esqueci minha senha" no modal → fluxo Django `PasswordResetView` | Must | Link abre página de recuperação; e-mail enviado com link de reset válido por 24h | 🟢 |
| RF-07 | Após qualquer autenticação bem-sucedida no modal, prosseguir para checkout sem limpeza do carrinho | Must | Itens no carrinho antes do modal permanecem após autenticação | 🟢 |
| RF-08 | `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` configurados como variáveis de ambiente; nunca hardcoded | Must | App inicia sem as vars → Google desabilitado graciosamente (aba Google oculta ou com mensagem); vars presentes → OAuth funcional | 🟢 |
| RF-09 | Painel do manager (`/dashboard/`) e rotas `accounts/login` e `accounts/signup` mantidos sem alteração | Must | Login de staff via `/accounts/login/` continua funcionando; nenhuma rota existente quebrada | 🟢 |
| RF-10 | Username gerado automaticamente a partir do e-mail no cadastro tradicional (ex.: `joao.silva@gmail.com` → `joao.silva`) com sufixo numérico se já existir | Should | Usuário nunca precisa digitar username; colisões resolvidas automaticamente | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Segurança | OAuth callback (`/accounts/google/login/callback/`) protegido por CSRF via `django-allauth` | Padrão do allauth; não requer implementação manual | 🟢 |
| Segurança | `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` apenas em variáveis de ambiente | Risco crítico de exposição se em código | 🟢 |
| Segurança | Fluxo de reset de senha usa token único com expiração de 24h (padrão Django `PasswordResetView`) | Django built-in; sem implementação custom | 🟢 |
| Compatibilidade | `django-allauth` deve coexistir com `AuthenticationMiddleware` e `SessionMiddleware` existentes | `_reversa_sdd/architecture.md#Stack` — middlewares em posições fixas | 🟡 |
| Sem regressão | Autenticação de manager via `/accounts/login/` e sessão `is_staff` não alteradas | Qualquer quebra bloqueia o painel do restaurante | 🟢 |
| UX | Modal deve funcionar corretamente no drawer do carrinho (overlay sobre overlay) sem conflito de z-index | O drawer tem `z-40`; o modal precisa de `z-50` ou superior | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Cliente não autenticado clica em "Finalizar Pedido"
  Dado que o carrinho tem itens e o usuário não está autenticado
  Quando clica em "Finalizar Pedido"
  Então o modal de identificação aparece (não prossegue para checkout)
  E o carrinho permanece com os itens

Cenário: Login via Google — conta nova
  Dado que o modal está aberto e o usuário nunca teve conta
  Quando clica em "Continuar com Google" e autoriza no OAuth
  Então uma conta é criada com nome e e-mail do Google
  E a sessão Django é iniciada
  E o carrinho permanece intacto
  E o sistema prossegue para o checkout

Cenário: Login via Google — conta existente
  Dado que o modal está aberto e o e-mail do Google já está cadastrado
  Quando clica em "Continuar com Google" e autoriza
  Então a conta existente é usada (sem criar duplicata)
  E o carrinho permanece intacto
  E o sistema prossegue para o checkout

Cenário: Cadastro tradicional bem-sucedido
  Dado que o modal está aberto na aba "Cadastrar"
  Quando preenche nome, e-mail único, celular e senha válida e confirma
  Então a conta é criada, login automático ocorre
  E `UserProfile.phone` é salvo com o celular informado
  E o carrinho permanece intacto
  E o sistema prossegue para o checkout

Cenário: Login tradicional com credenciais erradas
  Dado que o modal está aberto na aba "Entrar"
  Quando preenche e-mail ou senha incorretos
  Então uma mensagem de erro aparece inline no modal
  E o modal não fecha
  E o carrinho não é afetado

Cenário: Recuperação de senha
  Dado que o usuário clicou em "Esqueci minha senha" no modal
  Quando informa o e-mail cadastrado e submete
  Então recebe e-mail com link de reset válido por 24h
  E ao clicar no link e definir nova senha, pode fazer login normalmente

Cenário: Manager não é afetado
  Dado que um usuário staff acessa "/accounts/login/"
  Quando faz login com usuário/senha de staff
  Então é redirecionado para o dashboard normalmente
  E nenhum modal de identificação interfere no fluxo
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 — Interceptação do "Finalizar Pedido" | Must | Porta de entrada de toda a feature |
| RF-02 — Modal com abas | Must | UX central; sem isso nada funciona |
| RF-03 — Google OAuth2 | Must | Principal método pedido; requer `django-allauth` |
| RF-04 — Cadastro tradicional | Must | Alternativa ao Google; cobre quem não tem conta Google |
| RF-05 — Login tradicional | Must | Clientes recorrentes sem Google |
| RF-06 — Recuperação de senha | Must | Requisito mínimo de segurança para auth com senha |
| RF-07 — Preservar carrinho | Must | Sem isso o fluxo quebra a cada login |
| RF-08 — Credenciais Google em env vars | Must | Segurança não negociável |
| RF-09 — Sem regressão no manager | Must | Risco crítico de bloquear o painel do restaurante |
| RF-10 — Username automático | Should | Conveniência; não bloqueia o fluxo |

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda.

## 10. Lacunas

Nenhuma lacuna pendente.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-30 | Versão inicial gerada por `/reversa-requirements` | reversa |
