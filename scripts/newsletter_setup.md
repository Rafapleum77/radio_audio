# Newsletter BIT ADICT · setup

## Decisão: **Buttondown** (não Substack)

**Por quê não Substack:**
- Substack pega 10% do que tu fatura — caro pra escala
- Substack tem branding deles muito forte (parece "blog do Rafael no Substack")
- Migrar lista depois é doloroso

**Por quê Buttondown:**
- Plano free até 100 assinantes (~3 meses de teste)
- Plano pago US$9/mês até 1k assinantes (sem % por venda)
- Custom domain (`newsletter.radiobitcoin.org`) no plano pago
- Sem branding na newsletter (parece tua)
- Exporta lista em CSV a qualquer hora (sem prisão de plataforma)
- Aceita pagamento via Stripe (assinatura paga)

## Setup operacional

### 1. Criar conta
- https://buttondown.com/register
- Subdomínio sugerido: `radiobitcoin` (vira `buttondown.com/radiobitcoin`)
- Plano: Free até validar (100 leads)

### 2. Configurar
- **Branding**: cor primária `#f2a900`, logo `radiobitcoin_logo_square.webp`
- **Welcome email**: mandar link do eBook "10 erros" automaticamente
- **Custom domain (futuro)**: `newsletter.radiobitcoin.org` (CNAME em GitHub Pages → buttondown)
- **Tag dos leads**: source = "ebook-10-erros" pra rastrear

### 3. Integrar com `ebook.html`
- Substituir o `formsubmit.co` por API do Buttondown:
  ```js
  fetch('https://api.buttondown.com/v1/subscribers', {
    method: 'POST',
    headers: {
      'Authorization': 'Token BUTTONDOWN_API_KEY',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({email, tags: ['ebook-10-erros']})
  })
  ```
- **API key**: pegar em https://buttondown.com/settings/api → guardar em `.env` (NUNCA no JS público)
- **Solução pública**: usar um endpoint serverless (Cloudflare Worker / Vercel) que recebe email + chama Buttondown com a key escondida. Template em `scripts/buttondown_worker.js` (criar quando ativarmos).

### 4. Estratégia de conteúdo

**Frequência:** 1 email/semana (sexta 9h BR).

**Estrutura do email:**
- **Esta semana nos bots** (3 linhas — PnL real, win rate, novidade)
- **Análise da carteira** (1 ação que entrou ou saiu, por quê)
- **Tópico educacional** (1 dos 10 erros do eBook, expandido)
- **Link único** (sempre apontando pra um produto BIT ADICT — VIP, Mentoria, Curso ou Recovery Kit)

### 5. Plano de monetização

- **Tier free**: newsletter semanal aberta (build audience)
- **Tier paga €9/mês**: análise quantitativa da carteira + sinais semanais consolidados dos bots + acesso ao histórico completo
- **Stripe via Buttondown**: setup direto no painel, sem precisar Stripe separado

### 6. Primeiro email pronto

Salvo em `/Users/rafaelrioscrosara/Bots/radio/scripts/newsletter_email_001.md`.
Quando criar conta no Buttondown, copia/cola lá.

## Métricas pra acompanhar

- Open rate (>40% saudável)
- Click rate (>5% saudável)
- Conversão newsletter → VIP/Curso
- Unsubscribe rate (<1% por email saudável)

## Próximos passos

1. Rafael cria conta Buttondown (5 min)
2. Configura branding + welcome email com link do eBook (10 min)
3. Quando tiver API key, eu atualizo o `ebook.html` pra mandar direto
4. Quando bater 100 subs, sobe pro plano pago + custom domain
5. Quando bater 500 subs, ativa o tier €9/mês

## Alternativa caso Buttondown não sirva

- **Ghost self-hosted**: €5/mês na DigitalOcean, controle total, sem % por venda. Mais trabalho de manutenção (4-8h setup).
- **Listmonk** (open source, free): hospedado contigo, zero custo recorrente, mas precisa mailgun/postmark pro envio (US$10/mês).
- **Mailerlite**: free até 1000 subs, similar ao Buttondown mas mais "businessy".
