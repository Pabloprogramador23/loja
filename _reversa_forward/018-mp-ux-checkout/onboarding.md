# Onboarding: Testando a Feature 018 — MP UX Checkout

> Feature: `018-mp-ux-checkout`
> Data: `2026-06-04`
> Pré-requisito: servidor rodando via `uvicorn store_saas.asgi:application --reload --port 8000`

---

## Cenário 1 — Guest abre MP em nova aba e paga com sucesso (mock)

1. Abra o browser em modo anônimo (para garantir sessão de guest)
2. Acesse `http://127.0.0.1:8000` → adicione qualquer produto ao carrinho
3. Preencha o formulário de checkout:
   - Nome: `Teste Guest`
   - Telefone: `11999999999`
   - Email: `teste@guest.com`
   - Endereço: `Rua Teste, 123`
   - Método: **Pagar Online**
4. Clique em **Confirmar Pedido**
5. **Resultado esperado:**
   - Uma nova aba abre (vai para `/payment/mock/?order_id=N` em ambiente de teste)
   - A aba original exibe `/payment/waiting/?order_id=N` com o número do pedido e status "Aguardando pagamento…"
6. Na nova aba (mock): o mock aprova automaticamente e redireciona para `/payment/success/`
7. Na aba original: o polling HTMX (a cada 5s) detecta que o status mudou de PENDING para PREPARING
8. **Resultado esperado:** tela de espera exibe "Pedido confirmado! 🎉" com link para `/order/N/track/`

---

## Cenário 2 — Guest fecha a aba do MP sem pagar (timeout visual)

1. Repita o Cenário 1 até o passo 4
2. Feche a nova aba do MP **sem pagar**
3. Na aba original, aguarde 10 minutos (ou simule: edite o JS para reduzir o timeout para 30s durante teste)
4. **Resultado esperado:** tela de espera exibe aviso "Não recebemos confirmação do pagamento. Verifique se concluiu o pagamento no MercadoPago." com link para rastrear o pedido

---

## Cenário 3 — Retorno via back_url de falha

1. Acesse diretamente: `http://127.0.0.1:8000/payment/failure/?preference_id=MOCK_PREF_<N>`
   (substituindo `<N>` por um ID de pedido existente no banco)
2. **Resultado esperado:** página exibe o número do pedido, status, e link **"Acompanhar pedido #N"** funcional

---

## Cenário 4 — Retorno via back_url de pending

1. Acesse diretamente: `http://127.0.0.1:8000/payment/pending/?preference_id=MOCK_PREF_<N>`
2. **Resultado esperado:** idem ao Cenário 3 com mensagem de "Pagamento pendente"

---

## Cenário 5 — Popup bloqueado pelo browser

1. No Chrome: `chrome://settings/content/popups` → adicione `127.0.0.1` como bloqueado
2. Execute o Cenário 1
3. **Resultado esperado:** a aba original exibe `/payment/waiting/` com um link clicável "Abrir MercadoPago" (fallback) em vez de abrir automaticamente

---

## Verificação de regressão

Após implementar, verificar que os seguintes fluxos **não quebraram**:

- [ ] Pagamento em entrega (dinheiro/cartão) ainda redireciona para `/payment/success/` sem abrir nova aba
- [ ] Usuário autenticado tem o mesmo comportamento de nova aba que o guest
- [ ] `/order/N/track/` acessível sem login para qualquer `order_id` válido
- [ ] Tela `/payment/success/` ainda funciona quando MP redireciona com `auto_return: approved`
