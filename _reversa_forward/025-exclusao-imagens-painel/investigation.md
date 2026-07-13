# Investigation: Exclusão de Mídia em Django

Este documento contém a investigação técnica sobre os padrões de exclusão física de arquivos de mídia gerenciados pelo Django ORM (`FileField` / `ImageField`) e alternativas de interface.

## 1. Padrões de Exclusão de Arquivos no Django

No Django, quando definimos um campo `ImageField` com `null=True, blank=True` e limpamos o campo associando-o a `None` (ou salvando um formulário que limpa o campo), **o Django não remove fisicamente o arquivo do disco por padrão**. Ele apenas atualiza o banco de dados definindo a coluna correspondente como `NULL` ou string vazia `''`.

Para garantir que o arquivo seja excluído fisicamente (conforme decidido na RN-05/RF-01/RF-02/RF-03), existem duas abordagens recomendadas:

### Abordagem A: Sobrescrita do `save()` do Model ou do Form
Executar a deleção do arquivo de mídia quando a exclusão for solicitada.
No Form:
```python
if self.cleaned_data.get('clear_logo') and instance.logo:
    instance.logo.delete(save=False) # delete() do FileField apaga o arquivo físico
    instance.logo = None
```
*Vantagens*: Risco mínimo de efeitos colaterais em outras partes do sistema, controle explícito no fluxo de entrada do formulário de administração.
*Desvantagens*: Se a deleção ocorrer fora do formulário (ex: via API ou Django Admin padrão), o arquivo físico correspondente não é apagado de forma automatizada (a menos que a mesma lógica seja repetida).

### Abordagem B: Signals `post_delete` e `pre_save`
Utilizar sinais do Django para apagar automaticamente arquivos órfãos.
*Vantagens*: Automatiza a limpeza do disco sempre que o registro é deletado ou alterado de qualquer lugar do sistema.
*Desvantagens*: Sinais no Django podem ser disparados inesperadamente em transações atômicas ou testes de integração, gerando erros colaterais difíceis de rastrear.

**Escolha Técnica**: Adotaremos a **Abordagem A** (lógica no formulário Django) pois limita o impacto apenas à operação conduzida pelo painel de gerenciamento (Manager), garantindo controle total sobre o estado sem introduzir complexidade de sinais globais no ecossistema multi-tenant.

## 2. Alternativas de Interface para Remoção (UX/UI)

### Alternativa 1: Widget nativo `ClearableFileInput`
*Implementação*: Modificar o widget padrão em `forms.py` para usar `forms.ClearableFileInput`.
*Resultado*: O Django insere um checkbox "Limpar" antes do input de arquivo.
*Avaliação*: Quebra a folha de estilos Tailwind CSS e polui visualmente os painéis. A customização desse widget no Django requer sobrescrever templates de widgets globais do framework, o que adiciona ruído e complexidade.

### Alternativa 2: Botão customizado em HTML + Campo Oculto (Hidden Input)
*Implementação*: Adicionar campos booleanos ocultos no formulário e renderizar um botão visual premium (ex: um botão de cor vermelha com ícone de lixeira e texto "Excluir") ao lado da miniatura da imagem existente nos templates.
*Fluxo*: 
1. Quando o botão é clicado, um script JS atualiza o valor do campo oculto (ex: de `False` para `True`) e esconde visualmente a prévia da imagem.
2. No evento de `submit` do formulário, um script verifica se alguma exclusão foi solicitada e emite um alerta `confirm()` nativo ao usuário.
*Avaliação*: Visualmente limpo, 100% controlável com classes do Tailwind CSS e fácil de testar.

**Escolha Técnica**: Adotaremos a **Alternativa 2** para preservar a estética premium e flexibilidade visual do painel de administração.

## 3. Ícones SVG de Talheres (Cutlery) aplicáveis para Placeholder do Cardápio

Como alternativa ao ícone genérico de câmera, utilizaremos um SVG representando um garfo e uma faca cruzados:

```html
<svg class="w-12 h-12 text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M12 2v20M17 5v6a3 3 0 01-3 3h-1m4-9v3m-8 6V2m0 11v9M7 2h0a3 3 0 003 3v2a3 3 0 00-3-3H7z" />
</svg>
```
Este ícone de talheres se integra visualmente com as categorias do cardápio digital (Pizzas, Bebidas, Sobremesas, etc.).
