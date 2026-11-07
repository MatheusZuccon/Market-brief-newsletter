# Market Brief — Newsletter de investimentos

Landing page para captura de assinantes, construída com Flask, PostgreSQL (Neon), HTML, CSS e JavaScript puros.

## Como executar

1. Entre na pasta do projeto:

   ```bash
   cd newsletter-site
   ```

2. Crie e ative um ambiente virtual (opcional, mas recomendado):

   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure o banco PostgreSQL. Copie `.env.example` para `.env` e preencha `DATABASE_URL` com a conexão do Neon. No PowerShell, também é possível usar:

   ```powershell
   $env:DATABASE_URL="postgresql://..."
   ```

5. Inicie a aplicação:

   ```bash
   python app.py
   ```

5. Abra `http://127.0.0.1:5000` no navegador.

A tabela `subscribers` é criada automaticamente na primeira inicialização.

## Deploy no Vercel

Este projeto já inclui `vercel.json` e usa o runtime Python do Vercel.

1. Importe o repositório no [Vercel](https://vercel.com/new).
2. Em **Settings > Environment Variables**, adicione `DATABASE_URL` com a conexão do Neon para os ambientes necessários.
3. Faça o deploy. O Vercel instalará as dependências de `requirements.txt` automaticamente.

Não salve a URL do banco em arquivos versionados. Como a credencial do Neon foi compartilhada durante a configuração, revogue-a e gere uma nova antes do deploy.

## Estrutura

```
newsletter-site/
├── app.py
├── requirements.txt
├── vercel.json
├── static/
│   ├── css/style.css
│   └── js/script.js
└── templates/index.html
```

## Rotas

- `GET /`: landing page.
- `POST /subscribe`: recebe `first_name`, `last_name` e `email`, valida os dados e registra o assinante.

## Enviar a newsletter pelo Gmail

O script `send_newsletter.py` busca todos os e-mails da tabela `subscribers` no Neon e envia uma mensagem individual para cada pessoa.

1. Ative a verificação em duas etapas na conta Gmail e crie uma **senha de app**. Não use a senha normal da sua conta.
2. Crie ou edite o arquivo HTML da newsletter, por exemplo `newsletter-exemplo.html`. O modelo incluso aceita `{{first_name}}` para personalizar a saudação. Substitua também `https://example.com` pelo link da sua análise e `SEU_EMAIL` pelo e-mail de contato no link de descadastro.
3. Configure as credenciais no terminal atual (PowerShell):

   ```powershell
   $env:DATABASE_URL="postgresql://..."
   $env:NEWSLETTER_SENDER_EMAIL="seuemail@gmail.com"
   $env:NEWSLETTER_GMAIL_APP_PASSWORD="sua-senha-de-app-de-16-digitos"
   ```

4. Faça primeiro uma prévia — nenhum e-mail será enviado:

   ```powershell
   python send_newsletter.py --subject "Market Brief: resumo da semana" --html-file newsletter-exemplo.html
   ```

5. Quando a lista estiver correta, envie de fato:

   ```powershell
   python send_newsletter.py --subject "Market Brief: resumo da semana" --html-file newsletter-exemplo.html --send
   ```

O script pausa 0,5 segundo entre disparos. Altere isso com `--delay 1`, por exemplo. Para proteger contra envios acidentais, `--send` é obrigatório. O HTML é enviado junto com uma alternativa em texto puro, necessária para compatibilidade com todos os clientes de e-mail.

> O script remove automaticamente os espaços de formatação que o Google exibe na senha de app. Ainda assim, nunca compartilhe essa senha ou a salve no código.
