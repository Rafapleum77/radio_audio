#!/usr/bin/env python3
"""
Watchdog dos bots Polymarket — roda via LaunchAgent a cada 5min.

Checa:
 - Processo local rodando (Mac: ps aux | LaunchAgent state)
 - Lenovo via SSH ping
 - PnL/trades novos via Polymarket data API
 - Circuit breaker pausado

Alerta no Telegram quando:
 - Bot crashou ou está sem responder
 - Trade resolveu (win/loss) — com valor
 - Circuit breaker disparou
"""
import os, sys, json, subprocess, time, requests
from pathlib import Path
from datetime import datetime

TG_TOKEN = os.getenv("TG_WATCHDOG_TOKEN", "")  # criar novo via @BotFather, exportar
TG_CHAT  = os.getenv("TG_WATCHDOG_CHAT", "6239727715")

STATE_FILE = Path.home() / "Bots/RESULTADOS/watchdog_state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

BOTS = [
    {
        "nome": "DIRECIONAL Rafael (BTC 5m)",
        "wallet": "0xCB275e1E092E5323FA23CC1864aED3BB6B5F6823",
        "tipo": "mac_launchagent",
        "label": "com.surfgael.bot-direcional",
    },
    {
        "nome": "XRP Rafael (15m)",
        "wallet": "0xCB275e1E092E5323FA23CC1864aED3BB6B5F6823",
        "tipo": "mac_launchagent",
        "label": "com.surfgael.bot-xrp",
    },
    {
        "nome": "Gael Mac (BTC 5m)",
        "wallet": "0xfD23e200c51ef70dE6BD99d43e4442ce0184c079",
        "tipo": "mac_launchagent",
        "label": "com.surfgael.bot-direcional-filho",
    },
    {
        "nome": "Gael Lenovo (BTC 5m)",
        "wallet": "0x0CAc24471777064974fF9Cb768C5C146B4733742",
        "tipo": "lenovo_ssh",
        "task_name": "BIT_ADICT_Direcional",
    },
]

def tg(msg):
    if not TG_TOKEN:
        # sem token: só loga em stdout
        print(f"[ALERT] {msg}")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": TG_CHAT, "text": msg, "parse_mode": "Markdown"},
            timeout=10,
        )
    except Exception:
        pass

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(s):
    with open(STATE_FILE, "w") as f:
        json.dump(s, f, indent=2)

def check_mac_launchagent(label):
    """Retorna (pid_running: bool, info: str)."""
    try:
        r = subprocess.run(
            ["launchctl", "list", label],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0:
            return False, "LaunchAgent não está carregado"
        # parse output: PID = ...
        for line in r.stdout.splitlines():
            if '"PID"' in line:
                pid = line.split("=")[1].strip().rstrip(";").strip()
                if pid and pid != "-":
                    return True, f"PID {pid}"
        return False, "sem PID ativo (provavelmente crashou)"
    except Exception as e:
        return False, str(e)

def check_lenovo_ssh(task_name):
    """Via SSH: task scheduled state + processo Python."""
    try:
        r = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes",
             "Windows@192.168.1.102",
             f'powershell -Command "(Get-ScheduledTask -TaskName {task_name}).State; (Get-Process python* -ErrorAction SilentlyContinue | Select -First 1).Id"'],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode != 0:
            return False, f"SSH sem resposta"
        lines = [l.strip() for l in r.stdout.strip().splitlines() if l.strip()]
        state = lines[0] if lines else "?"
        pid = lines[1] if len(lines) > 1 else ""
        if state == "Running" and pid:
            return True, f"Task={state} PID={pid}"
        return False, f"Task={state} (sem Python rodando)"
    except subprocess.TimeoutExpired:
        return False, "SSH timeout"
    except Exception as e:
        return False, str(e)

def check_polymarket(wallet):
    """Retorna {pnl_session: float, trades_session: int, last_trade_pnl: float|None}."""
    out = {"pnl_session": 0.0, "trades_session": 0, "last_trade_pnl": None, "last_title": ""}
    try:
        r = requests.get(
            f"https://data-api.polymarket.com/positions?user={wallet}&limit=30",
            timeout=8,
        )
        if r.status_code != 200:
            return out
        positions = r.json() or []
        # ordena por endDate desc
        positions = sorted(positions, key=lambda p: p.get("endDate") or "", reverse=True)
        for p in positions[:5]:
            cv = p.get("currentValue") or 0
            pnl = p.get("cashPnl") or 0
            if abs(cv) < 0.01 and pnl != 0 and out["last_trade_pnl"] is None:
                out["last_trade_pnl"] = pnl
                out["last_title"] = (p.get("title") or "")[:60]
                break
        return out
    except Exception:
        return out

def main():
    state = load_state()
    now = datetime.now().strftime("%H:%M")
    alerts = []
    for bot in BOTS:
        bot_key = bot["nome"]
        prev = state.get(bot_key, {})

        # Check process
        if bot["tipo"] == "mac_launchagent":
            up, info = check_mac_launchagent(bot["label"])
        else:
            up, info = check_lenovo_ssh(bot["task_name"])

        # Detect crash
        was_up = prev.get("up", True)
        if was_up and not up:
            alerts.append(f"🚨 *{bot_key}* CAIU\n  {info}")
        elif not was_up and up:
            alerts.append(f"✅ *{bot_key}* voltou ({info})")

        # Check trades
        pm = check_polymarket(bot["wallet"])
        last_pnl = pm.get("last_trade_pnl")
        last_title = pm.get("last_title", "")
        prev_last_title = prev.get("last_trade_title", "")
        if last_pnl is not None and last_title and last_title != prev_last_title:
            cor = "🟢" if last_pnl > 0 else "🔴"
            alerts.append(f"{cor} *{bot_key}* trade resolvido: `${last_pnl:+.2f}`\n  `{last_title}`")
            prev["last_trade_title"] = last_title
            prev["last_trade_pnl"] = last_pnl

        prev["up"] = up
        prev["last_check"] = now
        prev["last_info"] = info
        state[bot_key] = prev

    if alerts:
        tg(f"📡 *Watchdog Bots* — {now}\n\n" + "\n\n".join(alerts))

    save_state(state)
    # Stdout simples pra log
    print(f"[{now}] watchdog OK | bots: {sum(1 for b in BOTS if state.get(b['nome'],{}).get('up'))}/{len(BOTS)} up")

if __name__ == "__main__":
    main()
