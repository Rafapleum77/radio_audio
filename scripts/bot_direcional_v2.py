# -*- coding: utf-8 -*-
"""
BIT ADICT — BOT DIRECIONAL v1.0
Estratégia: aposta 1 lado (UP ou DOWN) baseado em análise técnica do BTC
- RSI + EMA + Momentum + Bollinger para decidir direção
- $2 por trade, sem stop em perdas seguidas
- Stop-loss global $20
"""

import os
import sys
import time
import threading
import requests
import logging
import pandas as pd
import numpy as np
import ccxt
from web3 import Web3
from dotenv import load_dotenv
# Polymarket migrou pra CLOB V2 em 28/04/2026 — lib V1 nao funciona mais
from py_clob_client_v2.client import ClobClient
from py_clob_client_v2 import OrderArgsV2, OrderType, Side, SignatureTypeV2
BUY = Side.BUY

try:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

load_dotenv()
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

# ═══════════════════════════════════════════════════════════════
#  PAPER MODE (DRY_RUN=true não envia ordens reais, só loga)
# ═══════════════════════════════════════════════════════════════
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
SKIP_BALANCE_CHECK = os.getenv("SKIP_BALANCE_CHECK", "false").lower() == "true"
PAPER_LOG = os.path.expanduser("~/Bots/RESULTADOS/paper_direcional.log")

# ═══════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════

HOST     = "https://clob.polymarket.com"
POLY_RPC = os.getenv("POLY_RPC", "https://polygon-bor-rpc.publicnode.com")
KEY      = os.getenv("POLY_KEY")
FUNDER   = os.getenv("POLY_FUNDER")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT  = os.getenv("TELEGRAM_CHAT_ID")

USDC_ADDRESS = Web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")
CTF_EXCHANGE = Web3.to_checksum_address("0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E")

ERC20_ABI = [
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf",
     "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}],
     "name": "allowance", "outputs": [{"name": "", "type": "uint256"}],
     "stateMutability": "view", "type": "function"},
]

VALOR_TRADE   = float(os.getenv("VALOR_TRADE",  "2.0"))   # $ por operação
STOP_LOSS     = float(os.getenv("STOP_LOSS",    "20.0"))  # $ perda máxima global
CONFIANCA_MIN = int(os.getenv("CONFIANCA_MIN",  "65"))    # score mínimo (subiu de 60→65)
PRECO_MIN     = float(os.getenv("PRECO_MIN",    "0.55"))  # 0.55 = só compra quando indicador concorda com favorito do mercado (edge real). 0.45 (antigo) apostava sistematicamente no underdog → 0% win rate
PRECO_MAX     = float(os.getenv("PRECO_MAX",    "0.80"))  # evita trades caros demais (ex: 0.97 → ganho potencial ~$0.02)
INTERVALO     = 20       # segundos entre ciclos
SLUG_BASE     = "btc-updown-5m"
DURACAO_SLOT  = 300
TEMPO_MIN     = 60       # segundos mínimos antes do slot expirar

V, A, R, C, X = "\033[92m", "\033[93m", "\033[91m", "\033[96m", "\033[0m"
B = "\033[1m"; DIM = "\033[2m"; MAG = "\033[95m"; WHT = "\033[97m"

# ═══════════════════════════════════════════════════════════════
#  ESTADO
# ═══════════════════════════════════════════════════════════════

estado = {
    "pnl":            0.0,
    "trades":         0,
    "ganhos":         0,
    "inicio":         time.time(),
    "slot_executado": None,
    "pausado":        False,
    "encerrar":       False,
    "ultima_direcao": None,
    "maior_pnl":      0.0,
}

cache = {"slot": None, "t_up": None, "t_down": None, "titulo": None, "valido": False}
_ultimo_update_id = 0
exchange = ccxt.binance({"timeout": 10000, "enableRateLimit": True})
_w3 = None

# ═══════════════════════════════════════════════════════════════
#  WEB3
# ═══════════════════════════════════════════════════════════════

def get_w3():
    global _w3
    if _w3 is None or not _w3.is_connected():
        _w3 = Web3(Web3.HTTPProvider(POLY_RPC, request_kwargs={"timeout": 10}))
    return _w3

def obter_saldo_usdc(wallet):
    try:
        w3 = get_w3()
        usdc = w3.eth.contract(address=USDC_ADDRESS, abi=ERC20_ABI)
        return round(usdc.functions.balanceOf(Web3.to_checksum_address(wallet)).call() / 1e6, 4)
    except:
        return 0.0

def obter_allowance_usdc(wallet):
    try:
        w3 = get_w3()
        usdc = w3.eth.contract(address=USDC_ADDRESS, abi=ERC20_ABI)
        return round(usdc.functions.allowance(Web3.to_checksum_address(wallet), CTF_EXCHANGE).call() / 1e6, 4)
    except:
        return 0.0

# ═══════════════════════════════════════════════════════════════
#  PNL TRACKER REAL (via Polymarket data API)
# ═══════════════════════════════════════════════════════════════

_pnl_baseline_conds = set()  # conditionIds existentes no startup (não contam)
_pnl_session_conds  = set()  # conditionIds novos já contabilizados na sessão
_pnl_last_check     = 0.0

def init_pnl_tracker(wallet):
    """Marca posições atuais como baseline — só conta novas trades da sessão."""
    if not wallet:
        return
    try:
        r = requests.get(f"https://data-api.polymarket.com/positions?user={wallet}&limit=100", timeout=8)
        if r.status_code != 200:
            return
        for p in (r.json() or []):
            cid = p.get("conditionId") or ""
            if cid:
                _pnl_baseline_conds.add(cid)
        print(f"{V}[PNL] Baseline: {len(_pnl_baseline_conds)} posições históricas ignoradas{X}")
    except Exception as e:
        print(f"{A}[PNL] Baseline falhou: {e}{X}")

def atualizar_pnl_real(wallet):
    """Polla posições resolvidas; atualiza estado['pnl'] e estado['ganhos']."""
    global _pnl_last_check
    agora = time.time()
    if agora - _pnl_last_check < 30:  # cache 30s
        return
    _pnl_last_check = agora
    if not wallet:
        return
    try:
        r = requests.get(f"https://data-api.polymarket.com/positions?user={wallet}&limit=50", timeout=8)
        if r.status_code != 200:
            return
        novos_resolved = 0
        for p in (r.json() or []):
            cid = p.get("conditionId") or ""
            if not cid or cid in _pnl_baseline_conds or cid in _pnl_session_conds:
                continue
            cash_pnl = p.get("cashPnl") or 0
            current_value = p.get("currentValue") or 0
            # resolvido = currentValue ~0 (mercado fechou) e cashPnl != 0
            if abs(current_value) < 0.01 and cash_pnl != 0:
                _pnl_session_conds.add(cid)
                estado["pnl"] += cash_pnl
                if cash_pnl > 0:
                    estado["ganhos"] += 1
                novos_resolved += 1
                cor = V if cash_pnl > 0 else R
                print(f"\n{cor}[PNL] Trade resolvido: {cash_pnl:+.2f} | PnL sessão: {estado['pnl']:+.2f} | Win rate: {_taxa()}{X}")
                cb_register_trade_result(cash_pnl)
        if novos_resolved > 0 and abs(estado["pnl"]) > 0:
            estado["maior_pnl"] = max(estado["maior_pnl"], estado["pnl"])
    except Exception:
        pass  # silencioso — não quebra o bot por API hiccup

# ═══════════════════════════════════════════════════════════════
#  CIRCUIT BREAKER (sobrevivência > otimização)
# ═══════════════════════════════════════════════════════════════
#  3 losses seguidos → pausa 4h
#  5 losses seguidos → pausa 24h
#  PnL do dia <= -3% do bankroll → pausa até fim do dia
# ═══════════════════════════════════════════════════════════════

import json
from datetime import datetime as _dt

BANKROLL_USD = float(os.getenv("BANKROLL_USD", "100.0"))  # tamanho banca pra calcular % daily loss
DAILY_LOSS_PCT = float(os.getenv("DAILY_LOSS_PCT", "0.03"))  # 3% = pausa restante do dia
LOSS_STREAK_PAUSE = int(os.getenv("LOSS_STREAK_PAUSE", "3"))
LOSS_STREAK_HARD = int(os.getenv("LOSS_STREAK_HARD", "5"))
PAUSE_4H = 4 * 3600
PAUSE_24H = 24 * 3600

_CB_DIR = os.path.expanduser("~/Bots/RESULTADOS")
os.makedirs(_CB_DIR, exist_ok=True)
_CB_FILE = os.path.join(_CB_DIR, f"cb_{(FUNDER or 'default')[2:10].lower()}.json")

def cb_load():
    try:
        with open(_CB_FILE) as f:
            d = json.load(f)
            # reset diário automático
            if d.get("daily_date") != _dt.now().strftime("%Y-%m-%d"):
                d["daily_pnl"] = 0.0
                d["daily_date"] = _dt.now().strftime("%Y-%m-%d")
                cb_save(d)
            return d
    except Exception:
        return {
            "pause_until": 0,
            "loss_streak": 0,
            "daily_pnl": 0.0,
            "daily_date": _dt.now().strftime("%Y-%m-%d"),
            "pause_reason": "",
        }

def cb_save(d):
    try:
        with open(_CB_FILE, "w") as f:
            json.dump(d, f, indent=2)
    except Exception:
        pass

def cb_is_paused():
    """Retorna (paused: bool, reason: str). Mostra log de status uma vez ao detectar pausa."""
    d = cb_load()
    agora = time.time()
    if d.get("pause_until", 0) > agora:
        restantes = int((d["pause_until"] - agora) / 60)
        return True, f"{d.get('pause_reason','?')} (faltam {restantes}min)"
    return False, ""

def cb_register_trade_result(cash_pnl):
    """Atualiza streak + daily_pnl. Aciona pausa se threshold atingido."""
    d = cb_load()
    d["daily_pnl"] = d.get("daily_pnl", 0.0) + cash_pnl

    if cash_pnl < 0:
        d["loss_streak"] = d.get("loss_streak", 0) + 1
    else:
        d["loss_streak"] = 0  # reset em qualquer win

    agora = time.time()
    pause_set = None

    # Hard: 5 losses → 24h
    if d["loss_streak"] >= LOSS_STREAK_HARD:
        pause_set = (agora + PAUSE_24H, f"5 losses seguidos → pausa 24h")
    # Soft: 3 losses → 4h
    elif d["loss_streak"] >= LOSS_STREAK_PAUSE:
        pause_set = (agora + PAUSE_4H, f"3 losses seguidos → pausa 4h")

    # Daily loss limit: -3% do bankroll
    daily_limit = -abs(BANKROLL_USD * DAILY_LOSS_PCT)
    if d["daily_pnl"] <= daily_limit:
        # pausa até meia-noite local
        meia_noite = _dt.now().replace(hour=23, minute=59, second=59).timestamp()
        if pause_set is None or meia_noite > pause_set[0]:
            pause_set = (meia_noite, f"daily loss ${daily_limit:.0f} atingido → pausa restante do dia")

    if pause_set:
        d["pause_until"] = pause_set[0]
        d["pause_reason"] = pause_set[1]
        msg = f"🛑 CIRCUIT BREAKER: {pause_set[1]} | PnL dia: ${d['daily_pnl']:+.2f} | Streak: {d['loss_streak']}"
        print(f"\n{R}{msg}{X}")
        enviar_telegram(msg)
    cb_save(d)

# ═══════════════════════════════════════════════════════════════
#  TELEGRAM
# ═══════════════════════════════════════════════════════════════

def enviar_telegram(msg):
    if not TG_TOKEN or not TG_CHAT:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": TG_CHAT, "text": msg, "parse_mode": "Markdown"},
            timeout=10,
        )
    except:
        pass

def _uptime():
    s = int(time.time() - estado["inicio"])
    h, m = divmod(s // 60, 60)
    return f"{h:02d}h{m:02d}m"

def _taxa():
    if estado["trades"] == 0: return "0%"
    return f"{estado['ganhos']/estado['trades']*100:.1f}%"

def processar_comando(texto):
    cmd = texto.strip().lower().split()[0]
    if cmd == "/status":
        saldo = obter_saldo_usdc(FUNDER) if FUNDER else 0
        enviar_telegram(
            f"📊 *DIRECIONAL v1.0 — Status*\n"
            f"Estado: `{'⏸ PAUSADO' if estado['pausado'] else '▶️ ATIVO'}`\n"
            f"💵 Saldo: `${saldo:.2f}`\n"
            f"📉 P&L: `${estado['pnl']:+.2f}`\n"
            f"📈 Trades: `{estado['trades']}` | Win: `{_taxa()}`\n"
            f"🎯 Última direção: `{estado['ultima_direcao'] or 'nenhuma'}`\n"
            f"⏱️ Uptime: `{_uptime()}`"
        )
    elif cmd == "/pausar":
        estado["pausado"] = True
        enviar_telegram("⏸ *Bot PAUSADO*")
    elif cmd == "/retomar":
        estado["pausado"] = False
        enviar_telegram("▶️ *Bot RETOMADO*")
    elif cmd == "/stop":
        estado["encerrar"] = True
        enviar_telegram("🛑 *Encerrando...*")
    elif cmd == "/ajuda":
        enviar_telegram("/status /pausar /retomar /stop /ajuda")

def _polling_telegram():
    global _ultimo_update_id
    if not TG_TOKEN: return
    while not estado.get("encerrar"):
        try:
            resp = requests.get(
                f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates",
                params={"offset": _ultimo_update_id + 1, "timeout": 3},
                timeout=10,
            ).json()
            if resp.get("ok") and resp.get("result"):
                for u in resp["result"]:
                    _ultimo_update_id = u["update_id"]
                    msg = u.get("message") or u.get("edited_message")
                    if not msg: continue
                    texto = msg.get("text", "")
                    chat = str(msg.get("chat", {}).get("id", ""))
                    if chat == str(TG_CHAT) and texto.startswith("/"):
                        processar_comando(texto)
        except:
            pass
        time.sleep(3)

# ═══════════════════════════════════════════════════════════════
#  ANÁLISE TÉCNICA — DECIDE DIREÇÃO
# ═══════════════════════════════════════════════════════════════

_cache_tec = {"ts": 0, "dados": None}
_window_opens = {}  # {slot_ts: btc_open_price} — pra calcular Window Delta (sinal dominante)

def _window_delta_pct(preco_atual):
    """Variação % do BTC desde a abertura da janela 5min atual.
    Sinal DOMINANTE pra mercados de curta duração (peso 5-7 vs 1-2 dos clássicos)."""
    slot = slot_atual_ts()
    if slot not in _window_opens:
        _window_opens[slot] = preco_atual  # registra primeira observação
        # limpa entradas antigas (>3 slots)
        for old_slot in list(_window_opens.keys()):
            if old_slot < slot - 3 * DURACAO_SLOT:
                _window_opens.pop(old_slot, None)
        return 0.0
    open_price = _window_opens[slot]
    if open_price <= 0:
        return 0.0
    return (preco_atual - open_price) / open_price * 100

def obter_dados_tecnicos():
    """
    v2.0 — @wehighallday upgrades:
    - Bollinger em 15m (evita fakeouts do 1m)
    - Donchian 7 dias para confirmar breakout real
    - Volume spike detector
    - Garbage collection explícito para evitar memory leak
    """
    import gc
    agora = time.time()
    if agora - _cache_tec["ts"] < 60:
        return _cache_tec["dados"]
    try:
        # ── 1m para RSI/EMA/Momentum ─────────────────────────
        bars_1m = exchange.fetch_ohlcv("BTC/USDT", timeframe="1m", limit=60)
        df1 = pd.DataFrame(bars_1m, columns=["ts", "open", "high", "low", "close", "vol"])

        # RSI 14
        delta = df1["close"].diff()
        gain  = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss  = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
        rs    = gain / loss.replace(0, np.nan)
        rsi   = float((100 - (100 / (1 + rs))).iloc[-1])

        # EMA 9 e 21
        ema9  = float(df1["close"].ewm(span=9).mean().iloc[-1])
        ema21 = float(df1["close"].ewm(span=21).mean().iloc[-1])

        # Momentum 10 períodos
        mom = float(df1["close"].iloc[-1] - df1["close"].iloc[-11])

        # Variação 1m e 3m
        preco_atual = float(df1["close"].iloc[-1])
        var1m = float((df1["close"].iloc[-1] - df1["close"].iloc[-2]) / df1["close"].iloc[-2] * 100)
        var3m = float((df1["close"].iloc[-1] - df1["close"].iloc[-4]) / df1["close"].iloc[-4] * 100)

        # GC do df1m
        del bars_1m, delta, gain, loss, rs
        df1 = None
        gc.collect()

        # ── 15m para Bollinger (anti-fakeout) ────────────────
        bars_15m = exchange.fetch_ohlcv("BTC/USDT", timeframe="15m", limit=40)
        df15 = pd.DataFrame(bars_15m, columns=["ts", "open", "high", "low", "close", "vol"])

        sma20_15 = df15["close"].rolling(20).mean()
        std20_15 = df15["close"].rolling(20).std()
        bb_upper_15 = float((sma20_15 + std20_15 * 2).iloc[-1])
        bb_lower_15 = float((sma20_15 - std20_15 * 2).iloc[-1])
        bb_pos_15 = (preco_atual - bb_lower_15) / (bb_upper_15 - bb_lower_15) if (bb_upper_15 - bb_lower_15) > 0 else 0.5

        # Breakout acima da BB superior 15m?
        bb_breakout_up   = preco_atual > bb_upper_15
        bb_breakout_down = preco_atual < bb_lower_15

        # Volume spike 15m (volume atual vs média 20 períodos)
        vol_media_15 = float(df15["vol"].rolling(20).mean().iloc[-1])
        vol_atual_15 = float(df15["vol"].iloc[-1])
        vol_spike    = vol_atual_15 / vol_media_15 if vol_media_15 > 0 else 1.0

        del bars_15m, sma20_15, std20_15
        df15 = None
        gc.collect()

        # ── 1h para Donchian 7 dias (42 períodos × 1h = ~7d) ─
        bars_1h = exchange.fetch_ohlcv("BTC/USDT", timeframe="1h", limit=170)
        df1h = pd.DataFrame(bars_1h, columns=["ts", "open", "high", "low", "close", "vol"])

        don_high = float(df1h["high"].rolling(168).max().iloc[-1])   # 7 dias
        don_low  = float(df1h["low"].rolling(168).min().iloc[-1])
        don_pos  = (preco_atual - don_low) / (don_high - don_low) if (don_high - don_low) > 0 else 0.5

        # Breakout Donchian — fechou acima/abaixo do canal 7d?
        don_breakout_up   = preco_atual >= don_high * 0.995
        don_breakout_down = preco_atual <= don_low  * 1.005

        del bars_1h
        df1h = None
        gc.collect()

        # ── WINDOW DELTA (sinal DOMINANTE pra mercado 5min) ──
        # Pesquisa 2026: indicador mais forte pra prediction binária é a variação % do BTC
        # desde a abertura da janela atual. RSI/EMA viram tiebreakers, não drivers.
        win_delta = _window_delta_pct(preco_atual)

        dados = dict(
            rsi=round(rsi, 2),
            ema9=ema9, ema21=ema21,
            mom=round(mom, 2),
            # Bollinger 15m
            bb_pos=round(bb_pos_15, 3),
            bb_breakout_up=bb_breakout_up,
            bb_breakout_down=bb_breakout_down,
            # Volume spike 15m
            vol_spike=round(vol_spike, 2),
            # Donchian 7d
            don_pos=round(don_pos, 3),
            don_breakout_up=don_breakout_up,
            don_breakout_down=don_breakout_down,
            # Variações
            var1m=round(var1m, 4),
            var3m=round(var3m, 4),
            preco=preco_atual,
            # Window Delta — sinal dominante pra 5min
            win_delta=round(win_delta, 4),
        )
        _cache_tec["ts"]   = agora
        _cache_tec["dados"] = dados
        return dados
    except Exception as e:
        print(f"{A}[WARN] Dados técnicos: {e}{X}")
        return _cache_tec["dados"]


def decidir_direcao(d) -> tuple:
    """
    v2.0 — Lógica melhorada:
    - Bollinger 15m (anti-fakeout)
    - Donchian 7 dias (confirmação breakout real)
    - Volume spike (confirma movimento)
    - Preço mínimo 0.45 (evita apostas de baixa probabilidade)
    """
    if d is None:
        return None, 0, []

    pontos_up   = 0
    pontos_down = 0
    razoes      = []

    # ── WINDOW DELTA (DOMINANTE — peso 50 quando forte) ─────
    # Pesquisa 2026: pra mercado 5min binário, esse é O sinal. Clássicos viram tiebreakers.
    wd = d.get("win_delta", 0.0)
    if wd >= 0.15:
        pontos_up += 50
        razoes.append(f"WinΔ +{wd:.2f}% FORTE↑")
    elif wd >= 0.05:
        pontos_up += 30
        razoes.append(f"WinΔ +{wd:.2f}%↑")
    elif wd >= 0.02:
        pontos_up += 10
        razoes.append(f"WinΔ +{wd:.2f}%")
    elif wd <= -0.15:
        pontos_down += 50
        razoes.append(f"WinΔ {wd:.2f}% FORTE↓")
    elif wd <= -0.05:
        pontos_down += 30
        razoes.append(f"WinΔ {wd:.2f}%↓")
    elif wd <= -0.02:
        pontos_down += 10
        razoes.append(f"WinΔ {wd:.2f}%")

    # ── RSI ──────────────────────────────────────────────────
    if d["rsi"] < 30:
        pontos_up += 30
        razoes.append(f"RSI oversold {d['rsi']:.1f}")
    elif d["rsi"] < 40:
        pontos_up += 15
        razoes.append(f"RSI baixo {d['rsi']:.1f}")
    elif d["rsi"] > 70:
        pontos_down += 30
        razoes.append(f"RSI overbought {d['rsi']:.1f}")
    elif d["rsi"] > 60:
        pontos_down += 15
        razoes.append(f"RSI alto {d['rsi']:.1f}")

    # ── EMA crossover ────────────────────────────────────────
    if d["ema9"] > d["ema21"]:
        pontos_up += 20
        razoes.append("EMA9>EMA21 bullish")
    else:
        pontos_down += 20
        razoes.append("EMA9<EMA21 bearish")

    # ── Momentum ─────────────────────────────────────────────
    if d["mom"] > 50:
        pontos_up += 15
        razoes.append(f"Mom+{d['mom']:.0f}")
    elif d["mom"] > 0:
        pontos_up += 7
    elif d["mom"] < -50:
        pontos_down += 15
        razoes.append(f"Mom{d['mom']:.0f}")
    elif d["mom"] < 0:
        pontos_down += 7

    # ── Bollinger 15m (anti-fakeout) ─────────────────────────
    if d["bb_breakout_up"]:
        pontos_down += 25   # breakout acima → reversão provável
        razoes.append("BB15m breakout UP→reversão")
    elif d["bb_breakout_down"]:
        pontos_up += 25     # breakout abaixo → reversão provável
        razoes.append("BB15m breakout DOWN→reversão")
    elif d["bb_pos"] < 0.2:
        pontos_up += 15
        razoes.append(f"BB15m baixo {d['bb_pos']:.2f}")
    elif d["bb_pos"] > 0.8:
        pontos_down += 15
        razoes.append(f"BB15m alto {d['bb_pos']:.2f}")

    # ── Donchian 7 dias ──────────────────────────────────────
    if d["don_breakout_up"]:
        pontos_up += 20     # breakout acima do canal 7d = tendência forte
        razoes.append("Donchian 7d breakout UP")
    elif d["don_breakout_down"]:
        pontos_down += 20
        razoes.append("Donchian 7d breakout DOWN")
    elif d["don_pos"] < 0.3:
        pontos_up += 10
        razoes.append(f"Don7d fundo {d['don_pos']:.2f}")
    elif d["don_pos"] > 0.7:
        pontos_down += 10
        razoes.append(f"Don7d topo {d['don_pos']:.2f}")

    # ── Volume spike (confirma movimento) ────────────────────
    if d["vol_spike"] > 1.8:
        # Volume alto confirma a direção dominante
        if pontos_up > pontos_down:
            pontos_up += 15
            razoes.append(f"Vol spike {d['vol_spike']:.1f}x ↑confirma")
        elif pontos_down > pontos_up:
            pontos_down += 15
            razoes.append(f"Vol spike {d['vol_spike']:.1f}x ↓confirma")

    total = pontos_up + pontos_down
    if total == 0:
        return None, 0, razoes

    if pontos_up > pontos_down:
        confianca = int(pontos_up / total * 100)
        return "UP", confianca, razoes
    elif pontos_down > pontos_up:
        confianca = int(pontos_down / total * 100)
        return "DOWN", confianca, razoes
    else:
        return None, 50, razoes

# ═══════════════════════════════════════════════════════════════
#  POLYMARKET
# ═══════════════════════════════════════════════════════════════

def extrair_float(resp, chaves=("price", "value", "amount", "balance")):
    if resp is None: return 0.0
    if isinstance(resp, (int, float)): return float(resp)
    if isinstance(resp, str):
        try: return float(resp)
        except: return 0.0
    if isinstance(resp, dict):
        for k in chaves:
            if k in resp:
                try: return float(resp[k])
                except: continue
    return 0.0

def tempo_restante():
    ts = int(time.time())
    return DURACAO_SLOT - (ts % DURACAO_SLOT)

def slot_atual_ts():
    ts = int(time.time())
    return ts - (ts % DURACAO_SLOT)

def conectar(tentativas=5):
    if not KEY or not FUNDER:
        print(f"{R}[ERRO] POLY_KEY ou POLY_FUNDER não definidos{X}")
        sys.exit(1)
    for i in range(tentativas):
        try:
            _sig_str = os.getenv("SIGNATURE_TYPE", "POLY_PROXY").upper()
            _sig = getattr(SignatureTypeV2, _sig_str, SignatureTypeV2.POLY_PROXY)
            c = ClobClient(HOST, key=KEY, chain_id=137, signature_type=_sig, funder=FUNDER)
            c.set_api_creds(c.derive_api_key())
            print(f"{V}[OK] Conectado ao Polymarket{X}")
            return c
        except Exception as e:
            print(f"{A}[WARN] Conexao falhou ({e}) — retry {2**i}s{X}")
            time.sleep(2 ** i)
    sys.exit(1)

def atualizar_cache(client, tentativas=3):
    slot = slot_atual_ts()
    if cache["valido"] and cache["slot"] == slot:
        return True
    for s in [slot, slot - DURACAO_SLOT]:
        slug = f"{SLUG_BASE}-{s}"
        for _ in range(tentativas):
            try:
                resp = requests.get(f"https://gamma-api.polymarket.com/markets?slug={slug}", timeout=10).json()
                if not resp: break
                m = resp[0]
                market = client.get_market(m["conditionId"])
                tokens = market.get("tokens", [])
                t_up   = next((t["token_id"] for t in tokens if t.get("outcome","").upper() in ["UP","YES"]), None)
                t_down = next((t["token_id"] for t in tokens if t.get("outcome","").upper() in ["DOWN","NO"]), None)
                if t_up and t_down:
                    cache.update(slot=slot, t_up=t_up, t_down=t_down,
                                 titulo=m.get("question","BTC UP/DOWN 5m"), valido=True)
                    print(f"\n{C}[CACHE] Slot: {slug}{X}")
                    return True
                break
            except requests.exceptions.Timeout:
                time.sleep(2)
            except:
                break
    cache["valido"] = False
    return False

def executar_ordem(client, token_id, preco, label, valor):
    if DRY_RUN:
        if preco <= 0:
            return False, None, f"preço inválido: {preco}"
        valor_real = max(valor, 5.0 * preco)
        size = round(valor_real / preco, 2)
        if size < 5.0:
            return False, None, f"size inválido: {size}"
        print(f"  [PAPER] {label}: {size} tokens @ {preco} (${valor_real:.2f})")
        try:
            with open(PAPER_LOG, "a") as f:
                f.write(f"{int(time.time())},{label},{preco:.4f},{size},{valor_real:.2f},{token_id}\n")
        except Exception:
            pass
        return True, f"paper-{int(time.time())}", None
    try:
        if preco <= 0:
            return False, None, f"preço inválido: {preco}"
        valor_real = max(valor, 5.0 * preco)  # garante size >= 5
        size = round(valor_real / preco, 2)
        if size < 5.0:
            return False, None, f"size inválido: {size}"
        args = OrderArgsV2(token_id=token_id, price=round(preco, 4), size=size, side=BUY)
        resp = client.post_order(client.create_order(args), OrderType.GTC)
        order_id = resp.get("orderID") or resp.get("id") if isinstance(resp, dict) else None
        print(f"{V}  [OK] {label}: {size} tokens @ {preco} (${valor_real:.2f}){X}")
        return True, order_id, None
    except Exception as e:
        print(f"{R}  [ERRO] {label}: {e}{X}")
        return False, None, str(e)

# ═══════════════════════════════════════════════════════════════
#  STOP-LOSS
# ═══════════════════════════════════════════════════════════════

def verificar_stop_loss():
    if estado["pnl"] <= -abs(STOP_LOSS):
        msg = f"🛑 *STOP-LOSS DIRECIONAL*\nPerda: `${abs(estado['pnl']):.2f}`\nTrades: `{estado['trades']}`"
        print(f"\n{R}{msg}{X}")
        enviar_telegram(msg)
        sys.exit(0)

# ═══════════════════════════════════════════════════════════════
#  LOOP PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def monitorar():
    print(f"\n{C}{'═'*60}")
    print(f"  BIT ADICT — BOT DIRECIONAL v2.0")
    print(f"  Valor/trade: ${VALOR_TRADE} | Stop: ${STOP_LOSS}")
    print(f"  Conf.mín: {CONFIANCA_MIN}% | Preço mín: {PRECO_MIN}")
    print(f"  Indicadores: RSI+EMA+Mom | BB15m | Donchian7d | VolSpike")
    print(f"{'═'*60}{X}\n")

    try:
        saldo = obter_saldo_usdc(FUNDER)
        allow = obter_allowance_usdc(FUNDER)
        print(f"{V}[Web3] Saldo: ${saldo:.2f} | Allowance: ${allow:.2f}{X}")
        if allow < VALOR_TRADE:
            print(f"{R}[AVISO] Allowance insuficiente! Aprova em polymarket.com{X}")
    except Exception as e:
        print(f"{A}[WARN] Web3: {e}{X}")

    client = conectar()

    # PnL tracker: marca posições históricas como baseline (não contam na sessão)
    init_pnl_tracker(FUNDER)

    threading.Thread(target=_polling_telegram, daemon=True).start()
    print(f"{V}[OK] Telegram iniciado{X}\n")

    enviar_telegram(
        f"🚀 *DIRECIONAL v2.0 iniciado!*\n"
        f"Valor/trade: `${VALOR_TRADE}` | Stop: `${STOP_LOSS}`\n"
        f"Confiança mín: `{CONFIANCA_MIN}%` | Preço: `{PRECO_MIN}-{PRECO_MAX}`\n"
        f"📊 BB15m + Donchian7d + VolSpike + RSI + EMA"
    )

    while True:
        try:
            if estado["encerrar"]:
                break

            atualizar_pnl_real(FUNDER)
            verificar_stop_loss()

            # Circuit breaker: 3/5 losses ou daily loss limit
            cb_paused, cb_reason = cb_is_paused()
            if cb_paused:
                print(f"\r{R}[CB PAUSADO] {cb_reason}{X}                                              ", end="")
                time.sleep(60)
                continue

            if estado["pausado"]:
                time.sleep(INTERVALO)
                continue

            # Dados técnicos e decisão
            d = obter_dados_tecnicos()
            direcao, confianca, razoes = decidir_direcao(d)

            tr = tempo_restante()

            # Dashboard linha
            dir_str = f"{V}▲ UP{X}" if direcao == "UP" else (f"{R}▼ DOWN{X}" if direcao == "DOWN" else f"{DIM}─ NEUTRO{X}")
            conf_cor = V if confianca >= CONFIANCA_MIN else A
            print(
                f"\r{C}{time.strftime('%H:%M:%S')}{X} │ "
                f"BTC:{C}${d['preco']:,.0f}{X} │ "
                f"RSI:{C}{d['rsi']:.1f}{X} │ "
                f"EMA:{V if d['ema9']>d['ema21'] else R}{'▲' if d['ema9']>d['ema21'] else '▼'}{X} │ "
                f"Dir:{dir_str} {conf_cor}{confianca}%{X} │ "
                f"T-{R if tr<TEMPO_MIN else V}{tr:03d}s{X} │ "
                f"P&L:{V if estado['pnl']>=0 else R}{estado['pnl']:+.2f}{X} │ "
                f"Win:{_taxa()}   ",
                end=""
            )

            # Condições para entrar
            mercado_ok = atualizar_cache(client)
            if not mercado_ok:
                time.sleep(INTERVALO)
                continue

            slot = cache["slot"]
            slot_novo = slot != estado["slot_executado"]

            if (direcao is not None and
                confianca >= CONFIANCA_MIN and
                tr >= TEMPO_MIN and
                slot_novo):

                # Escolhe token baseado na direção
                token_id = cache["t_up"] if direcao == "UP" else cache["t_down"]
                preco = extrair_float(
                    client.get_price(token_id, side="BUY"),
                    chaves=("price", "mid", "value")
                )

                if preco <= 0:
                    time.sleep(INTERVALO)
                    continue

                # ── Filtro: só entra quando indicador concorda com favorito do mercado ──
                # PRECO_MIN=0.55 → seu lado deve estar cotado >= 55% (consenso confirma indicador)
                # PRECO_MAX=0.80 → não compra caro demais (R/R ruim, ex: 0.97 → +$0.02 vs -$1.94)
                if preco < PRECO_MIN:
                    print(f"\n{A}[SKIP] {direcao} preço {preco:.2f} < {PRECO_MIN} — mercado discorda do indicador{X}")
                    time.sleep(INTERVALO)
                    continue
                if preco > PRECO_MAX:
                    print(f"\n{A}[SKIP] {direcao} preço {preco:.2f} > {PRECO_MAX} — caro demais (R/R ruim){X}")
                    time.sleep(INTERVALO)
                    continue

                # Verifica saldo (pulado em paper OU se SKIP_BALANCE_CHECK=true)
                # SKIP_BALANCE_CHECK: bypass quando cash real esta no proxy (nao no EOA Magic)
                if not DRY_RUN and not SKIP_BALANCE_CHECK:
                    saldo, saldo_ok = obter_saldo_usdc(FUNDER), True
                    if saldo < VALOR_TRADE * 1.05:
                        print(f"\n{R}[BLOQUEADO] Saldo insuficiente: ${saldo:.2f}{X}")
                        time.sleep(INTERVALO)
                        continue

                print(f"\n{V}╔{'═'*50}╗")
                print(f"║  ⚡ SINAL DIRECIONAL: {direcao} — Confiança {confianca}%")
                print(f"║  Preço {direcao}: {preco} | Valor: ${VALOR_TRADE}")
                print(f"║  Razões: {' | '.join(razoes[:3])}")
                print(f"╚{'═'*50}╝{X}")

                ok, order_id, erro = executar_ordem(client, token_id, preco, direcao, VALOR_TRADE)

                if ok:
                    estado["trades"] += 1
                    estado["slot_executado"] = slot
                    estado["ultima_direcao"] = direcao
                    # PnL estimado (ganho se acertar: ~$valor/preco * (1-preco) - fees)
                    ganho_pot = round(VALOR_TRADE / preco * (1 - preco) - VALOR_TRADE * 0.02, 3)

                    enviar_telegram(
                        f"🎯 *Trade Direcional — {direcao}*\n"
                        f"Confiança: `{confianca}%`\n"
                        f"Preço: `{preco}` | Valor: `${VALOR_TRADE}`\n"
                        f"Ganho potencial: `${ganho_pot:.3f}`\n"
                        f"📊 {' | '.join(razoes[:3])}\n"
                        f"P&L acum.: `${estado['pnl']:+.2f}` | Win: `{_taxa()}`"
                    )
                    print(f"{V}  ✔ Ordem enviada! Potencial: ${ganho_pot:.3f}{X}")
                    # hook Nostr best-effort: posta entrada em trade
                    try:
                        import sys as _sys
                        _sys.path.insert(0, str(__import__('pathlib').Path.home() / 'Bots/tiktok_pipeline'))
                        from post_nostr import publicar_trade
                        publicar_trade("DIRECIONAL v2", f"BTC {direcao} 5m", f"ENTROU conf={confianca}%", ganho_pot)
                    except Exception:
                        pass  # Nostr falha nao quebra o bot
                else:
                    print(f"{R}  ✗ Falhou: {erro}{X}")

            time.sleep(INTERVALO)

        except KeyboardInterrupt:
            break
        except Exception as e:
            err = str(e).lower()
            print(f"\n{R}[ERRO] {e}{X}")
            if any(k in err for k in ("connection", "timeout", "reset")):
                try:
                    client = conectar()
                except:
                    pass
            time.sleep(10)

    # Resumo final
    h, m = divmod(int(time.time()-estado["inicio"])//60, 60)
    print(f"\n{MAG}{'═'*45}")
    print(f"  DIRECIONAL — SESSÃO ENCERRADA")
    print(f"  P&L: ${estado['pnl']:+.2f} | Trades: {estado['trades']} | Win: {_taxa()}")
    print(f"  Uptime: {h:02d}h{m:02d}m")
    print(f"{'═'*45}{X}")
    enviar_telegram(
        f"⏹️ *Direcional encerrado*\n"
        f"P&L: `${estado['pnl']:+.2f}` | Win: `{_taxa()}`\n"
        f"Trades: `{estado['trades']}` | Uptime: `{h:02d}h{m:02d}m`"
    )


if __name__ == "__main__":
    monitorar()