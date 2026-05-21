#!/usr/bin/env python3.11
"""
Gera /Users/rafaelrioscrosara/Bots/radio/bots_status.json a cada execução.

Combina:
- public_snapshot() do painel_radio.py (XRP, ARBITRAGE, DIRECIONAL, redes, locutores, radio, maquinas)
- Bot do Petlendas BSB (Mac Mini DIRECIONAL_FILHO via log local)
- Bot Aniversario Gael (Lenovo via API Polymarket)

Cron 1x/min via launchd. Auto-commit pro repo radio.
"""
from __future__ import annotations
import json, re, sys, time, subprocess, requests
from pathlib import Path
from datetime import datetime

# Importa painel_radio.py pra reusar coletores
sys.path.insert(0, str(Path.home() / "Bots"))
try:
    import painel_radio as pr
    SNAPSHOT_OK = True
except Exception as e:
    print(f"WARN: nao consegui importar painel_radio: {e}")
    SNAPSHOT_OK = False

OUT = Path.home() / "Bots/radio/bots_status.json"
LOG_GAEL = Path.home() / "Bots/DIRECIONAL_FILHO/logs/stdout.log"

RE = re.compile(
    r"(?P<hora>\d{2}:\d{2}:\d{2}).*?"
    r"(?:BTC|XRP):\$(?P<preco>[\d,.]+).*?"
    r"RSI:(?P<rsi>[\d.]+).*?"
    r"EMA:(?P<ema>[▲▼]).*?"
    r"Dir:[▲▼].\s*(?P<dir>UP|DOWN)\s*(?P<conf>\d+)%.*?"
    r"T-(?P<t>\d+)s.*?"
    r"P&L:(?P<pnl>[-+\d.]+).*?"
    r"Win:(?P<win>[\d.]+)%"
)
RE_TRADE = re.compile(r"\[OK\]\s+(?P<dir>UP|DOWN):.*?@\s*(?P<preco>[\d.]+).*?\(\$(?P<valor>[\d.]+)\)")


def strip_ansi(s):
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def read_tail(path, max_bytes=16384):
    if not path.exists():
        return ""
    try:
        size = path.stat().st_size
        with path.open("rb") as f:
            if size > max_bytes:
                f.seek(-max_bytes, 2)
            return strip_ansi(f.read().decode("utf-8", errors="replace"))
    except Exception:
        return ""


def coletar_petlendas_mac():
    """Bot DIRECIONAL_FILHO rodando no Mac Mini (conta petlendasbsb@gmail.com)."""
    pid = None
    try:
        out = subprocess.check_output(["pgrep", "-f", "DIRECIONAL_FILHO.*bot_direcional"], text=True).strip()
        if out:
            pid = int(out.split()[0])
    except Exception:
        pass

    log = read_tail(LOG_GAEL)
    pedacos = re.split(r"[\r\n]+", log)
    status = None
    for p in reversed(pedacos):
        m = RE.search(p)
        if m:
            d = m.groupdict()
            d["preco"] = d["preco"].replace(",", "")
            status = d
            break

    wins = losses = 0
    trades = []
    last_open = None
    for p in pedacos:
        m = RE_TRADE.search(p)
        if m:
            last_open = m.groupdict()
            trades.append({"dir": m.group("dir"), "preco": m.group("preco"), "valor": m.group("valor")})
        if last_open:
            if re.search(r"✓.*?(?:WIN|venceu|ganhou)", p, re.I):
                wins += 1; last_open = None
            elif re.search(r"✗.*?(?:LOSS|perdeu)", p, re.I):
                losses += 1; last_open = None

    return {
        "nome": "PETLENDAS BSB",
        "moeda": "BTC",
        "janela": "5min",
        "local": "Mac Mini",
        "ativo": pid is not None,
        "pid": pid,
        "status": status,
        "wins": wins,
        "losses": losses,
        "trades_total": wins + losses,
        "win_rate": round(wins / max(wins + losses, 1) * 100, 1),
        "trades_recentes": trades[-5:],
    }


def coletar_via_api_polymarket(funder, nome, moeda, local):
    """Bot remoto - puxa via API Polymarket."""
    try:
        r = requests.get(f"https://data-api.polymarket.com/positions?user={funder}&limit=30", timeout=8)
        positions = r.json() if r.status_code == 200 else []
    except Exception:
        positions = []

    pnl_total = sum(p.get("cashPnl", 0) for p in positions)
    wins = sum(1 for p in positions if p.get("cashPnl", 0) > 0)
    losses = sum(1 for p in positions if p.get("cashPnl", 0) < 0)
    abertas = sum(1 for p in positions if p.get("currentValue", 0) > 0.01 and not p.get("redeemable"))

    trades = [{
        "dir": p.get("outcome", "?").upper(),
        "preco": str(round(p.get("avgPrice", 0) * 100, 1)),
        "valor": f"{p.get('initialValue', 0):.2f}",
    } for p in positions[:5]]

    return {
        "nome": nome,
        "moeda": moeda,
        "janela": "5min",
        "local": local,
        "ativo": len(positions) > 0,
        "via": "polymarket_api",
        "status": None,
        "wins": wins,
        "losses": losses,
        "trades_total": wins + losses,
        "win_rate": round(wins / max(wins + losses, 1) * 100, 1),
        "trades_recentes": trades,
        "pnl_total": round(pnl_total, 2),
        "posicoes_abertas": abertas,
        "funder": funder,
        "profile_url": f"https://polymarket.com/profile/{funder}",
    }


def main():
    data = {
        "atualizado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "atualizado_ts": int(time.time()),
        "polymarket_bots": {
            "petlendas_bsb":   coletar_petlendas_mac(),
            "bot_aniversario": coletar_via_api_polymarket(
                "0x0CAc24471777064974fF9Cb768C5C146B4733742",
                "BOT ANIVERSÁRIO DO GAEL",
                "BTC",
                "Lenovo PC novo"
            ),
        },
    }

    # Adiciona snapshot do painel local (XRP, ARBITRAGE, DIRECIONAL, redes, locutores, sistema)
    if SNAPSHOT_OK:
        try:
            snap = pr.public_snapshot()
            data["radio_panel"] = snap
        except Exception as e:
            print(f"WARN: snapshot painel_radio falhou: {e}")

    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"[{data['atualizado_em']}] {OUT}")
    p = data['polymarket_bots']
    print(f"  Petlendas (Mac): ativo={p['petlendas_bsb']['ativo']}")
    print(f"  Aniversario (Lenovo): trades={p['bot_aniversario']['trades_total']} pnl=${p['bot_aniversario']['pnl_total']}")
    if SNAPSHOT_OK and "radio_panel" in data:
        rp = data["radio_panel"]
        bots_panel = rp.get("bots", [])
        print(f"  Painel radio: {len(bots_panel)} bots + {len(rp.get('maquinas', []))} maquinas")


if __name__ == "__main__":
    main()
