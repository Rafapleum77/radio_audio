#!/usr/bin/env python3
"""Aplica os Stripe Payment Links nas 5 landings.

Lê scripts/stripe_links.json e, pra cada URL preenchida, insere um botão
"💳 PAGAR COM CARTÃO" antes do botão WhatsApp existente em cada landing.

Uso:
    python3 scripts/apply_stripe.py
    python3 scripts/apply_stripe.py --revert    (remove os botoes Stripe)

O botão WhatsApp continua, virando opção secundária pra quem prefere falar.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINKS_FILE = ROOT / "scripts" / "stripe_links.json"

# Mapeia produto → (arquivo, regex_pra_achar_botao_wa, label_botao_stripe)
# Cada produto tem 3 chaves no JSON: {base}_eur, {base}_usd, {base}_brl
# O botao gerado tem data-stripe-eur/usd/brl e o currency.js troca o href em runtime.
MAPPINGS = [
    # VIP
    {
        "key": "vip_mensal_20",
        "files": ["vip.html"],
        "wa_pattern": r"Quero%20o%20BIT%20ADICT%20VIP",
        "label": "💳 ASSINAR COM CARTÃO",
    },
    # CURSO
    {
        "key": "curso_300",
        "files": ["curso.html"],
        "wa_pattern": r"Quero%20o%20Curso%20BIT%20ADICT",
        "label": "💳 PAGAR COM CARTÃO",
    },
    # RECOVERY digital
    {
        "key": "recovery_digital_20",
        "files": ["recovery.html", "index.html"],
        "wa_pattern": r"Quero%20o%20Recovery%20Kit%20Digital",
        "label": "💳 PAGAR COM CARTÃO",
    },
    # RECOVERY pen drive
    {
        "key": "recovery_pendrive_50",
        "files": ["recovery.html", "index.html"],
        "wa_pattern": r"Quero%20o%20Recovery%20Kit%20no%20pen%20drive",
        "label": "💳 PAGAR COM CARTÃO",
    },
    # PACOTE completo
    {
        "key": "pacote_completo_200",
        "files": ["recovery.html", "index.html"],
        "wa_pattern": r"Quero%20comprar%20o%20Pacote%20BIT%20ADICT",
        "label": "💳 PAGAR COM CARTÃO",
    },
]

STRIPE_BTN_CLASS = "rb-ba__btn pri"
STRIPE_MARKER = "<!-- STRIPE_BTN -->"


def make_stripe_btn(urls: dict, label: str) -> str:
    """urls = {'eur': '...', 'usd': '...', 'brl': '...'} (qualquer combinacao).
    href default aponta pra USD se existir, senao primeiro disponivel.
    O currency.js troca o href em runtime conforme moeda detectada."""
    default = urls.get("usd") or urls.get("eur") or urls.get("brl") or ""
    attrs = " ".join(f'data-stripe-{k}="{v}"' for k, v in urls.items() if v)
    return (
        f'{STRIPE_MARKER}<a class="{STRIPE_BTN_CLASS}" '
        f'href="{default}" {attrs} target="_blank" rel="noopener" '
        f'style="background:linear-gradient(180deg,#635bff 0%,#4b46c7 100%);'
        f'color:#fff;border:1px solid rgba(255,255,255,0.2);'
        f'box-shadow:0 4px 14px rgba(99,91,255,0.4);margin-right:8px;">'
        f'{label}</a>'
    )


def apply_for_mapping(html: str, m: dict, urls: dict) -> tuple[str, int]:
    pattern = re.compile(
        r'(<a\s+[^>]*?class="' + re.escape(STRIPE_BTN_CLASS) +
        r'"[^>]*?href="https://wa\.me/5561998110979\?text=' + m["wa_pattern"] +
        r'[^"]*"[^>]*>[^<]*</a>)'
    )
    btn_stripe = make_stripe_btn(urls, m["label"])
    new_html, n = pattern.subn(btn_stripe + "\n      " + r"\1", html, count=10)
    return new_html, n


def revert_stripe(html: str) -> tuple[str, int]:
    pattern = re.compile(
        STRIPE_MARKER + r'<a\s+[^>]*?href="[^"]*"[^>]*>[^<]*</a>\s*'
    )
    new_html, n = pattern.subn("", html)
    return new_html, n


def main():
    revert = "--revert" in sys.argv

    if revert:
        modified = 0
        for path in ROOT.glob("*.html"):
            html = path.read_text()
            new_html, n = revert_stripe(html)
            if n:
                path.write_text(new_html)
                modified += n
                print(f"✓ {path.name}: removed {n} botão(es) Stripe")
        print(f"\nTotal: {modified} botões removidos.")
        return

    if not LINKS_FILE.exists():
        print(f"ERRO: {LINKS_FILE} não existe.", file=sys.stderr)
        sys.exit(1)

    links = json.loads(LINKS_FILE.read_text())
    links = {k: v for k, v in links.items() if not k.startswith("_")}

    # agrupa as 3 moedas por produto: vip_mensal_20_eur/usd/brl -> vip_mensal_20: {eur,usd,brl}
    by_product: dict[str, dict[str, str]] = {}
    for k, v in links.items():
        if not v or "PREENCHER" in str(v):
            continue
        for suffix in ("_eur", "_usd", "_brl"):
            if k.endswith(suffix):
                base = k[:-4]
                by_product.setdefault(base, {})[suffix[1:]] = v
                break

    if not by_product:
        print("Nada a fazer. Preenche pelo menos 1 URL em scripts/stripe_links.json")
        sys.exit(0)

    # relatorio do que vai aplicar
    for m in MAPPINGS:
        base = m["key"]
        urls = by_product.get(base, {})
        flags = "".join(["✓" if c in urls else "·" for c in ("eur", "usd", "brl")])
        print(f"  {base:30} [{flags}] EUR/USD/BRL")

    # primeiro reverte tudo (pra ser idempotente)
    for path in ROOT.glob("*.html"):
        html = path.read_text()
        new_html, _ = revert_stripe(html)
        if new_html != html:
            path.write_text(new_html)

    # aplica
    total = 0
    for m in MAPPINGS:
        urls = by_product.get(m["key"])
        if not urls:
            continue
        for fname in m["files"]:
            path = ROOT / fname
            if not path.exists():
                continue
            html = path.read_text()
            new_html, n = apply_for_mapping(html, m, urls)
            if n:
                path.write_text(new_html)
                total += n
                moedas = "/".join(sorted(urls.keys())).upper()
                print(f"✓ {fname}: {m['key']} ({moedas}) ({n} botão{'es' if n > 1 else ''})")

    print(f"\nTotal: {total} botões Stripe aplicados.")
    if total == 0:
        print("⚠️  Nenhum botão WhatsApp encontrado nas páginas — talvez já tenha sido aplicado.")


if __name__ == "__main__":
    main()
