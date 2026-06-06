# Regression Watch: 021-remover-criar-loja

> Feature: `021-remover-criar-loja`
> Gerado por: `/reversa-coding`
> Data: `2026-06-05`

## Watch Items

| ID | Origem | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------|-----------------------------|---------------------|-------------------|
| W001 | `accounts/urls.py` | Nenhuma rota com `name='criar_loja'` registrada no URLconf | ausência | `GET /criar-loja/` retorna algo diferente de 404, ou `reverse('criar_loja')` não levanta `NoReverseMatch` |
| W002 | `accounts/views.py` | Função `criar_loja_view` não existe no módulo | ausência | grep por `criar_loja_view` em `accounts/views.py` retorna match |
| W003 | `accounts/forms.py` | Classe `StoreRegistrationForm` não existe no módulo | ausência | grep por `StoreRegistrationForm` em `accounts/forms.py` retorna match |
| W004 | `templates/accounts/` | Arquivo `criar_loja.html` não existe em disco | ausência | arquivo presente em `templates/accounts/criar_loja.html` |
| W005 | `templates/accounts/login.html` | Nenhuma referência a `criar_loja` ou "Crie sua loja" no template de login | ausência | grep por `criar_loja` em `login.html` retorna match |
| W006 | `accounts/views.py` | `signup_view` e `login_view` continuam presentes e funcionais | presença | grep por `signup_view` ou `login_view` retorna zero matches; ou `/signup/` / `/login/` retornam erro |

## Observações (sem peso de regressão)

- 🟡 `accounts/views.py` importa `transaction` — removido como dead code junto com a view. Sem impacto funcional.

## Histórico de re-extrações

*(será preenchido pelo agente reverso quando `/reversa` for executado novamente)*

## Arquivadas

*(vazio — nenhum item arquivado nesta rodada)*
