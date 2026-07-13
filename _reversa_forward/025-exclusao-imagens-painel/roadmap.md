# Roadmap: Exclusão de Imagens no Painel

> Identificador: `025-exclusao-imagens-painel`
> Data: `2026-07-13`
> Requirements: `_reversa_forward/025-exclusao-imagens-painel/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A abordagem consiste em atualizar os formulários do Django ([core/forms.py](file:///c:/Users/Pablo/Desktop/loja/core/forms.py)) e as visualizações correspondentes para gerenciar a exclusão lógica e física das imagens. 

Utilizaremos campos booleanos ocultos auxiliares nos formulários (`clear_logo`, `clear_cover_image`, `clear_image`) para rastrear se o usuário optou por remover a imagem existente. No método `save()` dos formulários, caso o respectivo campo booleano de limpeza seja verdadeiro, o arquivo físico será removido do disco/storage (`media/`) e o valor do modelo será definido como `None`.

Nos templates HTML ([settings.html](file:///c:/Users/Pablo/Desktop/loja/templates/core/manager/settings.html) e [product_form.html](file:///c:/Users/Pablo/Desktop/loja/templates/core/manager/product_form.html)), adicionaremos botões de exclusão visualmente integrados e código JavaScript para gerenciar os inputs ocultos e emitir um modal `confirm()` do navegador antes de salvar as alterações caso alguma exclusão de imagem tenha sido marcada.

Além disso, atualizaremos a exibição do produto sem imagem no catálogo do cliente ([product_list.html](file:///c:/Users/Pablo/Desktop/loja/templates/core/partials/product_list.html)) com um ícone de talheres genérico em formato SVG.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Utilidade antes de completude | A possibilidade de remover imagens inválidas ou incorretas do painel é uma demanda de operação imediata para evitar catálogo inconsistente. | respeita |
| III. Configuração simples, operação autônoma | A operação é realizada diretamente pelo painel de gerenciamento usando ferramentas nativas do navegador (`confirm`), sem dependências externas complexas. | respeita |
| IV. Produto focado, não showcase | A solução adota a manipulação de formulários tradicionais do Django e confirmação via JavaScript simples nativo, evitando frameworks pesados no painel. | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Campos ocultos auxiliares de limpeza (`clear_*`) nos formulários Django | Permite controlar o estado de exclusão com Tailwind customizado de forma atômica no submit, sem depender do layout padrão feio do `ClearableFileInput`. | Injetar o widget nativo do Django `ClearableFileInput` diretamente no formulário (descartado por quebrar o visual premium do Tailwind). | 🟢 |
| D-02 | Exclusão física do arquivo no `save()` do formulário | Garante que o storage do servidor de mídia não fique acumulando arquivos órfãos sem referências. | Manter os arquivos físicos no servidor após desassociação (descartado por violar o RNF de desempenho/armazenamento). | 🟢 |
| D-03 | Confirmação em JavaScript via evento `submit` do form | Fornece um gate de confirmação nativo e confiável no navegador antes que os arquivos sejam apagados permanentemente no servidor. | Botão de exclusão com requisição AJAX imediata via HTMX (descartado por aumentar a complexidade e deletar o arquivo antes do salvamento geral do formulário). | 🟢 |
| D-04 | Atualização do SVG do placeholder do catálogo de clientes | A imagem padrão de produto sem foto será alterada de uma câmera fotográfica para talheres (cutlery), combinando com o tema de cardápio de restaurante. | Esconder totalmente a área de imagem (descartado para manter o alinhamento de grid simétrico dos produtos). | 🟢 |

## 4. Premissas

Nenhuma premissa com dúvidas pendente (todas as dúvidas foram respondidas e acordadas na etapa de clarify).

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `StoreSettingsForm` | `_reversa_sdd/inventory.md#Estrutura-de-Diretórios` (core/forms.py) | regra-alterada | Adicionados campos booleanos `clear_logo` e `clear_cover_image` e sobrescrito o método `save()` para gerenciar exclusão física e lógica das mídias. |
| `ProductForm` | `_reversa_sdd/inventory.md#Estrutura-de-Diretórios` (core/forms.py) | regra-alterada | Adicionado campo booleano `clear_image` e sobrescrito o método `save()` para gerenciar exclusão física e lógica da imagem de produto. |
| Configurações da Loja | `_reversa_sdd/inventory.md#Estrutura-de-Diretórios` (templates/core/manager/settings.html) | contrato-alterado | Atualizado template para incluir botões de exclusão de mídias e script JS de confirmação. |
| Edição de Produto | `_reversa_sdd/inventory.md#Estrutura-de-Diretórios` (templates/core/manager/product_form.html) | contrato-alterado | Atualizado template para incluir botão de exclusão de imagem e script JS de confirmação. |
| Lista de Produtos do Catálogo | `_reversa_sdd/inventory.md#Estrutura-de-Diretórios` (templates/core/partials/product_list.html) | contrato-alterado | Substituído o ícone padrão de câmera pelo ícone SVG de talheres para produtos sem imagem. |

## 6. Delta no modelo de dados

- Resumo das mudanças: Não há alterações estruturais nos modelos de dados (os campos nos modelos já suportam valores nulos e vazios). Apenas as instâncias são modificadas limpando os campos de imagem (`logo = None`, `cover_image = None` ou `image = None`).
- Detalhe completo em: `_reversa_forward/025-exclusao-imagens-painel/data-delta.md`

## 7. Delta de contratos externos

n/a

## 8. Plano de migração

n/a (Nenhum schema de banco de dados foi alterado; a integridade das instâncias existentes permanece intacta).

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Exclusão acidental de arquivos importantes | alto | média | Mitigado pela exigência do modal `confirm()` do navegador no submit do formulário antes de aplicar a deleção física. |
| Falha na deleção física caso o arquivo não exista no disco | baixo | baixa | O método de exclusão verificará explicitamente a existência física do arquivo e o `ImageField` para evitar exceções do tipo `FileNotFoundError` durante o salvamento. |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Interface visual dos formulários com botões de "Remover" integrados
- [ ] Confirmação de pop-up testada e funcional no submit
- [ ] Arquivo físico removido com sucesso de `media/store_logos/`, `media/store_covers/` ou `media/products/` após exclusão
- [ ] Placeholder de talheres SVG exibido no catálogo de clientes para itens sem imagem

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-07-13 | Versão inicial gerada por `/reversa-plan` | reversa |
