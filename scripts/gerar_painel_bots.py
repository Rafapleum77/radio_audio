#!/usr/bin/env python3.11
"""
Gera /Users/rafaelrioscrosara/Bots/radio/bots_status.json a cada execução.
Lê logs dos 2 bots ativos:
- DIRECIONAL (Rafael, XRP) em /tmp/direcional_live.log
- DIRECIONAL_FILHO (Gael, BTC) em ~/Bots/DIRECIONAL_FILHO/logs/stdout.log

Cron sugerido: 1x/min via launchd.
"""
import json, re, time, subprocess
from pathlib import Path
from datetime import datetime

OUT = Path.home() / "Bots/radio/bots_status.json"
LOG_RAFAEL = Path("/tmp/direcional_live.log")
LOG_GAEL   = Path.home() / "Bots/DIRECIONAL_FILHO/logs/stdout.log"

# Regex pra capturar última linha de status de cada bot:
# Formato: "HH:MM:SS │ BTC:$X │ RSI:Y │ EMA:▲ │ Dir:▲ UP NN% │ T-NNNs │ P&L:+X.XX │ Win:X.X%"
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

# Regex pra trades concluídos no log
RE_TRADE = re.compile(
    r"\[OK\]\s+(?P<dir>UP|DOWN):.*?@\s*(?P<preco>[\d.]+).*?\(\$(?P<valor>[\d.]+)\)"
)
RE_RESULT_WIN = re.compile(r"✓.*?(?:WIN|venceu|ganhou)\b", re.I)
RE_RESULT_LOSS = re.compile(r"✗.*?(?:LOSS|perdeu)\b", re.I)


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
            data = f.read()
        return strip_ansi(data.decode("utf-8", errors="replace"))
    except Exception:
        return ""


def coletar_bot_full(log_path, nome, moeda, folder):
    pid = pid_ativo(folder)
    log = read_tail(log_path)
    if not log:
        return {
            "nome": nome,
            "moeda": moeda,
            "ativo": pid is not None,
            "pid": pid,
            "status": None,
            "trades_log": [],
            "mtime": None,
        }

    pedacos = re.split(r"[\r\n]+", log)
    status = None
    for p in reversed(pedacos):
        m = RE.search(p)
        if m:
            d = m.groupdict()
            d["preco"] = d["preco"].replace(",", "")
            status = d
            break

    # Conta trades + win/loss
    wins = 0
    losses = 0
    trades = []
    last_open = None
    for p in pedacos:
        m = RE_TRADE.search(p)
        if m:
            last_open = m.groupdict()
            trades.append({"dir": m.group("dir"), "preco": m.group("preco"), "valor": m.group("valor")})
        if last_open:
            if RE_RESULT_WIN.search(p):
                wins += 1
                last_open = None
            elif RE_RESULT_LOSS.search(p):
                losses += 1
                last_open = None

    mtime = log_path.stat().st_mtime if log_path.exists() else None

    return {
        "nome": nome,
        "moeda": moeda,
        "ativo": pid is not None,
        "pid": pid,
        "status": status,
        "wins": wins,
        "losses": losses,
        "trades_total": wins + losses,
        "win_rate": round(wins / max(wins + losses, 1) * 100, 1),
        "trades_recentes": trades[-5:],
        "mtime": mtime,
        "mtime_pretty": datetime.fromtimestamp(mtime).strftime("%H:%M:%S") if mtime else None,
    }


def pid_ativo(folder_match):
    """Detecta PID do bot rodando em determinada pasta."""
    try:
        out = subprocess.check_output(["pgrep", "-f", "bot_direcional_v2.py"], text=True).strip()
        for pid in out.split():
            try:
                cwd_out = subprocess.check_output(["lsof", "-p", pid, "-d", "cwd", "-F", "n"], text=True, stderr=subprocess.DEVNULL)
                for line in cwd_out.splitlines():
                    if line.startswith("n") and folder_match in line:
                        return int(pid)
            except Exception:
                continue
    except Exception:
        pass
    return None


def main():
    data = {
        "atualizado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "atualizado_ts": int(time.time()),
        "bots": {
            "direcional_rafael": coletar_bot_full(LOG_RAFAEL, "DIRECIONAL", "XRP", "DIRECIONAL"),
            "direcional_gael":   coletar_bot_full(LOG_GAEL,   "BOT DO PAPAI", "BTC", "DIRECIONAL_FILHO"),
        },
    }
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"[{data['atualizado_em']}] {OUT} atualizado")
    print(f"  Rafael: ativo={data['bots']['direcional_rafael']['ativo']} status={'OK' if data['bots']['direcional_rafael']['status'] else 'sem leitura'}")
    print(f"  Gael:   ativo={data['bots']['direcional_gael']['ativo']} status={'OK' if data['bots']['direcional_gael']['status'] else 'sem leitura'}")


if __name__ == "__main__":
    main()
