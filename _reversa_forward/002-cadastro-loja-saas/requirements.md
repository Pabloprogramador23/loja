# Requirements: Cadastro de Loja SaaS (Auto-onboarding)

> Identificador: `002-cadastro-loja-saas`
> Data: `2026-05-26`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Hoje apenas um superuser Django pode criar lojas via `/admin/`. Esta feature entrega o fluxo de auto-onboarding: um empreendedor acessa `/criar-loja/`, preenche um único formulário com seus dados pessoais e os dados da loja, e o sistema cria o usuário e a loja de forma atômica, autenticando-o automaticamente. Complementarmente, o dashboard deixa de exigir o atributo interno `is_staff` e passa a verificar se o usuário logado é o **dono** (`Store.owner`) da loja atual, viabilizando o modelo SaaS autônomo sem intervenção de administrador.

---

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/domain.md#RN-12` | Dashboard restrito a `is_staff=True`; acesso binário sem granularidade por loja | 🟢 |
| `_reversa_sdd/domain.md#glossário` | Papel "Manager" = `is_staff=True`; sem UserProfile, grupos Django ou vínculo User↔Store | 🟢 |
| `_reversa_sdd/permissions.md#papeis` | Nenhum papel de "Dono de Loja" existe; hierarquia plana com quatro papéis | 🟢 |
| `_reversa_sdd/permissions.md#views` | Todas as views do dashboard verificam `if not request.user.is_staff` manualmente por view | 🟢 |
| `_reversa_sdd/code-analysis.md#accounts` | `signup_view` cria apenas usuário comum; sem vínculo a Store nem seleção de papel | 🟢 |
| `_reversa_sdd/architecture.md#multi-tenant` | `Store` identificada por `subdomain` único; TenantMiddleware resolve tenant por host/header/fallback localhost | 🟢 |
| `_reversa_sdd/domain.md#RN-03` | `TenantAwareModel.save()` atribui automaticamente a loja corrente ao criar registros — o dono operará sempre dentro do contexto da sua loja | 🟢 |

---

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| **Empreendedor** (novo) | Abrir sua loja virtual no SaaS sem depender de suporte técnico | Acessa `/criar-loja/`, preenche formulário, cai diretamente no dashboard da sua loja |
| **Dono de Loja** (recorrente) | Gerenciar produtos, pedidos e configurações da loja | Faz login → acessa `/dashboard/` sem necessitar de atributo administrativo concedido manualmente |
| **Superuser** (plataforma) | Manter poder administrativo cross-tenant | Continua acessando o dashboard de qualquer loja via atributo `is_staff`, sem alteração |

---

## 4. Regras de negócio novas ou alteradas

1. **RN-A01:** A criação de loja é atômica — o usuário e a loja são criados na mesma operação indivisível. Se qualquer etapa falhar, nenhum registro é persistido no banco. 🟢
   - Tipo: nova

2. **RN-A02:** `Store` passa a ter um campo `owner` com relação **1-para-1** com o usuário — um usuário pode ser dono de, no máximo, uma loja. A unicidade é garantida no modelo de dados. 🟢
   - Tipo: nova

3. **RN-A03:** Acesso ao dashboard exige que o usuário logado seja o dono da loja atual (`Store.owner == usuário logado`) **ou** possua o atributo de administrador do sistema (`is_staff=True`). A segunda condição preserva o acesso do Superuser e mantém compatibilidade com lojas já existentes. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#RN-12` (regra alterada)
   - Tipo: alterada

4. **RN-A04:** O subdomínio escolhido pelo empreendedor deve conter apenas letras minúsculas, números e hífens. Subdomínios reservados pela plataforma (`www`, `api`, `admin`) são rejeitados com mensagem de erro específica. 🟡
   - Tipo: nova

5. **RN-A05:** Ao concluir o cadastro da loja, o usuário é autenticado automaticamente na sessão e redirecionado para o dashboard da loja recém-criada. 🟡
   - Tipo: nova

6. **RN-A06:** Após qualquer login bem-sucedido, o sistema verifica se o usuário possui uma loja associada via vínculo 1-para-1. Se sim, redireciona automaticamente para o dashboard. Se não (cliente comum), redireciona para a página inicial. Isso permite que o dono da loja acesse o sistema pelo fluxo de login normal sem precisar navegar manualmente até o dashboard. 🟢
   - Tipo: nova

---

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Página `/criar-loja/` acessível publicamente | Must | GET `/criar-loja/` retorna HTTP 200 para visitante não autenticado | 🟢 |
| RF-02 | Formulário com campos: nome de usuário, senha, confirmação de senha, nome da loja, subdomínio | Must | Todos os 5 campos presentes; todos obrigatórios; subdomínio validado por unicidade antes do salvamento | 🟢 |
| RF-03 | Criação de usuário e loja é atômica | Must | Se o subdomínio já existe, nenhum usuário novo é criado; se a criação do usuário falha, nenhuma loja é criada | 🟢 |
| RF-04 | Campo `owner` adicionado ao modelo `Store` | Must | Lojas criadas pelo novo formulário possuem `owner` preenchido; lojas existentes têm `owner` vazio (compatibilidade) | 🟢 |
| RF-05 | Dono acessa `/dashboard/` sem atributo administrativo | Must | Usuário cujo `store.owner == usuário` acessa o dashboard da loja atual e recebe HTTP 200 | 🟢 |
| RF-06 | Superuser mantém acesso ao dashboard de qualquer loja | Must | Usuário com `is_staff=True` acessa dashboard normalmente | 🟢 |
| RF-07 | Subdomínio validado contra formato e lista de reservados | Must | Tentativa com `admin`, `api`, `www` ou caractere inválido exibe erro no formulário; nenhum registro é criado | 🟡 |
| RF-08 | Após cadastro bem-sucedido, usuário é redirecionado para `/dashboard/` já autenticado | Should | POST válido em `/criar-loja/` resulta em sessão autenticada e redirect HTTP 302 para `/dashboard/` | 🟡 |
| RF-09 | Link "Crie sua loja" exibido na tela de login para não autenticados | Should | Tela `/login/` exibe link visível apontando para `/criar-loja/` | 🟡 |
| RF-10 | Após login, dono de loja é redirecionado automaticamente para o dashboard | Must | Usuário com loja associada que faz login via `/login/` recebe redirect para `/dashboard/`; usuário sem loja vai para `/` | 🟢 |

---

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Segurança | Criação de usuário e loja em operação atômica para evitar estado inconsistente (usuário sem loja ou loja sem dono) | Padrão já adotado no checkout — `_reversa_sdd/code-analysis.md#core/views` | 🟢 |
| Segurança | Subdomínio sanitizado via validação explícita antes de persistir, prevenindo valores inesperados no lookup do TenantMiddleware | `_reversa_sdd/architecture.md#multi-tenant`: TenantMiddleware usa `subdomain` como chave de busca direta no banco | 🟢 |
| Compatibilidade | Campo `owner` em `Store` deve aceitar valor vazio para preservar lojas criadas antes desta feature | Lojas existentes não possuem dono definido; acesso via `is_staff` deve continuar funcionando | 🟡 |
| UX | Mensagem de erro distinta para subdomínio já em uso versus subdomínio em formato inválido | Sem esse feedback o empreendedor não sabe o motivo da falha | 🟡 |

---

## 7. Critérios de Aceitação

```gherkin
Cenário: Empreendedor cria loja com dados válidos
  Dado que acesso GET /criar-loja/ como visitante não autenticado
  Quando preencho username="joao", senha válida, nome da loja="Pizza do João", subdomínio="pizzadojoao"
  E envio o formulário
  Então um usuário com username "joao" é criado
  E uma loja com subdomain "pizzadojoao" e owner=joao é criada
  E sou autenticado automaticamente na sessão
  E sou redirecionado para /dashboard/

Cenário: Subdomínio já utilizado por outra loja
  Dado que uma loja com subdomain="pizzadojoao" já existe no sistema
  Quando submeto o formulário de criação de loja com subdomínio="pizzadojoao"
  Então o formulário exibe a mensagem "Este subdomínio já está em uso"
  E nenhum usuário novo é criado
  E nenhuma loja nova é criada

Cenário: Subdomínio reservado pela plataforma
  Quando submeto o formulário com subdomínio="admin"
  Então o formulário exibe a mensagem "Subdomínio reservado"
  E nenhum registro é criado

Cenário: Subdomínio com caractere inválido
  Quando submeto o formulário com subdomínio="Minha Loja!"
  Então o formulário exibe erro de formato de subdomínio
  E nenhum registro é criado

Cenário: Dono acessa o dashboard da sua loja
  Dado que estou autenticado como "joao"
  E a loja atual tem owner=joao
  Quando acesso GET /dashboard/
  Então recebo HTTP 200

Cenário: Usuário sem ownership tenta acessar dashboard
  Dado que estou autenticado como "maria"
  E maria não é owner da loja atual
  E maria.is_staff é False
  Quando acesso GET /dashboard/
  Então sou redirecionado para /

Cenário: Superuser acessa dashboard de qualquer loja
  Dado que estou autenticado como usuário com is_staff=True
  Quando acesso GET /dashboard/
  Então recebo HTTP 200

Cenário: Dono faz login e é redirecionado para o dashboard da sua loja
  Dado que "joao" possui uma loja associada
  Quando "joao" faz login em /login/ com credenciais válidas
  Então é redirecionado automaticamente para /dashboard/

Cenário: Cliente comum faz login e é redirecionado para a home
  Dado que "maria" não possui loja associada
  Quando "maria" faz login em /login/ com credenciais válidas
  Então é redirecionada para /
```

---

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 — Página /criar-loja/ | Must | Ponto de entrada do auto-onboarding; sem ele a feature não existe |
| RF-02 — Formulário completo | Must | Dados mínimos para criar loja válida |
| RF-03 — Criação atômica | Must | Integridade de dados; evita usuários órfãos ou lojas sem dono |
| RF-04 — Campo owner em Store | Must | Base estrutural para toda a feature |
| RF-05 — Dashboard por ownership | Must | Objetivo central; sem isso o SaaS segue exigindo intervenção manual |
| RF-06 — Superuser mantém acesso | Must | Backward compatibility com modelo operacional atual |
| RF-07 — Validação de subdomínio | Must | Segurança e UX; subdomínios inválidos corrompem o roteamento multi-tenant |
| RF-08 — Redirect pós-cadastro | Should | UX importante mas não bloqueia o uso da feature |
| RF-09 — Link na tela de login | Should | Descobribilidade; não é funcional |
| RF-10 — Redirect automático pós-login | Must | Responde à necessidade do dono de entrar diretamente na sua loja |

---

## 9. Esclarecimentos

### Sessão 2026-05-26

- **Q:** O campo `owner` deve ser relação 1-para-1 (um usuário = uma loja) ou 1-para-N (um usuário pode ter múltiplas lojas)?
  **R:** 1-para-1 — um usuário pode ser dono de no máximo uma loja. Restrição garantida no modelo de dados. → aplicado em RN-A02.

- **Q:** Qual a política de acesso ao dashboard para lojas existentes sem `owner` definido, e existe fluxo de atribuição retroativa de dono?
  **R:** O dono faz login e o sistema detecta automaticamente a loja associada, redirecionando para o dashboard. Lojas sem `owner` (criadas antes desta feature) continuam acessíveis exclusivamente via `is_staff`. Não há fluxo de atribuição retroativa. → aplicado em RN-A06 e RF-10.

---

## 10. Lacunas

> Nenhuma lacuna pendente. Todas as dúvidas foram resolvidas na sessão de esclarecimentos de 2026-05-26.

---

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-26 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-05-26 | Dúvidas resolvidas via `/reversa-clarify`: cardinalidade OneToOne, redirect pós-login; adicionados RN-A06 e RF-10 | reversa |
