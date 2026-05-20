# Stripe Checkout · setup BIT ADICT

## Estratégia: Payment Links (sem código no servidor)

Stripe Payment Links são URLs prontas que tu cria no dashboard e cola direto nas landings. **Não precisa servidor backend, não precisa secret key no código**.

Vantagens:
- Sem deploy de backend
- Stripe cuida de tudo (3-D Secure, anti-fraude, recibo, fatura)
- Aceita cartão, Google Pay, Apple Pay, PIX (BR), boleto (BR), SEPA (EU)
- Webhook pode chamar API tua quando paga (pra criar acesso no VIP)

Desvantagens:
- Taxa Stripe: 2.9% + €0.30 por transação (Europa) ou 3.99% + R$0.39 (BR)
- Sem custom checkout (segue branding Stripe)

## Passo a passo (45 minutos total)

### 1. Criar conta (10 min)
- https://dashboard.stripe.com/register
- País: escolhe **Portugal** (vai pagar imposto lá durante a viagem) ou **Brasil** (Pix nativo)
- Conta business — preenche dados do MEI/empresa
- Verifica email + adiciona conta bancária

### 2. Criar Payment Links (15 min)

Pra cada produto, vai em **Products → Add product**, depois **More options → Create payment link**:

#### Produto 1: Recovery Kit Digital
- Name: `BIT ADICT Recovery Kit Digital`
- Price: **€19** (one-time)
- Após pagamento: **Redirect to** `https://radiobitcoin.org/obrigado-digital.html`
- URL gerada → copia (ex: `https://buy.stripe.com/aEU14m9XB6JS6F2eUU`)

#### Produto 2: Recovery Kit pen drive
- Name: `BIT ADICT Recovery Kit Pen Drive`
- Price: **€49** (one-time)
- Collect address: **Sim** (precisa endereço pra mandar)
- Redirect: `https://radiobitcoin.org/obrigado-pendrive.html`

#### Produto 3: Pacote Completo
- Name: `BIT ADICT Pacote Completo`
- Price: **€149** (one-time)
- Collect address: **Sim**
- Redirect: `https://radiobitcoin.org/obrigado-pacote.html`

#### Produto 4: VIP mensal
- Name: `BIT ADICT VIP`
- Price: **€19** (recurring monthly)
- Redirect: `https://radiobitcoin.org/obrigado-vip.html`

#### Produto 5: Mentoria 1h
- Name: `BIT ADICT Mentoria 1h`
- Price: **€150** (one-time)
- Redirect: `https://radiobitcoin.org/obrigado-mentoria.html`

#### Produto 6: Mentoria 4h
- Name: `BIT ADICT Mentoria Pacote 4h`
- Price: **€497** (one-time)
- Redirect: `https://radiobitcoin.org/obrigado-mentoria.html`

#### Produto 7: Curso pré-venda
- Name: `BIT ADICT Soberania Digital`
- Price: **€297** (one-time)
- Redirect: `https://radiobitcoin.org/obrigado-curso.html`

### 3. Trazer os links pro site (10 min)

Cola cada URL no arquivo `stripe_links.json` (criado abaixo). O script `apply_stripe.py` (também abaixo) percorre as 5 landings e troca os botões WhatsApp pelos Stripe Checkout (mantendo WhatsApp como fallback secundário).

### 4. Páginas de obrigado (5 min)

Pasta `obrigado/` com 7 HTMLs simples agradecendo + próximos passos:
- "Tua compra foi confirmada"
- "Vou te mandar acesso no WhatsApp em até 10min" (digital/VIP)
- "Vou te mandar tracking do envio em até 48h" (pen drive/pacote)

### 5. Webhook (futuro — opcional)

Quando bater 10+ assinantes VIP, faz sentido automatizar:
- Stripe webhook → Cloudflare Worker → adiciona pessoa no grupo VIP WhatsApp
- Por enquanto, manual é melhor (mais pessoal, validação de identidade)

## Imposto e fiscal

**BR (MEI):** Stripe BR emite NFS-e automática (ativa em settings). Pix nativo.
**PT (sócio único):** Stripe PT emite fatura em EUR. SEPA + cartão funcionam direto.

**Decisão:** começa com Stripe BR (Pix BR é killer feature) e ativa Stripe PT depois quando passar 90 dias em Portugal e precisar emitir fatura pra EU.

## Próximos passos

1. Rafael cria conta Stripe (BR primeiro)
2. Cria 7 Payment Links (15 min)
3. Cola URLs no `stripe_links.json`
4. Roda `python3 scripts/apply_stripe.py` (eu deixei pronto)
5. Commit + push → ao vivo

## Fallback: enquanto não tem Stripe

Os botões atuais (WhatsApp) continuam funcionando 100%. Stripe vira **opção primária** (botão dourado) e WhatsApp vira **opção secundária** (botão outline pra quem prefere falar comigo antes).
