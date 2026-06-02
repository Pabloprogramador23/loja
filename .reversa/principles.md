# Princípios do projeto

> Projeto: `loja`
> Data da última alteração: `2026-06-01`
> Mantido por: `/reversa-principles`

## Princípios ativos

### I. Utilidade antes de completude

**Descrição.** O projeto existe para resolver um problema real de um cliente real. Uma feature só entra se há uso imediato e concreto previsto. Não se adiciona algo "porque pode ser útil um dia".

**Exemplo de aplicação.** Uber Direct foi adicionado como opção de entrega, mas o cliente usa motoboy próprio. Pelo princípio I, a integração não deveria ter entrado — não há uso imediato previsto.

**Impacto em templates.**
- `requirements-template.md`: o campo "Motivação" deve incluir referência explícita ao uso real esperado pelo cliente
- `roadmap-template.md`: decisões técnicas devem ser justificadas por necessidade concreta, não por possibilidade futura
- `actions-template.md`: tarefas sem uso imediato mapeado devem ser marcadas como candidatas a corte

**Criado em.** `2026-06-01`
**Última revisão.** `2026-06-01`

---

### II. Integrações essenciais apenas

**Descrição.** Cada integração externa adiciona superfície de falha, custo de manutenção e complexidade de configuração. Só entra uma integração se ela substitui algo que o cliente precisaria fazer manualmente e de forma recorrente.

**Exemplo de aplicação.** MercadoPago é essencial — sem ele não há pagamento online. Google OAuth é opcional — o cliente consegue criar conta com email/senha sem perda real. Login social não entra.

**Impacto em templates.**
- `requirements-template.md`: seção de integrações deve listar a justificativa de essencialidade para cada serviço externo
- `roadmap-template.md`: integrações devem aparecer em fase própria com critério de aceite explícito

**Criado em.** `2026-06-01`
**Última revisão.** `2026-06-01`

---

### III. Configuração simples, operação autônoma

**Descrição.** O dono do restaurante precisa conseguir operar o sistema sem depender do desenvolvedor. Qualquer configuração que exija conhecimento técnico (APIs externas, webhooks, chaves secretas) aumenta a barreira de adoção e vai contra o produto.

**Exemplo de aplicação.** Taxa de entrega com cálculo dinâmico via Google Maps exige que o dono configure uma API key do Google. Taxa fixa + threshold de frete grátis ele configura sozinho no painel. Prefira a segunda.

**Impacto em templates.**
- `requirements-template.md`: toda feature que exija configuração deve descrever quem configura e como (interface no painel vs. variável de ambiente)
- `roadmap-template.md`: priorizar soluções que o usuário final consegue operar de forma autônoma

**Criado em.** `2026-06-01`
**Última revisão.** `2026-06-01`

---

### IV. Produto focado, não showcase

**Descrição.** O projeto não é vitrine de tecnologia. A escolha de uma solução mais simples é sempre preferível à mais sofisticada, mesmo que a sofisticada seja tecnicamente mais interessante.

**Exemplo de aplicação.** Ao escolher entre calcular frete por distância (complexo, externo, com latência de API) e frete fixo configurável (simples, interno, zero dependência) — escolha o fixo. A escolha técnica elegante não agrega valor ao cliente neste contexto.

**Impacto em templates.**
- `requirements-template.md`: o campo "Alternativas consideradas" deve registrar por que a solução mais simples foi ou não adotada
- `roadmap-template.md`: quando duas abordagens resolvem o mesmo problema, documentar a mais simples como padrão preferido

**Criado em.** `2026-06-01`
**Última revisão.** `2026-06-01`

---

## Princípios aposentados

<!-- Nenhum princípio aposentado até o momento. -->

---

## Histórico de alterações

| Data | Operação | Princípio | Resumo |
|------|----------|-----------|--------|
| 2026-06-01 | criar | I | Utilidade antes de completude — versão inicial |
| 2026-06-01 | criar | II | Integrações essenciais apenas — versão inicial |
| 2026-06-01 | criar | III | Configuração simples, operação autônoma — versão inicial |
| 2026-06-01 | criar | IV | Produto focado, não showcase — versão inicial |
