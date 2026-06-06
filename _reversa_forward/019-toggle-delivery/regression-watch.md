# Regression Watch: 019-toggle-delivery

> Feature: `019-toggle-delivery`
> Gerado em: `2026-06-04`
> Referência: `_reversa_forward/019-toggle-delivery/legacy-impact.md`

---

## Watch Items

| ID | Origem | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------|-----------------------------|------|-------------------|
| W001 | `core/models.py` — `Store` | Modelo `Store` possui campo `delivery_enabled BooleanField(default=True)` | presença | Se re-extração mapear `Store` sem `delivery_enabled`, campo foi removido ou renomeado |
| W002 | `core/views.py` — `checkout()` | Primeira guarda de `checkout()` verifica `store.delivery_enabled` antes de criar qualquer objeto | presença | Se re-extração descrever `checkout()` sem menção a `delivery_enabled`, guarda foi removida |
| W003 | `core/context_processors.py` | Context processor `cart()` inclui chave `delivery_enabled` no dict retornado | presença | Se re-extração descrever o context processor sem essa chave, foi revertido |
| W004 | `core/views.py` — `toggle_delivery_view` | View `POST /dashboard/toggle-delivery/` existe e é restrita a `user_can_manage_store` | presença | Se re-extração não listar essa view ou rota, foi removida |
| W005 | `core/urls.py` | Rota `dashboard/toggle-delivery/` mapeada para `toggle_delivery_view` | presença | Se re-extração não listar essa rota, foi removida de `urls.py` |

---

## Observações (sem peso de regressão)

| Origem | Nota |
|--------|------|
| `roadmap.md#D-06` | Agendamento automático por horário foi descartado; se requisitado no futuro, exige campo `open_time`/`close_time` e tarefa Celery periódica |
| `legacy-impact.md#RN-04` | A guarda de `delivery_enabled` precede a validação de campos — comportamento intencional |

---

## Histórico de re-extrações

<!-- Preenchido pelo agente reverso quando /reversa for executado novamente -->

---

## Arquivadas

<!-- Watch items removidos ou superados ficam aqui -->
