#!/usr/bin/env python3
"""
Cria Preferences Mercado Pago (Checkout Pro) pros 7 produtos em BRL.
Output: scripts/mp_links.json com {slot: init_point_url}
Idempotente: lista preferences existentes via search por external_reference.
"""
import os, sys, json, time
import urllib.request, urllib.parse, urllib.error

ENV = "/Users/rafaelrioscrosara/Bots/.env"
LINKS_JSON = "/Users/rafaelrioscrosara/Desktop/radio_audio/scripts/mp_links.json"
SUCCESS_URL = "https://radiobitcoin.org/obrigado.html?p={slug}"
FAILURE_URL = "https://radiobitcoin.org/{page}"

TOKEN = None
for line in open(ENV):
    if line.startswith("MERCADOPAGO_ACCESS_TOKEN="):
        TOKEN = line.strip().split("=", 1)[1]
        break
assert TOKEN, "MERCADOPAGO_ACCESS_TOKEN nao encontrado em " + ENV

# Catalogo: (slot_key BRL, nome, descricao, slug_obrigado, pagina_falha, preco_brl)
CATALOGO = [
    ("recovery_digital_20_brl",  "BIT ADICT Recovery Kit Digital",
     "Utilitario offline pra validar e recuperar acesso a wallets crypto. ZIP + Manual PDF + 4 ferramentas. 100% offline, open source.",
     "digital", "recovery.html", 100.00),
    ("recovery_pendrive_50_brl", "BIT ADICT Recovery Kit Pen Drive",
     "Recovery Kit gravado em pen drive USB 8GB + manual impresso. Entrega Portugal/Europa 5 dias, Brasil/mundo via correios.",
     "pendrive", "recovery.html", 250.00),
    ("pacote_essencial_100_brl", "BIT ADICT Pacote Essencial",
     "Recovery Kit Digital + acesso ao grupo WhatsApp privado + suporte 30 dias.",
     "essencial", "index.html", 500.00),
    ("pacote_avancado_150_brl",  "BIT ADICT Pacote Avancado",
     "Recovery Kit Digital + Pen Drive + grupo WhatsApp privado + suporte 60 dias.",
     "avancado", "index.html", 750.00),
    ("pacote_completo_200_brl",  "BIT ADICT Pacote Completo",
     "Recovery Kit (digital + pen drive) + codigo dos 4 bots Polymarket + moeda Bitcoin fisica + barra de ouro colecao + grupo WhatsApp privado + suporte 90 dias.",
     "pacote", "index.html", 1000.00),
    ("vip_mensal_20_brl",        "BIT ADICT VIP (mensal)",
     "Acesso mensal ao grupo VIP, sinais bots Polymarket em tempo real, sessoes ao vivo.",
     "vip", "vip.html", 100.00),
    ("curso_300_brl",            "BIT ADICT Curso Soberania Digital",
     "Curso completo: wallets cold, Tor, OPSEC, Nostr, recovery, multi-sig.",
     "curso", "curso.html", 1500.00),
]

API = "https://api.mercadopago.com"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

def http(method, path, body=None):
    url = API + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {e.code} {path}: {body[:300]}")

def search_existing(external_reference):
    """Busca preference por external_reference. Retorna init_point ou None."""
    qs = urllib.parse.urlencode({"external_reference": external_reference, "limit": 1})
    try:
        res = http("GET", f"/checkout/preferences/search?{qs}")
        elements = res.get("elements", [])
        if elements:
            return elements[0].get("init_point")
    except Exception as e:
        print(f"  (search err: {e})")
    return None

def create_preference(slot, title, desc, slug, fail_page, price):
    body = {
        "items": [{
            "title": title,
            "description": desc,
            "quantity": 1,
            "unit_price": float(price),
            "currency_id": "BRL",
        }],
        "back_urls": {
            "success": SUCCESS_URL.format(slug=slug),
            "failure": FAILURE_URL.format(page=fail_page),
            "pending": SUCCESS_URL.format(slug=slug),
        },
        "auto_return": "approved",
        "external_reference": slot,
        "statement_descriptor": "BIT ADICT",
        "payment_methods": {
            "installments": 12,  # parcelamento em ate 12x no cartao
            "default_installments": 1,
        },
        "metadata": {"bitadict_slot": slot},
    }
    res = http("POST", "/checkout/preferences", body)
    return res.get("init_point") or res.get("sandbox_init_point")

def main():
    try:
        out = json.load(open(LINKS_JSON))
    except FileNotFoundError:
        out = {"_doc": "Mercado Pago Checkout Pro - Preferences BRL. Use scripts/apply_mp.py pra injetar botoes."}
    created, skipped, errors = 0, 0, []
    for slot, title, desc, slug, fail_page, price in CATALOGO:
        print(f"\n=== {slot} ({title}) R${price:.2f} ===")
        existing_local = out.get(slot, "").strip()
        if existing_local.startswith("https://"):
            print(f"  - ja preenchido localmente, pulando")
            skipped += 1
            continue
        existing_remote = search_existing(slot)
        if existing_remote:
            print(f"  ✓ achado no MP -> {existing_remote}")
            out[slot] = existing_remote
            skipped += 1
            continue
        try:
            url = create_preference(slot, title, desc, slug, fail_page, price)
            print(f"  ★ CRIADO -> {url}")
            out[slot] = url
            created += 1
            time.sleep(0.3)
        except Exception as e:
            errors.append(f"{slot}: {e}")
            print(f"  ERR: {e}")
    out["_status"] = f"{sum(1 for k,v in out.items() if not k.startswith('_') and v.strip().startswith('https://'))}/{len(CATALOGO)} preenchidos (bulk {time.strftime('%Y-%m-%d')})"
    json.dump(out, open(LINKS_JSON, "w"), indent=2, ensure_ascii=False)
    print(f"\n=== Resumo ===")
    print(f"  Criados: {created}")
    print(f"  Ja existentes: {skipped}")
    print(f"  Erros: {len(errors)}")
    for e in errors:
        print(f"  ! {e}")
    return 0 if not errors else 1

if __name__ == "__main__":
    sys.exit(main())
