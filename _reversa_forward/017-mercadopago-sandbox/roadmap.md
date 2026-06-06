# Roadmap: Integração Real MercadoPago (Sandbox)

> Identificador: `017-mercadopago-sandbox`
> Data: `2026-06-02`
> Requirements: `_reversa_forward/017-mercadopago-sandbox/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

---

## 1. Resumo da abordagem

A infraestrutura de integração com o MercadoPago **já está completa no código** (SDK, HMAC, token por tenant, Checkout Pro, PIX). O que está pendente são três itens distintos:

**1. Configuração de ambiente** — substituir o token dummy `TEST-0000…` pelo token sandbox real. O `.env.example` já documenta as variáveis; o usuário só precisa preencher o `.env` real.

**2. Três correções de bug que impedem o sandbox de funcionar:**
- `Order` não tem campo `customer_email`, então o email coletado no checkout de convidados é descartado e nunca chega ao MP
- `create_checkout_pro_preference()` usa `order.user.email` que lança `AttributeError` para pedidos de convidado (`order.user = None`)
- `float(order.total_amount)` pode gerar arredondamento em valores como R$ 0,10

**3. Comportamento do mock** — o fallback silencioso para mock quando a API retorna HTTP 403 mascara erros de credencial inválida. Com token sandbox real, uma credencial errada deve exibir erro, não QR Code fictício.

A abordagem é cirúrgica: adicionar campo `customer_email` em `Order`, corrigir os dois pontos que o usam em `payment.py`, ajustar o guard do mock, e configurar o `.env`. Sem novos modelos, sem novos serviços.

---

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Utilidade antes de completude | MercadoPago sandbox tem uso imediato: Pablo precisa testar o fluxo de pagamento antes de ir para produção | respeita |
| II. Integrações essenciais apenas | MP já era a integração eleita; esta feature não adiciona nova integração, apenas ativa a existente corretamente | respeita |
| III. Configuração simples, operação autônoma | As variáveis de ambiente são configuradas uma única vez pelo desenvolvedor; o dono da loja não precisa saber disso | respeita |
| IV. Produto focado, não showcase | As correções são mínimas e diretas; nenhuma abstração nova; nenhuma biblioteca adicional | respeita |

---

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|---------------|--------------------------|-------------|
| D-01 | Adicionar `Order.customer_email` (CharField nullable) | O email do guest é coletado no form mas descartado; é o local natural para persistir — junto dos demais dados do cliente no pedido | Armazenar na sessão: perderia o email após clear() do carrinho | 🟢 |
| D-02 | Passar `order.customer_email` para `create_pix_payment()` e `create_checkout_pro_preference()` | Ambas as funções precisam do email; centralizar no Order evita recoletar do request | Recoletar do POST: impossível fora do contexto do request (webhook, retry) | 🟢 |
| D-03 | Remover o fallback mock para HTTP 403 quando token não é `TEST-0000` | Silenciar o 403 esconde credencial inválida; sandbox real deve falhar visivelmente | Manter mock universal: viola RF-06 e confunde debug | 🟢 |
| D-04 | Substituir `float(order.total_amount)` por `str(order.total_amount)` | MP SDK aceita string; evita arredondamento de float com Decimal | `Decimal` direto: SDK Python do MP pode não aceitar Decimal nativo | 🟡 |
| D-05 | Usar ngrok (ou similar) para expor webhook em desenvolvimento local | MP não consegue chamar localhost; ngrok é a solução padrão de mercado para dev | Endpoint temporário em staging: custo e complexidade maiores | 🟢 |

---

## 4. Premissas

| Premissa | Origem (`requirements.md` seção) | Risco se errada |
|----------|----------------------------------|-----------------|
| `customer_email` já é coletado e validado como obrigatório para guest no formulário de checkout (confirmado em `core/views.py:177` e `templates/core/partials/cart_drawer.html:76`) | Seção 10 — Lacunas | Baixo — verificado no código durante o plano; premissa confirmada, não é mais dúvida |

---

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `Order` model | `_reversa_sdd/code-analysis.md` / `core/models.py` | campo-novo | Adicionar `customer_email = CharField(max_length=254, blank=True, default='')` |
| `views.checkout()` | `core/views.py:230` | regra-alterada | Salvar `customer_email` no `Order` durante a criação |
| `create_checkout_pro_preference()` | `core/payment.py:36-39` | regra-alterada | Substituir `order.user.email` por `order.customer_email or order.user.email` |
| `create_pix_payment()` | `core/payment.py:85` | regra-alterada | Priorizar `order.customer_email` antes de `order.user.email` |
| Mock guard (PIX) | `core/payment.py:104` | regra-alterada | Remover 403 do trigger de mock; mock só ativa para `TEST-0000` |
| `transaction_amount` (PIX) | `core/payment.py:93` | regra-alterada | `float(order.total_amount)` → `str(order.total_amount)` |
| `.env` / `.env.example` | `store_saas/settings.py` | configuração | Preencher `MERCADOPAGO_ACCESS_TOKEN` e `MERCADOPAGO_WEBHOOK_SECRET` reais |

---

## 6. Delta no modelo de dados

- Adicionar `customer_email` (CharField, nullable) em `Order`
- Gerar e aplicar migração Django
- Detalhe completo em: `_reversa_forward/017-mercadopago-sandbox/data-delta.md`

---

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| `POST /api/webhooks/mercadopago` | HTTP (recebido do MP) | `_reversa_forward/017-mercadopago-sandbox/interfaces/webhook-mercadopago.md` |

---

## 8. Plano de migração

1. Preencher `.env` com token sandbox real e webhook secret
2. Aplicar as 5 correções de código em `core/models.py`, `core/views.py` e `core/payment.py`
3. Gerar e rodar migração Django (`makemigrations core`, `migrate`)
4. Subir ngrok apontando para porta 8000 e configurar a URL no painel MP sandbox
5. Reiniciar servidor e worker Celery
6. Testar o fluxo completo: checkout → QR Code real → simular aprovação no painel MP sandbox → verificar `Order.status = PREPARING`

---

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| MP sandbox rejeitar o email do guest mesmo sendo válido | Médio — bloqueia checkout guest | Baixo | Usar email de teste sandbox bem formado; MP sandbox é tolerante com domínios |
| ngrok URL muda a cada restart (plano free) | Baixo — precisa reconfigurar webhook no painel MP a cada restart | Alto (plano free) | Usar ngrok com subdomínio fixo (plano pago) ou tunel estável alternativo; ou resetar manualmente |
| Migração em banco com dados existentes | Baixo — campo nullable com default `''` | Baixo | `blank=True, default=''` garante compatibilidade com rows existentes sem UPDATE |
| MP retornar 201 mas sem `point_of_interaction` (edge case sandbox) | Médio — `qr_code` seria None | Baixo | Código já faz `.get()` em vez de acesso direto; retornaria None no payload sem crash |

---

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] QR Code real exibido no checkout (não o pixel 1×1)
- [ ] Webhook recebe notificação do MP sandbox e transiciona pedido para PREPARING
- [ ] `Order.customer_email` salvo para pedidos de convidado
- [ ] Erro real de API (credencial inválida) exibe mensagem — não mock silencioso
- [ ] `regression-watch.md` gerado

---

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-02 | Versão inicial gerada por `/reversa-plan` | reversa |
