# Regression Watch: Taxa de Entrega por Restaurante

> Identificador: `007-taxa-entrega`
> Data: `2026-05-30`
> Gerado por: `/reversa-coding`

---

## Watch Items

| ID | Origem | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------|-----------------------------|--------------------|--------------------|
| W001 | `_reversa_sdd/domain.md#RN-04` + `core/views.py:checkout` | `Order.total_amount` = subtotal dos itens + `Order.delivery_fee` em todos os pedidos online | presença | `total_amount` igual ao subtotal dos itens quando `delivery_fee > 0` |
| W002 | `_reversa_sdd/domain.md#RN-04` + `core/views.py:checkout` | `Order.delivery_fee` snapshot imutável: alterar `Store.delivery_fee` não muda pedidos já criados | redação | `order.delivery_fee` diferente de `store.delivery_fee` no momento da criação |
| W003 | `_reversa_sdd/domain.md#RN-08` + `core/views.py:manager_create_order` | Pedidos de balcão (`delivery_address = "Balcão / Retirada"`) sempre têm `Order.delivery_fee = 0.00` | presença | `delivery_fee > 0` em qualquer `Order` com `delivery_address` contendo "Balcão" |
| W004 | `_reversa_sdd/erd-complete.md#STORE` | `Store` possui campos `delivery_fee` (decimal, default 0.00) e `free_delivery_threshold` (decimal nullable) | presença | Campos ausentes no modelo ou na migration |
| W005 | `_reversa_sdd/erd-complete.md#ORDER` | `Order` possui campo `delivery_fee` (decimal, default 0.00) | presença | Campo ausente no modelo ou na migration |

---

## Observações (sem peso de regressão)

> Os itens abaixo originalmente eram 🟡 INFERIDO no `_reversa_sdd/` e não geram watch items obrigatórios, mas merecem atenção em re-extrações futuras.

- **Context processor aditivo:** as 4 novas variáveis (`store_delivery_fee`, `free_delivery_threshold`, `effective_delivery_fee`, `cart_total_with_fee`, `threshold_gap`) são injetadas em todos os templates via o context processor `cart`. Em re-extração, verificar se o context processor ainda retorna todas essas chaves.
- **Mensagem motivacional no drawer:** depende de `threshold_gap` ser `None` quando o threshold está desativado — comportamento 🟡 INFERIDO do cálculo no context processor.

---

## Histórico de re-extrações

### Re-extração 2026-05-30 (verificação inline pós-coding)

> Nota: `_reversa_sdd/` ainda não foi re-extraído com os agentes completos (Scout→Reviewer). Verificação realizada diretamente contra o código gerado na sessão de coding. Re-extração completa recomendada em sessão futura.

| ID | Veredito | Observação |
|----|----------|------------|
| W001 | 🟢 verde | `checkout()` em `core/views.py`: `total_amount=subtotal+effective_fee`, `delivery_fee=effective_fee` — regra preservada |
| W002 | 🟢 verde | `Order.delivery_fee` campo independente gravado no create; sem releitura de `store.delivery_fee` — snapshot intacto |
| W003 | 🟢 verde | `manager_create_order()` em `core/views.py`: `delivery_fee=Decimal('0.00')` explícito — balcão isento confirmado |
| W004 | 🟢 verde | `core/models.py` e migration `0010`: `Store.delivery_fee` e `Store.free_delivery_threshold` presentes com tipos corretos |
| W005 | 🟢 verde | `core/models.py` e migration `0010`: `Order.delivery_fee` presente com default `0.00` |

---

## Arquivadas

> Itens removidos de watch em versões futuras (nenhum por enquanto).
