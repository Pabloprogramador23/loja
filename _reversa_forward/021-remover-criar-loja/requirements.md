# Requirements: Remover opção "Criar Loja" do sistema

> Identificador: `021-remover-criar-loja`
> Data: `2026-06-05`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

A plataforma possui um fluxo público de auto-cadastro de loja (`/criar-loja/`) que permite que qualquer visitante crie uma nova Store no sistema. Esse fluxo não deve existir no produto atual — o cadastro de lojas é feito manualmente pelo administrador (Pablo). Esta feature remove completamente a rota, a view, o formulário e todos os pontos de entrada que levam o usuário a essa funcionalidade, sem afetar o cadastro de clientes (`/signup/`) nem o fluxo de login.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/inventory.md#Módulos de Negócio` | `accounts/views.py` contém `criar_loja_view` (linha 11); `accounts/urls.py` expõe rota `criar-loja/` (linha 6) | 🟢 |
| `_reversa_sdd/domain.md#Glossário` | **Store (Tenant)** — unidade de negócio isolada, identificada por `subdomain` único. Criação via `StoreRegistrationForm` com campos `store_name` e `subdomain`. | 🟢 |
| `_reversa_sdd/inventory.md#Estrutura de Diretórios` | Template `templates/accounts/criar_loja.html` presente; link "🏪 Crie sua loja" em `templates/accounts/login.html:55` | 🟢 |
| `accounts/forms.py` | `StoreRegistrationForm(UserCreationForm)` com campos adicionais `store_name`, `subdomain`, validador de subdomínio e verificação de unicidade | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Visitante anônimo | Não deve poder criar loja | Acessa `/criar-loja/` diretamente pela URL ou pelo link na tela de login → deve receber 404 ou redirect para login |
| Pablo (admin) | Criar lojas manualmente via Django Admin | Continua usando `/admin/` para criar `Store` — fluxo não afetado por esta feature |
| Cliente da loja | Fazer cadastro como cliente | Usa `/signup/` normalmente — fluxo não afetado |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** O sistema não expõe nenhuma rota pública para criação de Store. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#RN-02` (resolução de tenant) — a criação de novos tenants passa a ser exclusividade do superuser via Django Admin.
   - Tipo: nova (restrição)

2. **RN-02:** A rota `/criar-loja/` retorna 404 ou redireciona para login. 🟢
   - Tipo: alterada (remoção de endpoint)

3. **RN-03:** O link "🏪 Crie sua loja" é removido da tela de login. 🟢
   - Tipo: alterada (remoção de UI)

4. **RN-04:** `StoreRegistrationForm` e `criar_loja_view` são removidos do código — não podem ser instanciados ou acessados por nenhum caminho. 🟢
   - Tipo: removida

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Remover a rota `criar-loja/` de `accounts/urls.py` | Must | `GET /criar-loja/` retorna 404; nenhuma URL com `name='criar_loja'` está registrada no URLconf | 🟢 |
| RF-02 | Remover `criar_loja_view` de `accounts/views.py` | Must | Arquivo não contém a função nem imports de `StoreRegistrationForm` na chamada dessa view | 🟢 |
| RF-03 | Remover `StoreRegistrationForm` de `accounts/forms.py` | Must | Classe não existe mais no módulo; imports de `RESERVED_SUBDOMAINS` e `subdomain_validator` permanecem apenas se usados por outro form (verificar) | 🟢 |
| RF-04 | Remover template `templates/accounts/criar_loja.html` | Must | Arquivo não existe mais em disco | 🟢 |
| RF-05 | Remover link "🏪 Crie sua loja" de `templates/accounts/login.html` (linha 55) | Must | Tela de login não contém referência à URL `criar_loja` nem ao texto "Crie sua loja" no bloco de links | 🟢 |
| RF-06 | Verificar se há outros pontos do sistema referenciando `criar_loja` ou `criar-loja` | Must | Grep em `**/*.py` e `**/*.html` retorna zero ocorrências após a remoção | 🟢 |
| RF-07 | Garantir que `subdomain_validator` e `RESERVED_SUBDOMAINS` em `accounts/forms.py` sejam removidos se não forem usados por nenhum outro form no arquivo | Should | Sem dead code remanescente no módulo | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Segurança | Nenhum endpoint público permite criação de Store após a remoção | A rota era o único ponto de entry público para criação de tenant — removê-la elimina vetor de abuso | 🟢 |
| Regressão | `accounts/signup_view` (cadastro de cliente) e `accounts/login_view` continuam funcionando sem alterações | As duas views são independentes da `criar_loja_view` | 🟢 |
| Regressão | Django Admin continua permitindo criação de Store por superuser | `Store` é um model Django padrão registrado em `admin.py` — não depende do fluxo removido | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Rota criar-loja não existe mais
  Dado que o sistema está rodando
  Quando um visitante acessa GET /criar-loja/
  Então recebe resposta 404

Cenário: Link removido da tela de login
  Dado que o usuário está na tela de login (/login/)
  Quando a página é renderizada
  Então não existe nenhum elemento com o texto "Crie sua loja" ou link para /criar-loja/

Cenário: Cadastro de cliente não é afetado
  Dado que a feature foi aplicada
  Quando um visitante acessa /signup/ e preenche nome de usuário, e-mail e senha válidos
  Então a conta de cliente é criada e o usuário é redirecionado para a index

Cenário: Login continua funcionando
  Dado que a feature foi aplicada
  Quando um usuário existente acessa /login/ e entra com credenciais corretas
  Então é autenticado e redirecionado normalmente (dashboard se owner, index caso contrário)

Cenário: URL criar_loja não referenciada em nenhum template
  Dado que a feature foi aplicada
  Quando se executa grep por 'criar_loja' em todos os .html e .py do projeto
  Então o resultado é vazio
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 Remover rota | Must | Elimina acesso público imediatamente |
| RF-02 Remover view | Must | Elimina código morto e vetor de reativação acidental |
| RF-03 Remover form | Must | Elimina código morto; form não tem outro uso |
| RF-04 Remover template | Must | Elimina arquivo inalcançável |
| RF-05 Remover link no login | Must | Remove ponto de entrada visível ao usuário |
| RF-06 Grep de validação | Must | Garante ausência de referências ocultas |
| RF-07 Limpar dead code (validator/RESERVED) | Should | Higiene de código; não afeta comportamento |

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda. Rode `/reversa-clarify` quando houver `[DÚVIDA]` pendente.

## 10. Lacunas

Nenhuma lacuna identificada — o escopo é cirúrgico e todos os pontos de impacto foram mapeados diretamente no código.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-05 | Versão inicial gerada por `/reversa-requirements` | reversa |
