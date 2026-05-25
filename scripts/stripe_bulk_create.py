#!/usr/bin/env python3
"""
Cria todos Products + Prices + Payment Links no Stripe de uma vez.
Idempotente: usa metadata bitadict_slot pra detectar e pular existentes.
Output: imprime mapa slot -> URL e grava em stripe_links.json.
"""
import os, sys, json, time
import stripe

ENV = "/Users/rafaelrioscrosara/Bots/.env"
LINKS_JSON = "/Users/rafaelrioscrosara/Desktop/radio_audio/scripts/stripe_links.json"
SUCCESS_URL = "https://radiobitcoin.org/obrigado.html?p={slug}"

# Carrega chave
for line in open(ENV):
    if line.startswith("STRIPE_SECRET_KEY="):
        stripe.api_key = line.strip().split("=", 1)[1]
        break
assert stripe.api_key, "STRIPE_SECRET_KEY não encontrada em " + ENV

# Catálogo: (slot_base, nome, descricao, slug_obrigado, recorrente, [(moeda, amount_minor)])
# amount_minor: BRL/USD/EUR usam centavos (×100)
CATALOGO = [
    ("recovery_digital_20",
     "BIT ADICT Recovery Kit Digital",
     "Utilitario offline pra validar e recuperar acesso a wallets crypto. ZIP + Manual PDF + 4 ferramentas. 100% offline, open source.",
     "digital", False,
     [("eur", 2000), ("usd", 2000), ("brl", 10000)]),
    ("recovery_pendrive_50",
     "BIT ADICT Recovery Kit Pen Drive",
     "Recovery Kit gravado em pen drive USB 8GB + manual impresso. Entrega Portugal/Europa 5 dias, Brasil/mundo via correios.",
     "pendrive", False,
     [("eur", 5000), ("usd", 5000), ("brl", 25000)]),
    ("pacote_essencial_100",
     "BIT ADICT Pacote Essencial",
     "Recovery Kit Digital + acesso ao grupo WhatsApp privado + suporte 30 dias.",
     "essencial", False,
     [("eur", 10000), ("usd", 10000), ("brl", 50000)]),
    ("pacote_avancado_150",
     "BIT ADICT Pacote Avancado",
     "Recovery Kit Digital + Pen Drive + grupo WhatsApp privado + suporte 60 dias.",
     "avancado", False,
     [("eur", 15000), ("usd", 15000), ("brl", 75000)]),
    ("pacote_completo_200",
     "BIT ADICT Pacote Completo",
     "Recovery Kit (digital + pen drive) + codigo dos 4 bots Polymarket + moeda Bitcoin fisica + barra de ouro colecao + grupo WhatsApp privado + suporte 90 dias.",
     "pacote", False,
     [("eur", 20000), ("usd", 20000), ("brl", 100000)]),
    ("vip_mensal_20",
     "BIT ADICT VIP",
     "Acesso mensal ao grupo VIP, sinais bots Polymarket em tempo real, sessoes ao vivo. Cancela quando quiser.",
     "vip", True,  # recurring
     [("eur", 2000), ("usd", 2000), ("brl", 10000)]),
    ("curso_300",
     "BIT ADICT Curso Soberania Digital",
     "Curso completo de soberania digital: wallets cold, Tor, OPSEC, Nostr, evasao de censura, recovery, multi-sig.",
     "curso", False,
     [("eur", 30000), ("usd", 30000), ("brl", 150000)]),
]

def find_existing_link(slot_key):
    """Procura Payment Link com metadata bitadict_slot == slot_key (1 página, 100 links max)."""
    links = stripe.PaymentLink.list(limit=100, active=True)
    for l in links.auto_paging_iter():
        if l.metadata.get("bitadict_slot") == slot_key:
            return l.url
    return None

def find_or_create_product(slot_base, name, description):
    """Busca product por metadata bitadict_product_slot, cria se nao existir."""
    products = stripe.Product.list(limit=100, active=True)
    for p in products.auto_paging_iter():
        if p.metadata.get("bitadict_product_slot") == slot_base:
            return p
    p = stripe.Product.create(
        name=name,
        description=description,
        metadata={"bitadict_product_slot": slot_base},
    )
    print(f"  + Product criado: {p.id} ({slot_base})")
    return p

def find_or_create_price(product_id, currency, unit_amount, recurring, slot_key):
    """Busca price ativa do product na moeda+amount+recorrencia. Cria se nao existir."""
    prices = stripe.Price.list(product=product_id, active=True, limit=100)
    for pr in prices.auto_paging_iter():
        if (pr.currency == currency
                and pr.unit_amount == unit_amount
                and bool(pr.recurring) == recurring):
            return pr
    args = dict(
        product=product_id,
        currency=currency,
        unit_amount=unit_amount,
        metadata={"bitadict_slot": slot_key},
    )
    if recurring:
        args["recurring"] = {"interval": "month"}
    pr = stripe.Price.create(**args)
    print(f"  + Price criada: {pr.id} ({currency} {unit_amount/100})")
    return pr

def create_payment_link(price_id, slot_key, slug):
    pl = stripe.PaymentLink.create(
        line_items=[{"price": price_id, "quantity": 1}],
        after_completion={
            "type": "redirect",
            "redirect": {"url": SUCCESS_URL.format(slug=slug)},
        },
        metadata={"bitadict_slot": slot_key},
        allow_promotion_codes=True,
    )
    return pl.url

def main():
    out = json.load(open(LINKS_JSON))
    created, skipped, errors = 0, 0, []
    for slot_base, name, desc, slug, recurring, moedas in CATALOGO:
        print(f"\n=== {slot_base} ({name}) ===")
        try:
            product = find_or_create_product(slot_base, name, desc)
        except Exception as e:
            errors.append(f"{slot_base}: product {e}")
            print(f"  ERR product: {e}")
            continue
        for currency, amount in moedas:
            slot_key = f"{slot_base}_{currency}"
            existing = out.get(slot_key, "").strip()
            # pula se ja preenchido com URL prod
            if existing.startswith("https://buy.stripe.com/") and not existing.startswith("https://buy.stripe.com/test_"):
                print(f"  - {slot_key}: ja preenchido localmente, pulando")
                skipped += 1
                continue
            # busca link existente no Stripe (idempotencia cross-run)
            url = find_existing_link(slot_key)
            if url:
                print(f"  ✓ {slot_key}: encontrado no Stripe -> {url}")
                out[slot_key] = url
                skipped += 1
                continue
            try:
                price = find_or_create_price(product.id, currency, amount, recurring, slot_key)
                url = create_payment_link(price.id, slot_key, slug)
                out[slot_key] = url
                print(f"  ★ {slot_key}: CRIADO -> {url}")
                created += 1
                time.sleep(0.3)  # rate limit gentle
            except Exception as e:
                errors.append(f"{slot_key}: {e}")
                print(f"  ERR: {e}")
    # atualiza _status
    preenchidos = sum(1 for k, v in out.items()
                      if not k.startswith("_")
                      and v.strip().startswith("https://buy.stripe.com/")
                      and not v.strip().startswith("https://buy.stripe.com/test_"))
    total = sum(1 for k in out if not k.startswith("_"))
    out["_status"] = f"{preenchidos}/{total} preenchidos (bulk gerado via API {time.strftime('%Y-%m-%d')})"
    json.dump(out, open(LINKS_JSON, "w"), indent=2, ensure_ascii=False)
    print(f"\n=== Resumo ===")
    print(f"  Criados: {created}")
    print(f"  Ja existentes (pulados): {skipped}")
    print(f"  Erros: {len(errors)}")
    print(f"  Total preenchidos: {preenchidos}/{total}")
    for e in errors:
        print(f"  ! {e}")
    return 0 if not errors else 1

if __name__ == "__main__":
    sys.exit(main())
