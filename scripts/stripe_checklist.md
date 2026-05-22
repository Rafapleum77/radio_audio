# 💳 Stripe Payment Links · Checklist 14 produtos

> Cria cada link em **https://dashboard.stripe.com/payment-links**
> Cola URL gerada no `scripts/stripe_links.json` e roda `python3 scripts/apply_stripe.py`

**Setup geral** (uma vez):
- Dashboard → Settings → Branding → cor `#f2a900` + logo `radiobitcoin_logo_square.webp`
- Dashboard → Settings → Customer Portal → ativa (clientes podem gerenciar assinatura sozinhos)
- Dashboard → Payments → Methods → ativa **Cartão + Apple Pay + Google Pay + Link**

---

## 1️⃣ Recovery Kit Digital · EUR (€20)

- **Name**: `BIT ADICT Recovery Kit Digital`
- **Description**:
  > Utilitário offline pra validar e recuperar acesso a wallets crypto. ZIP pronto pra rodar + Manual PDF + atualizações grátis. Inclui 4 ferramentas: BIP39 validator, recovery parcial, bruteforce Monero, saldo multi-chain (9 chains). 100% offline, open source.
- **Price**: `20.00 EUR` · One-off
- **Statement descriptor**: `BITADICT RECOVERY KIT`
- **Image**: https://radiobitcoin.org/img/bitadict/campanha/02_recovery_kit_49.webp
- **After payment**: Custom URL → `https://radiobitcoin.org/obrigado.html?p=digital`
- **Collect address**: ❌ Não (produto digital)

→ **JSON key**: `recovery_digital_20_eur`

---

## 2️⃣ Recovery Kit Digital · USD ($20)

Idêntico ao #1, mas:
- **Price**: `20.00 USD`
- **JSON key**: `recovery_digital_20_usd`

---

## 3️⃣ Recovery Kit Pen Drive · EUR (€50)

- **Name**: `BIT ADICT Recovery Kit Pen Drive`
- **Description**:
  > Recovery Kit gravado em pen drive físico USB 8GB. Manual impresso. Entrega Portugal/Europa em 5 dias. Brasil/mundo via correios. 100% offline, open source.
- **Price**: `50.00 EUR` · One-off
- **Statement**: `BITADICT PEN DRIVE`
- **Image**: https://radiobitcoin.org/img/bitadict/campanha/02_recovery_kit_49.webp
- **Redirect**: `https://radiobitcoin.org/obrigado.html?p=pendrive`
- **Collect address**: ✅ Sim (precisa endereço entrega)
- **Shipping**: define preço de envio depois (ou inclui no preço base)

→ **JSON key**: `recovery_pendrive_50_eur`

---

## 4️⃣ Recovery Kit Pen Drive · USD ($50)
Igual #3, **Price**: `50.00 USD`, **JSON key**: `recovery_pendrive_50_usd`

---

## 5️⃣ Pacote Completo · EUR (€149)

- **Name**: `BIT ADICT Pacote Completo`
- **Description**:
  > Pacote completo BIT ADICT: Recovery Kit (digital + pen drive) + código dos 4 bots Polymarket (DIRECIONAL/XRP/ARBITRAGE/SOL) + moeda Bitcoin física + barra de ouro coleção + grupo WhatsApp privado de updates + suporte direto 90 dias.
- **Price**: `150.00 EUR` · One-off
- **Statement**: `BITADICT PACOTE`
- **Image**: https://radiobitcoin.org/img/bitadict/campanha/06_og_banner.webp
- **Redirect**: `https://radiobitcoin.org/obrigado.html?p=pacote`
- **Collect address**: ✅ Sim

→ **JSON key**: `pacote_completo_149_eur`

---

## 6️⃣ Pacote Completo · USD ($149)
Igual #5, **Price**: `150.00 USD`, **JSON key**: `pacote_completo_149_usd`

---

## 7️⃣ VIP Mensal · EUR (€20/mês) ⭐ RECORRENTE

- **Name**: `BIT ADICT VIP`
- **Description**:
  > Acesso ao grupo VIP WhatsApp com sinais dos 3 bots Polymarket em tempo real. Live semanal de revisão (sexta 19h BR). Painel de banca aberta. Comunidade educacional sobre soberania digital.
- **Price**: `20.00 EUR` · **Recurring** · Monthly
- **Statement**: `BITADICT VIP`
- **Image**: https://radiobitcoin.org/img/og/og_vip.webp
- **Redirect**: `https://radiobitcoin.org/obrigado.html?p=vip`
- **Customer portal**: ✅ Sim (clientes podem cancelar sozinhos)

→ **JSON key**: `vip_mensal_20_eur`

---

## 8️⃣ VIP Mensal · USD ($20/mês)
Igual #7, **Price**: `20.00 USD` recurring monthly, **JSON key**: `vip_mensal_20_usd`

---

## 9️⃣ Análise IA Express · EUR (€150)

- **Name**: `Análise Multi-IA Express BIT ADICT`
- **Description**:
  > Relatório PDF de 20 páginas auditando 1 área específica do teu setup crypto (opsec OU bots OU diversificação OU backup). 6 IAs analisam (Claude+GPT+Gemini+Manus+Llama+DeepSeek). Entrega em 24h. Zero call humana.
- **Price**: `150.00 EUR` · One-off
- **Statement**: `BITADICT IA EXPRESS`
- **Image**: https://radiobitcoin.org/img/og/og_mentoria.webp
- **Redirect**: `https://radiobitcoin.org/obrigado.html?p=mentoria`

→ **JSON key**: `mentoria_1h_150_eur`

---

## 🔟 Análise IA Express · USD ($150)
Igual #9, **Price**: `150.00 USD`, **JSON key**: `mentoria_1h_150_usd`

---

## 1️⃣1️⃣ Auditoria Multi-IA · EUR (€500)

- **Name**: `Auditoria Multi-IA BIT ADICT`
- **Description**:
  > Auditoria 360° do teu setup crypto: opsec + bots + diversificação + backup + herança. PDF executivo de 80 páginas. 6 IAs analisam em paralelo. 30 dias VIP grátis incluso. 3 follow-ups WhatsApp em 60 dias. Re-análise grátis após 6 meses.
- **Price**: `500.00 EUR` · One-off
- **Statement**: `BITADICT AUDITORIA`
- **Redirect**: `https://radiobitcoin.org/obrigado.html?p=mentoria`

→ **JSON key**: `mentoria_4h_500_eur`

---

## 1️⃣2️⃣ Auditoria Multi-IA · USD ($500)
Igual #11, **Price**: `500.00 USD`, **JSON key**: `mentoria_4h_500_usd`

---

## 1️⃣3️⃣ Curso BIT ADICT Soberania Digital · EUR (€300) PRÉ-VENDA

- **Name**: `Curso BIT ADICT Soberania Digital`
- **Description**:
  > Curso completo 8 módulos · 30+ aulas · ~20h conteúdo. Bitcoin self-custody · Recovery Kit · opsec · Lightning · Nostr · bots Polymarket · herança. Acesso vitalício + atualizações grátis. Recovery Kit Digital incluso. Código dos 4 bots incluso. 30 dias VIP grátis. Certificado conclusão.
- **Price**: `300.00 EUR` · One-off
- **Statement**: `BITADICT CURSO`
- **Image**: https://radiobitcoin.org/img/og/og_curso.webp
- **Redirect**: `https://radiobitcoin.org/obrigado.html?p=curso`

→ **JSON key**: `curso_300_eur`

---

## 1️⃣4️⃣ Curso · USD ($300)
Igual #13, **Price**: `300.00 USD`, **JSON key**: `curso_300_usd`

---

## ⚡ Workflow recomendado pra ti

1. Cria os 14 links no Stripe (estimo 30-45min — copia/cola das descrições acima)
2. Cada link gera URL `https://buy.stripe.com/...`
3. **Edita `scripts/stripe_links.json`** colocando cada URL na chave correspondente
4. Roda: `python3 scripts/apply_stripe.py`
5. Script atualiza as 5 landings (vip/mentoria/curso/recovery/index) com botões Stripe
6. Commit + push automático

**Modo TEST primeiro**: ativa Test Mode no Stripe (canto sup direito), cria os 14 links em test, valida fluxo end-to-end (pode pagar com cartão 4242 4242 4242 4242), aí desliga test e cria os mesmos 14 em produção.

## 🆘 Truques pra acelerar criação

- **Duplica produto existente**: depois de criar Recovery Kit Digital EUR, no produto clica "..." → Duplicate → muda só moeda pra USD
- **Atalho**: cria EUR primeiro de todos (7 produtos), depois duplica todos pra USD (7 mais) trocando apenas a moeda
- **Imagens**: sobe 4 imagens uma vez em Branding → reaproveita em todos
