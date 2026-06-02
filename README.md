# 🚀 SaaS de Delivery / Loja Virtual (Django Multi-Tenant)

Bem-vindo ao **StoreSaaS**! Este é um sistema completo de e-commerce e delivery do tipo SaaS (Software as a Service), projetado para gerenciar múltiplas lojas de forma isolada e segura. O sistema oferece desde o catálogo de produtos, carrinho de compras e checkout com PIX, até um painel administrativo completo para o gerente da loja.

## ✨ Funcionalidades Principais

### 🏢 Multi-Tenant (Multi-lojas)
- **Isolamento Lógico**: Cada loja tem seus próprios produtos, pedidos, clientes e configurações.
- **Middleware Inteligente**: O sistema detecta automaticamente qual loja está sendo acessada (via subdomínio ou configuração).

### 🛒 Experiência do Cliente (Storefront)
- **Catálogo Premium**: Interface responsiva estilo "App de Delivery" com categorias deslizantes e fotos de alta qualidade.
- **Carrinho Inteligente**: 
    - Botão flutuante no mobile.
    - Sincronização em tempo real (Desktop/Mobile).
    - Persistência baseada em sessão.
- **Checkout Simplificado**: 
    - Cadastro rápido ou conversão de convidado para usuário.
    - Autopreenchimento de endereço.
    - Pagamento via **PIX (Mercado Pago)** com QR Code instantâneo.
- **Área do Cliente**: Histórico de pedidos, status em tempo real e gestão de endereços (até 3 endereços salvos).

### 👨‍💼 Painel do Gerente (Dashboard)
- **Visão Geral**: Gráficos de vendas, pedidos do dia e status pendentes.
- **Gestão de Pedidos**: Kanban/Lista para atualizar status (Pendente -> Preparando -> Enviado).
- **Catálogo**: Adicionar/Editar produtos, preços e fotos.
- **Configurações da Loja**:
    - Alterar Nome e Logo da Loja.
    - Configurar **Token do Mercado Pago** (Produção/Teste) individualmente por loja.

---

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3.10+, Django 5.x
- **Banco de Dados**: SQLite (Desenvolvimento) / PostgreSQL (Recomendado para Produção)
- **Frontend**: HTML5, TailwindCSS (CDN), HTMX (Interatividade sem recarregar página), Alpine.js (opcional)
- **Pagamentos**: SDK Mercado Pago (Python)
- **Infraestrutura**: Docker & Docker Compose

---

## 🚀 Como Rodar o Projeto (Local)

### Pré-requisitos
- Docker & Docker Compose instalados.

### Passo a Passo

1. **Clone o repositório** (se aplicável).
2. **Inicie os containers**:
   ```bash
   docker-compose up --build
   ```
3. **Acesse a aplicação**:
   - URL: `http://localhost:8000`
   - O sistema criará automaticamente uma loja "Matrix" padrão na migração inicial (se configurado).

4. **Painel Administrativo (Django Admin)**:
   - URL: `http://localhost:8000/admin`
   - Usuário: `admin`
   - Senha: `admin` (ou conforme criado no `createsuperuser`)

---

## ⚙️ Configurações Pós-Deploy

Para deixar a loja pronta para vender, siga estes passos no **Painel do Gerente** (`/dashboard/settings/`):

1. **Identidade da Loja**:
    - Faça login como Gerente/Admin.
    - Vá em **Configurações**.
    - Atualize o **Nome da Loja** e faça upload do **Logo** e **Imagem de Capa** para dar a cara da sua marca.

2. **Pagamentos (Mercado Pago)**:
    - Crie uma conta no [Mercado Pago Developers](https://www.mercadopago.com.br/developers).
    - Crie uma aplicação e obtenha o **Access Token** (pode ser de Teste ou Produção).
    - Cole este token no campo **Token de Acesso** nas Configurações da Loja.
    - **Nota**: Sem isso, o sistema usará um modo "Mock" (Simulação) para testes.

---

## 📦 Deploy em Produção

Recomendações para levar para o ar (AWS, DigitalOcean, Heroku, Railway):

1. **Banco de Dados**: Mude de SQLite para **PostgreSQL**.
2. **Static Files**: Configure o `Whitenoise` (já instalado) ou use S3 para servir arquivos estáticos e de mídia (imagens dos produtos).
3. **Segurança**:
    - No `settings.py`, mude `DEBUG = True` para `False`.
    - Configure `ALLOWED_HOSTS` com o domínio real (ex: `['minaloja.com.br']`).
    - Gere uma nova `SECRET_KEY`.
4. **HTTPS**: Use um proxy reverso (Nginx/Traefik) ou serviços gerenciados para garantir SSL.

---

## 🤝 Contribuição

Este projeto foi desenvolvido com foco em clean code, modularidade e experiência do usuário. Sinta-se à vontade para abrir Issues ou Pull Requests para melhorias!

---
*Desenvolvido com 💜 por Antigravity*
