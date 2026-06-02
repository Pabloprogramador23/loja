# Relatório de Impacto de Princípios — 2026-06-01

> Gerado por `/reversa-principles`
> Princípios adicionados: I, II, III, IV
> Templates analisados: `requirements-template.md`, `roadmap-template.md`, `actions-template.md`

---

## `requirements-template.md`

### Sugestões de ajuste

1. **Campo "Motivação"** — adicionar sub-campo obrigatório:
   > "Uso real esperado: [descreva quem usará, com que frequência e em qual contexto concreto]"
   *(Decorre do Princípio I)*

2. **Seção de integrações** — adicionar coluna de justificativa:
   > "Essencialidade: [por que esta integração não pode ser substituída por solução interna?]"
   *(Decorre do Princípio II)*

3. **Campo "Configuração"** — adicionar distinção explícita:
   > "Quem configura: [ ] Desenvolvedor [ ] Dono da loja via painel"
   *(Decorre do Princípio III)*

4. **Campo "Alternativas consideradas"** — tornar obrigatório quando houver integração externa ou solução complexa:
   > "Alternativa mais simples avaliada: [descreva] — Descartada porque: [motivo]"
   *(Decorre do Princípio IV)*

---

## `roadmap-template.md`

### Sugestões de ajuste

1. **Critério de entrada de fase** — adicionar checklist antes de incluir uma tarefa:
   > "[ ] Tem uso imediato concreto mapeado? (Princípio I)
   > [ ] Depende de integração externa? Se sim, justificativa de essencialidade registrada? (Princípio II)
   > [ ] O dono da loja consegue operar sem o desenvolvedor? (Princípio III)
   > [ ] Existe alternativa mais simples que resolve 80% do problema? (Princípio IV)"

2. **Integrações** — criar fase dedicada com critério de aceite explícito antes de implementar.

---

## `actions-template.md`

### Sugestões de ajuste

1. **Marcador de candidato a corte** — adicionar tag opcional:
   > `[REVISAR: sem uso imediato mapeado]`
   Para tarefas que existem mas não têm uso concreto previsto. *(Princípio I)*

---

## Observação

Aplicar essas sugestões é decisão do desenvolvedor. Este relatório apenas registra onde os princípios criariam valor se refletidos nos templates. Nenhum template foi modificado automaticamente.

---

> Princípios novos ou alterados só passam a valer em features **iniciadas após 2026-06-01**.
> Features em andamento seguem os critérios que tinham quando foram iniciadas.
