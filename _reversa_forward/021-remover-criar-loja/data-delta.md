# Data Delta: Remover opção "Criar Loja"

> Identificador: `021-remover-criar-loja`
> Data: `2026-06-05`

## Resumo

**Nenhuma alteração no modelo de dados ou banco de dados.**

Esta feature remove exclusivamente código de aplicação (views, forms, urls, templates). O model `Store` permanece inalterado — a criação de novas Stores continua possível via Django Admin pelo superuser.

## Modelos afetados

Nenhum.

## Migrations necessárias

Nenhuma.

## Dados existentes

Stores existentes no banco (`loja1`, `pizzapablo`, etc.) não são afetadas pela remoção do fluxo de auto-cadastro.
