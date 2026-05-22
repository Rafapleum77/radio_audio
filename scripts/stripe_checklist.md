# 💳 Stripe Payment Links · Checklist 21 produtos (3 moedas)

> Cria cada link em **https://dashboard.stripe.com/payment-links**
> Cola URL gerada no `scripts/stripe_links.json` e roda `python3 scripts/apply_stripe.py`

**Total: 7 produtos × 3 moedas (EUR + USD + BRL) = 21 Payment Links**

**Atalho**: cria primeiro em EUR (7 produtos), depois **duplica cada um pra USD** trocando só a moeda, depois **duplica cada um pra BRL** trocando moeda + valor.

---

## 📋 TABELA DE PREÇOS (referência rápida)

| Produto | EUR | USD | BRL |
|---------|-----|-----|-----|
| Recovery Digital | €20 | $20 | R$100 |
| Recovery Pen Drive | €50 | $50 | R$250 |
| Pacote Completo | €150 | $150 | R$750 |
| VIP Mensal (recurring) | €20/mês | $20/mês | R$100/mês |
| Análise IA Express | €150 | $150 | R$750 |
| Auditoria Multi-IA | €500 | $500 | R$2.500 |
| Curso Soberania Digital | €300 | $300 | R$1.500 |

---

## 🛠️ Setup inicial (uma vez)

1. **Branding** → cor `#f2a900` + logo `radiobitcoin_logo_square.webp`
2. **Customer Portal → Ativar**
3. **Payment Methods → Ativar**: Cartão, **Pix** (BR), Boleto, Apple Pay, Google Pay, Link

---

## 1️⃣ Recovery Digital

**Name**: `BIT ADICT Recovery Kit Digital`
**Description**: Utilitário offline pra validar e recuperar acesso a wallets crypto. ZIP pronto pra rodar + Manual PDF + atualizações grátis. Inclui 4 ferramentas: BIP39 validator, recovery parcial, bruteforce Monero, saldo multi-chain (9 chains). 100% offline, open source.
**Image**: https://radiobitcoin.org/img/bitadict/campanha/02_recovery_kit_49.webp
**Redirect**: `https://radiobitcoin.org/obrigado.html?p=digital` · **Address**: ❌

| Moeda | Preço | JSON key |
|-------|-------|----------|
| EUR | **€20** | `recovery_digital_20_eur` |
| USD | **$20** | `recovery_digital_20_usd` |
| BRL | **R$100** | `recovery_digital_20_brl` |

---

## 2️⃣ Recovery Pen Drive

**Name**: `BIT ADICT Recovery Kit Pen Drive`
**Description**: Recovery Kit gravado em pen drive físico USB 8GB. Manual impresso. Entrega Portugal/Europa em 5 dias. Brasil/mundo via correios. 100% offline, open source.
**Redirect**: `https://radiobitcoin.org/obrigado.html?p=pendrive` · **Address**: ✅

| Moeda | Preço | JSON key |
|-------|-------|----------|
| EUR | **€50** | `recovery_pendrive_50_eur` |
| USD | **$50** | `recovery_pendrive_50_usd` |
| BRL | **R$250** | `recovery_pendrive_50_brl` |

---

## 3️⃣ Pacote Completo

**Name**: `BIT ADICT Pacote Completo`
**Description**: Recovery Kit (digital + pen drive) + código dos 4 bots Polymarket + moeda Bitcoin física + barra de ouro coleção + grupo WhatsApp privado + suporte 90 dias.
**Image**: https://radiobitcoin.org/img/bitadict/campanha/06_og_banner.webp
**Redirect**: `https://radiobitcoin.org/obrigado.html?p=pacote` · **Address**: ✅

| Moeda | Preço | JSON key |
|-------|-------|----------|
| EUR | **€150** | `pacote_completo_150_eur` |
| USD | **$150** | `pacote_completo_150_usd` |
| BRL | **R$750** | `pacote_completo_150_brl` |

---

## 4️⃣ VIP Mensal ⭐ RECORRENTE

**Name**: `BIT ADICT VIP`
**Description**: Grupo VIP WhatsApp com sinais dos 3 bots Polymarket em tempo real. Live semanal sexta 19h BR. Painel de banca aberta. Comunidade educacional sobre soberania digital.
**Image**: https://radiobitcoin.org/img/og/og_vip.webp
**Redirect**: `https://radiobitcoin.org/obrigado.html?p=vip` · **Type**: Recurring Monthly

| Moeda | Preço/mês | JSON key |
|-------|-----------|----------|
| EUR | **€20/mês** | `vip_mensal_20_eur` |
| USD | **$20/mês** | `vip_mensal_20_usd` |
| BRL | **R$100/mês** | `vip_mensal_20_brl` |

---

## 5️⃣ Análise IA Express

**Name**: `Análise Multi-IA Express BIT ADICT`
**Description**: Relatório PDF de 20 páginas auditando 1 área específica do teu setup crypto. 6 IAs analisam (Claude+GPT+Gemini+Manus+Llama+DeepSeek). Entrega em 24h. Zero call humana.
**Redirect**: `https://radiobitcoin.org/obrigado.html?p=mentoria`

| Moeda | Preço | JSON key |
|-------|-------|----------|
| EUR | **€150** | `mentoria_1h_150_eur` |
| USD | **$150** | `mentoria_1h_150_usd` |
| BRL | **R$750** | `mentoria_1h_150_brl` |

---

## 6️⃣ Auditoria Multi-IA

**Name**: `Auditoria Multi-IA BIT ADICT`
**Description**: Auditoria 360° do teu setup crypto: opsec + bots + diversificação + backup + herança. PDF executivo de 80 páginas. 6 IAs analisam. 30 dias VIP grátis. 3 follow-ups WhatsApp em 60 dias.
**Redirect**: `https://radiobitcoin.org/obrigado.html?p=mentoria`

| Moeda | Preço | JSON key |
|-------|-------|----------|
| EUR | **€500** | `mentoria_4h_500_eur` |
| USD | **$500** | `mentoria_4h_500_usd` |
| BRL | **R$2.500** | `mentoria_4h_500_brl` |

---

## 7️⃣ Curso BIT ADICT Soberania Digital

**Name**: `Curso BIT ADICT Soberania Digital`
**Description**: Curso completo 8 módulos · 30+ aulas · ~20h. Bitcoin self-custody · Recovery Kit · opsec · Lightning · Nostr · bots Polymarket · herança. Acesso vitalício. Recovery Kit + 4 bots inclusos. 30 dias VIP grátis. Certificado.
**Image**: https://radiobitcoin.org/img/og/og_curso.webp
**Redirect**: `https://radiobitcoin.org/obrigado.html?p=curso`

| Moeda | Preço | JSON key |
|-------|-------|----------|
| EUR | **€300** | `curso_300_eur` |
| USD | **$300** | `curso_300_usd` |
| BRL | **R$1.500** | `curso_300_brl` |

---

## ⚡ Workflow

1. Cria os 21 links no Stripe (~50min)
2. Cola URLs no `scripts/stripe_links.json`
3. Roda `python3 scripts/apply_stripe.py`
4. Site fica com botões Stripe + WhatsApp em todas as landings

**Modo TEST primeiro**: valida com cartão `4242 4242 4242 4242` antes de ativar produção.
