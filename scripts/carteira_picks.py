#!/usr/bin/env python3.11
"""
carteira_picks.py — puxa precos + indicadores tecnicos de 12 tickers
e gera carteira.json com recomendacao BUY/HOLD/SELL (perfil arrojado).

Roda a cada 30 min via LaunchAgent com.surfgael.carteira-picks em
market hours US (~10h-17h BR).

Tickers monitorados:
  Acoes:        TSLA INTC TSM NVDA INOD MU QCOM CWEN
  Commodities:  USO XLE IAU SLV

Saida: ~/Bots/radio/carteira.json + commit/push pro repo.
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import yfinance as yf
import pandas as pd
import numpy as np
import subprocess

OUT_JSON = Path.home() / "Bots/radio/carteira.json"
RADIO = Path.home() / "Bots/radio"

# Perfil ARROJADO — tolera RSI alto, favorece momentum
TICKERS = {
    "TSLA": {"nome": "Tesla",            "setor": "EV/Auto"},
    "INTC": {"nome": "Intel",            "setor": "Semi"},
    "TSM":  {"nome": "Taiwan Semi",      "setor": "Semi Foundry"},
    "NVDA": {"nome": "Nvidia",           "setor": "Semi GPU/AI"},
    "INOD": {"nome": "Innodata",         "setor": "AI Data"},
    "MU":   {"nome": "Micron",           "setor": "Semi Memory"},
    "QCOM": {"nome": "Qualcomm",         "setor": "Semi Mobile"},
    "CWEN": {"nome": "Clearway Energy",  "setor": "Renewable"},
    "USO":  {"nome": "United States Oil","setor": "Commodity Oil"},
    "XLE":  {"nome": "Energy SPDR",      "setor": "Energy Sector"},
    "IAU":  {"nome": "iShares Gold",     "setor": "Commodity Gold"},
    "SLV":  {"nome": "iShares Silver",   "setor": "Commodity Silver"},
}


def calc_rsi(closes, period=14):
    delta = closes.diff()
    up = delta.clip(lower=0).rolling(period).mean()
    dn = -delta.clip(upper=0).rolling(period).mean()
    rs = up / dn
    return 100 - (100 / (1 + rs))


def calc_macd(closes, fast=12, slow=26, signal=9):
    ema_fast = closes.ewm(span=fast, adjust=False).mean()
    ema_slow = closes.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    sig  = macd.ewm(span=signal, adjust=False).mean()
    return macd, sig


def reco_arrojada(rsi, macd_val, sig_val, price, sma50, sma200, pct52w):
    """Indicador composto pra perfil ARROJADO — favorece momentum, tolera RSI<=75."""
    macd_up   = macd_val > sig_val
    above_50  = price > sma50
    above_200 = price > sma200
    near_high = pct52w > 0.85
    near_low  = pct52w < 0.20

    # STRONG BUY: tendencia forte sem topo
    if above_50 and above_200 and macd_up and rsi < 65 and not near_high:
        return ("STRONG BUY", "Tendencia forte multi-prazo + momentum positivo, longe do topo 52w")
    # BUY: tendencia OK, RSI ainda saudavel
    if above_200 and macd_up and rsi < 70:
        return ("BUY", "Tendencia longa positiva + MACD bullish")
    # ACUMULAR: oversold em tendencia ainda viva
    if above_200 and rsi < 35 and near_low:
        return ("ACUMULAR", "Oversold em fundo 52w, tendencia longa intacta — entrada de qualidade")
    # TRIM: euforia, perto do topo
    if rsi > 75 and near_high:
        return ("TRIM", "RSI superaquecido + perto do topo 52w — realizar parcial")
    # SELL: quebra de tendencia longa
    if not above_200 and not macd_up:
        return ("SELL", "Abaixo SMA200 + MACD bearish — tendencia quebrou")
    # HOLD
    return ("HOLD", "Sem sinal claro — manter posicao")


def analyze_ticker(symbol):
    try:
        tk = yf.Ticker(symbol)
        h  = tk.history(period="1y", auto_adjust=True)
        if h.empty or len(h) < 50:
            return None
        closes = h["Close"]
        price = float(closes.iloc[-1])
        prev  = float(closes.iloc[-2])
        chg_pct = (price / prev - 1) * 100

        sma50  = float(closes.rolling(50).mean().iloc[-1])
        sma200 = float(closes.rolling(200).mean().iloc[-1]) if len(closes) >= 200 else float(closes.rolling(min(50, len(closes))).mean().iloc[-1])
        rsi    = float(calc_rsi(closes).iloc[-1])
        macd, sig = calc_macd(closes)
        macd_v = float(macd.iloc[-1])
        sig_v  = float(sig.iloc[-1])

        high52 = float(closes.max())
        low52  = float(closes.min())
        pct52w = (price - low52) / (high52 - low52) if high52 > low52 else 0.5

        reco, racional = reco_arrojada(rsi, macd_v, sig_v, price, sma50, sma200, pct52w)

        return {
            "symbol": symbol,
            "price": round(price, 2),
            "change_pct_1d": round(chg_pct, 2),
            "rsi": round(rsi, 1),
            "sma50": round(sma50, 2),
            "sma200": round(sma200, 2),
            "macd": round(macd_v, 3),
            "macd_signal": round(sig_v, 3),
            "macd_bullish": macd_v > sig_v,
            "above_sma50": price > sma50,
            "above_sma200": price > sma200,
            "high_52w": round(high52, 2),
            "low_52w": round(low52, 2),
            "pct_52w_range": round(pct52w * 100, 1),
            "reco": reco,
            "racional": racional,
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e)[:120]}


def main():
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] carteira_picks iniciado", flush=True)
    rows = []
    for sym, meta in TICKERS.items():
        r = analyze_ticker(sym)
        if r:
            r.update(meta)
            rows.append(r)
            status = "OK" if "error" not in r else "ERRO"
            print(f"  {sym:5s} {status} reco={r.get('reco','?')} price={r.get('price','?')}", flush=True)

    out = {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "perfil": "arrojado",
        "tickers": rows,
        "resumo": {
            "total_tickers": len(rows),
            "buy_signals":    sum(1 for r in rows if r.get("reco") in ("STRONG BUY", "BUY", "ACUMULAR")),
            "hold_signals":   sum(1 for r in rows if r.get("reco") == "HOLD"),
            "sell_signals":   sum(1 for r in rows if r.get("reco") in ("TRIM", "SELL")),
        },
    }

    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nSAIDA: {OUT_JSON} ({len(rows)} tickers)", flush=True)

    # commit + push (idempotente — so altera se houver mudanca)
    try:
        subprocess.run(["git", "-C", str(RADIO), "add", "carteira.json"], check=True)
        r = subprocess.run(["git", "-C", str(RADIO), "diff", "--cached", "--quiet"])
        if r.returncode != 0:  # ha mudancas
            subprocess.run(["git", "-C", str(RADIO), "commit", "-m", "carteira: update auto"], check=True)
            subprocess.run(["git", "-C", str(RADIO), "push"], check=False)
            print("commit + push OK")
        else:
            print("sem mudancas")
    except Exception as e:
        print(f"git skip: {e}")


if __name__ == "__main__":
    main()
