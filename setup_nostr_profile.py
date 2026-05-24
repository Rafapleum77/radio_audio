#!/usr/bin/env python3
"""
Configura profile BIT ADICT + publica catalogo atualizado no Nostr.
Usa as funcoes do nostr_broadcaster.py.

Publica 2 eventos:
  - kind 0: metadata (nome, bio, foto, lightning, NIP05)
  - kind 1: post com catalogo atualizado (5 produtos, precos novos, sem mentoria)
"""
import asyncio, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from nostr_broadcaster import make_event, publish_to_relay, RELAYS, PUBKEY_HEX

# ============ METADATA (kind 0) ============

PROFILE = {
    "name": "bitadict",
    "display_name": "BIT ADICT",
    "about": (
        "Operacao Vale Sats Global. Bitcoin self-custody, Recovery Kit "
        "offline, 4 bots Polymarket open-source. radiobitcoin.org "
        "Sem call, sem mentoria, sem promessa de lucro - so soberania automatizada."
    ),
    "picture": "https://radiobitcoin.org/img/bitadict/campanha/v3/pacote_completo_premium.png",
    "banner": "https://radiobitcoin.org/img/bitadict/campanha/06_og_banner.webp",
    "website": "https://radiobitcoin.org",
    "lud16": "texugorecords@walletofsatoshi.com",
    "nip05": "bitadict@radiobitcoin.org",
}

# ============ NOVA NOTE (kind 1) — catalogo atualizado ============

NOTE = """🦡 BIT ADICT — Catalogo atualizado (Maio/2026)

Tudo com 10% off pagando em Bitcoin via Lightning ⚡

📥 eBook "10 erros de quem perde Bitcoin" — GRATIS
   radiobitcoin.org/ebook.html

🛡️ Recovery Kit Digital — €20
   Ferramentas offline pra validar/recuperar seed (BIP39, multi-chain, Monero).
   radiobitcoin.org/recovery.html

📦 Recovery Kit Pen Drive fisico — €50
   USB + barra ouro coleção + manual impresso. Entrega Portugal/UE 5 dias.

💎 Pacote Completo BIT ADICT — €200 (mais pedido)
   Codigo dos 4 bots Polymarket open-source (XRP, SOL_XRP, Arbitrage, Direcional)
   + Recovery Kit + Cartao Lightning 50.000 sats + Moeda BTC + Barrinha Ouro 1kg
   + grupo WhatsApp BIT ADICT.

📡 VIP mensal — €20/mes
   Sinais dos 3 bots em tempo real no WhatsApp privado.
   radiobitcoin.org/vip.html

🎓 Curso Soberania Digital — €300 vitalicio (pre-venda)
   8 modulos, 30+ aulas. Self-custody, opsec, Lightning, Nostr, bots.
   radiobitcoin.org/curso.html

⚡ Lightning: texugorecords@walletofsatoshi.com
📱 WhatsApp: +55 61 99811-0979

Material educacional. Bot real perde tambem - sem promessa de retorno.

#Bitcoin #Bitadict #SelfCustody #Nostr #Lightning #Polymarket #RecoveryKit"""


async def publicar_evento(content, kind, label):
    event = make_event(content, kind=kind)
    tasks = [publish_to_relay(r, event) for r in RELAYS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    ok = sum(1 for r in results if r is True)
    print(f"[{label}] publicado em {ok}/{len(RELAYS)} relays · event id: {event['id'][:16]}...")
    return ok


async def main():
    print(f"=== Configurando profile Nostr {PUBKEY_HEX[:12]}... ===\n")

    # 1. metadata
    profile_json = json.dumps(PROFILE, ensure_ascii=False)
    await publicar_evento(profile_json, kind=0, label="PROFILE")

    # 2. note catalogo
    await publicar_evento(NOTE, kind=1, label="CATALOGO")

    print(f"\nPronto. Veja em njump.me/{PUBKEY_HEX}")


if __name__ == "__main__":
    asyncio.run(main())
