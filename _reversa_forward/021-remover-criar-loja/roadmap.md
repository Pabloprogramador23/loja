# Roadmap: Remover opção "Criar Loja" do sistema

> Identificador: `021-remover-criar-loja`
> Data: `2026-06-05`
> Requirements: `_reversa_forward/021-remover-criar-loja/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A feature é uma **remoção cirúrgica** de 5 pontos bem mapeados no código: 1 rota, 1 view, 1 form, 1 template e 1 link em template. Não há migração de banco de dados, não há contrato externo afetado, não há dado a preservar.

A abordagem é deletar de fora para dentro: primeiro o link de entrada (template `login.html`), depois o template-destino (`criar_loja.html`), depois a rota (urls.py), depois a view e finalmente o form. Esse encadeamento garante que nenhum passo deixa referência viva para um recurso já removido.

`subdomain_validator` e `RESERVED_SUBDOMAINS` em `accounts/forms.py` serão removidos junto com o form, pois não são usados por `CustomerSignupForm` nem `CheckoutSignupForm`.

A remoção não afeta nenhum outro fluxo de autenticação — `signup_view`, `login_view`, `logout_view` e as views de modal de checkout são independentes.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| Non-destructive sobre legado | A remoção é sobre código não-funcional para o produto final (auto-cadastro de tenant nunca foi habilitado em produção); não destrói dados de usuários | respeita |
| Isolamento de tenant | Remoção elimina o único vetor público de criação de tenant — reforça o isolamento | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Deletar o template `criar_loja.html` completamente | Arquivo sem rota acessível vira dead asset; não há valor em manter | Converter rota para 404 mantendo o template | 🟢 |
| D-02 | Remover `StoreRegistrationForm` inteiro (incluindo `subdomain_validator` e `RESERVED_SUBDOMAINS`) | Esses artefatos só existem para servir esse form; nenhum outro form no módulo os usa | Manter validators para eventual uso futuro | 🟢 |
| D-03 | Não criar redirect de `/criar-loja/` → `/login/` | A rota simplesmente deixa de existir (404); não há usuários que precisem de redirecionamento suave em produção | Redirecionar para não quebrar links externos | 🟡 |

## 4. Premissas

Nenhuma premissa — requirements.md não continha marcadores `[DÚVIDA]`.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `criar_loja_view` | `accounts/views.py` | componente-extinto | Função removida |
| `StoreRegistrationForm` | `accounts/forms.py` | componente-extinto | Classe + validators auxiliares removidos |
| Rota `criar-loja/` | `accounts/urls.py` | contrato-removido | Path removido do URLconf |
| Template `criar_loja.html` | `templates/accounts/criar_loja.html` | componente-extinto | Arquivo deletado |
| Link "Crie sua loja" | `templates/accounts/login.html` | regra-alterada | Bloco `<div>` removido (linha 54-57) |

## 6. Delta no modelo de dados

- Resumo das mudanças: **nenhuma** — a feature não toca modelos, migrations nem banco.
- Detalhe completo em: `_reversa_forward/021-remover-criar-loja/data-delta.md`

## 7. Delta de contratos externos

Nenhum contrato externo afetado. A rota `/criar-loja/` era uma rota Django pública sem integração com terceiros.

## 8. Plano de migração

n/a — nenhuma migração de banco de dados necessária.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Algum template ou view referencia `criar_loja` por nome e não foi mapeado | médio | baixo | RF-06: executar grep completo após remoção antes de encerrar |
| O link no login.html está dentro de bloco condicional não mapeado | baixo | baixo | Ler o template completo antes de editar |
| `subdomain_validator` usado em outro lugar não identificado no grep inicial | baixo | baixo | Confirmar com grep antes de remover |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `GET /criar-loja/` retorna 404
- [ ] Tela de login não exibe link "Crie sua loja"
- [ ] Grep por `criar_loja` em `**/*.py` e `**/*.html` retorna zero ocorrências
- [ ] `/signup/` e `/login/` funcionam normalmente
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-05 | Versão inicial gerada por `/reversa-plan` | reversa |
