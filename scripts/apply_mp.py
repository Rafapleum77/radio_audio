#!/usr/bin/env python3
"""Aplica os Mercado Pago Checkout links (Pix + cartao + boleto BR) nas landings.

Le scripts/mp_links.json e insere um botao verde "PAGAR COM PIX" ao lado
do botao Stripe (ou WhatsApp, se Stripe ainda nao foi aplicado).

Uso:
    python3 scripts/apply_mp.py
    python3 scripts/apply_mp.py --revert
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINKS_FILE = ROOT / "scripts" / "mp_links.json"

MP_BTN_CLASS = "rb-ba__btn pri"
MP_MARKER = "<!-- MP_BTN -->"
STRIPE_MARKER = "<!-- STRIPE_BTN -->"

# slot_key (com _brl) -> (files, wa_pattern_pra_localizar, label)
MAPPINGS = [
    {"key": "vip_mensal_20_brl",        "files": ["vip.html"],
     "wa_pattern": r"Quero%20o%20BIT%20ADICT%20VIP",
     "label": "💚 PAGAR COM PIX"},
    {"key": "curso_300_brl",            "files": ["curso.html"],
     "wa_pattern": r"Quero%20o%20Curso%20BIT%20ADICT",
     "label": "💚 PAGAR COM PIX"},
    {"key": "recovery_digital_20_brl",  "files": ["recovery.html", "index.html"],
     "wa_pattern": r"Quero%20o%20Recovery%20Kit%20Digital",
     "label": "💚 PAGAR COM PIX"},
    {"key": "recovery_pendrive_50_brl", "files": ["recovery.html", "index.html"],
     "wa_pattern": r"Quero%20o%20Recovery%20Kit%20no%20pen%20drive",
     "label": "💚 PAGAR COM PIX"},
    {"key": "pacote_essencial_100_brl", "files": ["precos.html"],
     "wa_pattern": r"Quero%20o%20Pacote%20Essencial%20BIT%20ADICT",
     "label": "💚 PAGAR COM PIX"},
    {"key": "pacote_avancado_150_brl",  "files": ["precos.html"],
     "wa_pattern": r"Quero%20o%20Pacote%20Avan%C3%A7ado%20BIT%20ADICT",
     "label": "💚 PAGAR COM PIX"},
    {"key": "pacote_completo_200_brl",  "files": ["recovery.html", "index.html"],
     "wa_pattern": r"Quero%20comprar%20o%20Pacote%20BIT%20ADICT",
     "label": "💚 PAGAR COM PIX"},
]


def make_mp_btn(url: str, label: str) -> str:
    return (
        f'{MP_MARKER}<a class="{MP_BTN_CLASS}" '
        f'href="{url}" target="_blank" rel="noopener" '
        f'style="background:linear-gradient(180deg,#00b65a 0%,#008f47 100%);'
        f'color:#fff;border:1px solid rgba(255,255,255,0.2);'
        f'box-shadow:0 4px 14px rgba(0,182,90,0.4);margin-right:8px;">'
        f'{label}</a>'
    )


def revert_mp(html: str) -> tuple[str, int]:
    pattern = re.compile(MP_MARKER + r'<a\s+[^>]*?href="[^"]*"[^>]*>[^<]*</a>\s*')
    return pattern.subn("", html)


def apply_for_mapping(html: str, m: dict, url: str) -> tuple[str, int]:
    # Insere ANTES do botao Stripe (se existir) ou ANTES do WhatsApp (fallback)
    btn_mp = make_mp_btn(url, m["label"])
    # Tenta primeiro inserir antes do STRIPE_BTN do mesmo grupo
    stripe_pattern = re.compile(
        re.escape(STRIPE_MARKER) + r'<a\s+[^>]*?>[^<]*</a>'
    )
    # Heuristica: insere antes do PRIMEIRO botao Stripe associado ao WA da mesma pattern
    wa_pattern = re.compile(
        r'(<a\s+[^>]*?href="https://wa\.me/5561998110979\?text=' + m["wa_pattern"] +
        r'[^"]*"[^>]*>[^<]*</a>)'
    )
    # Busca o bloco (Stripe + WhatsApp) ou só WhatsApp
    # Estrategia: substituir o botao WA por (MP + WA original) — o Stripe ja foi inserido antes do WA
    # entao MP fica ANTES do Stripe (esquerda total)
    pattern = re.compile(
        r'(' + re.escape(STRIPE_MARKER) + r'<a\s+[^>]*?>[^<]*</a>\s*\n?\s*<a\s+[^>]*?href="https://wa\.me/5561998110979\?text=' + m["wa_pattern"] + r'[^"]*"[^>]*>[^<]*</a>)'
    )
    new_html, n = pattern.subn(btn_mp + r"\n      \1", html, count=10)
    if n > 0:
        return new_html, n
    # Fallback: inserir antes do WA mesmo se nao tem Stripe
    new_html, n = wa_pattern.subn(btn_mp + r"\n      \1", html, count=10)
    return new_html, n


def main():
    revert = "--revert" in sys.argv
    if revert:
        modified = 0
        for path in ROOT.glob("*.html"):
            html = path.read_text()
            new_html, n = revert_mp(html)
            if n:
                path.write_text(new_html)
                modified += n
                print(f"✓ {path.name}: removed {n} botao(es) MP")
        print(f"\nTotal: {modified} botoes MP removidos.")
        return

    if not LINKS_FILE.exists():
        print(f"ERRO: {LINKS_FILE} nao existe.", file=sys.stderr)
        sys.exit(1)

    links = json.loads(LINKS_FILE.read_text())
    links = {k: v for k, v in links.items() if not k.startswith("_")}

    # primeiro reverte tudo (idempotencia)
    for path in ROOT.glob("*.html"):
        html = path.read_text()
        new_html, _ = revert_mp(html)
        if new_html != html:
            path.write_text(new_html)

    total = 0
    for m in MAPPINGS:
        url = links.get(m["key"], "").strip()
        if not url or not url.startswith("https://"):
            print(f"  - {m['key']}: sem URL")
            continue
        for fname in m["files"]:
            path = ROOT / fname
            if not path.exists():
                continue
            html = path.read_text()
            new_html, n = apply_for_mapping(html, m, url)
            if n:
                path.write_text(new_html)
                total += n
                print(f"✓ {fname}: {m['key']} ({n} botao)")
    print(f"\nTotal: {total} botoes MP aplicados.")


if __name__ == "__main__":
    main()
