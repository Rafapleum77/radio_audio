#!/usr/bin/env python3
"""
RÁDIO BITCOIN — Nostr Broadcaster
Posta automaticamente no Nostr a cada troca de música + preço BTC + link da rádio
"""
import json, time, hashlib, hmac, struct, asyncio, os, sys, requests
from datetime import datetime
from pathlib import Path

# ── CONFIGURAÇÃO ──────────────────────────────────────────────────
# Chaves Nostr lidas via dotenv (~/Bots/XRP/.env, symlinked aqui como .env).
# .env esta em .gitignore — NUNCA hardcoded aqui.
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # fallback: espera env vars ja exportadas pelo ambiente
PRIVKEY_HEX = os.environ.get("NOSTR_PRIVKEY") or sys.exit("ERRO: NOSTR_PRIVKEY nao definida no .env")
PUBKEY_HEX  = os.environ.get("NOSTR_PUBKEY")  or sys.exit("ERRO: NOSTR_PUBKEY nao definida no .env")
RADIO_URL    = "https://radiobitcoin.bitadict.com"
LIGHTNING    = "texugorecords@walletofsatoshi.com"
TRACKS_JSON  = os.path.join(os.path.dirname(__file__), "tracks.json")
ESTADO_JSON  = os.path.expanduser("~/Bots/RESULTADOS/estado_global.json")
STATE_FILE   = "/tmp/nostr_last_track.txt"

RELAYS = [
    "wss://nos.lol",
    "wss://relay.damus.io",
    "wss://nostr.wine",
    "wss://relay.nostr.band",
]

HASHTAGS = "#Bitcoin #RadioBitcoin #Nostr #Lightning #BTC #Bitadict #StackingSats"

# ── NOSTR UTILS ───────────────────────────────────────────────────
def _schnorr_sign(msg_bytes, privkey_hex):
    """Schnorr signature (BIP340) using hmac-based aux rand"""
    import secp256k1
    privkey = secp256k1.PrivateKey(bytes.fromhex(privkey_hex))
    sig = privkey.schnorr_sign(msg_bytes, None, raw=True)
    return sig.hex()

def make_event(content, kind=1, tags=None):
    tags = tags or []
    created_at = int(time.time())
    event_data = [0, PUBKEY_HEX, created_at, kind, tags, content]
    serialized = json.dumps(event_data, separators=(',',':'), ensure_ascii=False)
    event_id = hashlib.sha256(serialized.encode()).hexdigest()
    sig = _schnorr_sign(bytes.fromhex(event_id), PRIVKEY_HEX)
    return {"id": event_id, "pubkey": PUBKEY_HEX, "created_at": created_at,
            "kind": kind, "tags": tags, "content": content, "sig": sig}

async def publish_to_relay(relay_url, event):
    try:
        import websockets
        async with websockets.connect(relay_url, open_timeout=8, close_timeout=5) as ws:
            await ws.send(json.dumps(["EVENT", event]))
            resp = await asyncio.wait_for(ws.recv(), timeout=6)
            data = json.loads(resp)
            if data[0] == "OK" and data[2]:
                return True
    except Exception as e:
        pass
    return False

async def broadcast(content):
    event = make_event(content)
    tasks = [publish_to_relay(r, event) for r in RELAYS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    ok = sum(1 for r in results if r is True)
    print(f"[nostr] publicado em {ok}/{len(RELAYS)} relays")
    return ok

# ── DADOS ─────────────────────────────────────────────────────────
def get_btc_price():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5)
        return float(r.json()["price"])
    except:
        return None

def get_xrp_data():
    try:
        with open(ESTADO_JSON) as f:
            d = json.load(f)
        xrp = d.get("bots",{}).get("XRP",{})
        return xrp.get("preco"), xrp.get("rsi"), xrp.get("ema")
    except:
        return None, None, None

def get_tracks():
    try:
        with open(TRACKS_JSON) as f:
            return json.load(f)
    except:
        return []

def get_last_track():
    try:
        with open(STATE_FILE) as f:
            return f.read().strip()
    except:
        return ""

def save_last_track(title):
    with open(STATE_FILE, "w") as f:
        f.write(title)

def pick_next_track(tracks, last_title):
    """Rotação sequencial das faixas"""
    if not tracks:
        return None
    titles = [t["title"] for t in tracks]
    try:
        idx = titles.index(last_title)
        return tracks[(idx + 1) % len(tracks)]
    except:
        return tracks[0]

# ── TEMPLATES DE POST ─────────────────────────────────────────────
def post_track_change(track, btc_price, xrp_price, rsi, ema):
    cat = track.get("category","")
    emoji = "🤖" if "IA" in cat else "🎸"
    dur = track.get("dur","")

    btc_str = f"₿ ${btc_price:,.0f}" if btc_price else ""
    xrp_str = f"⚡ XRP ${xrp_price:.4f}" if xrp_price else ""
    rsi_str = f"RSI {rsi:.0f}" if rsi else ""
    ema_str = f"EMA {ema}" if ema else ""

    bot_line = ""
    if xrp_str:
        bot_line = f"\n📊 Bot ao vivo: {xrp_str} | {rsi_str} | {ema_str}"

    msg = f"""{emoji} TOCANDO AGORA na Rádio Bitcoin:

🎵 {track['title']}
⏱ {dur} · {cat}

{btc_str}{bot_line}

🔊 Ouça grátis:
{RADIO_URL}

⚡ Support: {LIGHTNING}

{HASHTAGS}"""
    return msg

def post_hourly_update(btc_price, xrp_price, rsi, ema, total_tracks):
    btc_str = f"${btc_price:,.0f}" if btc_price else "N/A"
    xrp_str = f"${xrp_price:.4f}" if xrp_price else "N/A"
    hora = datetime.now().strftime("%H:%M")

    msg = f"""📻 RÁDIO BITCOIN — Update {hora}

₿ Bitcoin: {btc_str}
⚡ XRP: {xrp_str} | RSI {rsi:.0f if rsi else 'N/A'} | EMA {ema or 'N/A'}

🎵 {total_tracks} músicas na playlist
🤖 {sum(1 for _ in range(total_tracks) if True)} tracks IA + Rock anos 80

🔊 {RADIO_URL}
⚡ Gorjeta: {LIGHTNING}

{HASHTAGS}"""
    return msg

# ── LOOP PRINCIPAL ────────────────────────────────────────────────
async def main():
    print("[nostr_broadcaster] iniciado")
    tracks = get_tracks()
    last_post_hour = -1
    post_interval = 1800  # posta a cada 30 min por troca de música
    last_post_time = 0

    while True:
        now = time.time()
        tracks = get_tracks()  # recarrega se atualizado
        btc = get_btc_price()
        xrp_price, rsi, ema = get_xrp_data()
        current_hour = datetime.now().hour

        # Post horário fixo (8h, 12h, 18h, 21h)
        if current_hour in (8, 12, 18, 21) and current_hour != last_post_hour:
            content = post_hourly_update(btc, xrp_price, rsi, ema, len(tracks))
            await broadcast(content)
            last_post_hour = current_hour
            last_post_time = now

        # Post de troca de música (a cada 30min no máximo)
        elif now - last_post_time > post_interval:
            last = get_last_track()
            track = pick_next_track(tracks, last)
            if track:
                save_last_track(track["title"])
                content = post_track_change(track, btc, xrp_price, rsi, ema)
                await broadcast(content)
                last_post_time = now

        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
