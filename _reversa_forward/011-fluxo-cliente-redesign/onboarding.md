# Onboarding: Localização Pré-Catálogo (011-D)

> Guia executável para testar a feature do zero
> Sem pré-requisito de features anteriores (sem migration, sem config nova)

---

## 0. Pré-requisitos

1. **Servidor rodando:**
   ```
   uvicorn store_saas.asgi:application --reload --port 8000
   ```
2. **Loja ativa** com pelo menos um produto disponível
3. **Browser** com devtools para inspecionar sessão (opcional)

---

## 1. Cenário A — Banner aparece para cliente sem endereço

1. Abra uma aba **anônima** (garante sessão limpa)
2. Acesse `http://127.0.0.1:8000/catalog/` (ou subdomínio da loja)
3. **Resultado esperado:** banner de localização aparece no topo da página com campo de texto e botão GPS

---

## 2. Cenário B — Preencher endereço via texto

1. No banner, digite "Rua das Flores, 42 - Centro"
2. Clique em "Confirmar Endereço"
3. **Resultado esperado:**
   - Banner desaparece
   - Catálogo permanece visível
   - No shell: `request.session.get('session_delivery_address')` → `'Rua das Flores, 42 - Centro'`

---

## 3. Cenário C — Usar GPS

1. No banner, clique em "Usar minha localização"
2. Autorize o acesso à localização no browser
3. **Resultado esperado:**
   - Campo de texto é preenchido com as coordenadas (ex: `-3.7172, -38.5434`)
   - Usuário pode editar antes de confirmar

---

## 4. Cenário D — Endereço pré-preenchido no checkout

1. Após o Cenário B (com endereço na sessão), adicione um produto ao carrinho
2. Abra o carrinho (drawer)
3. **Resultado esperado:**
   - Campo "Endereço Completo" já vem preenchido com "Rua das Flores, 42 - Centro"
   - Usuário pode editar normalmente

---

## 5. Cenário E — Manager não vê o banner

1. Faça login com usuário `is_staff=True`
2. Acesse `/catalog/`
3. **Resultado esperado:** banner não aparece

---

## 6. Cenário F — Dismiss sem preencher

1. Acesse `/catalog/` sem endereço na sessão
2. Clique em "Agora não" (ou botão de fechar do banner)
3. **Resultado esperado:**
   - Banner some
   - Catálogo continua visível
   - Sessão não tem `session_delivery_address` (ou tem `''`)

---

## 7. Checklist de aceite

- [ ] Banner exibido em `/catalog/` sem endereço na sessão
- [ ] Banner não exibido para `is_staff`
- [ ] Banner não exibido quando sessão já tem endereço
- [ ] Confirmar endereço de texto → banner some, sessão atualizada
- [ ] GPS → coordenadas no campo de texto
- [ ] `delivery_address` no cart_drawer pré-preenchido da sessão
- [ ] Dismiss → banner some, catálogo intocado
