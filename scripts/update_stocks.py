#!/usr/bin/env python3
"""Atualiza stocks.json com cotacao Yahoo Finance dos picks do Rafael."""
import json
import sys
import time
from datetime import datetime, timezone

import yfinance as yf

TICKERS = [
    ("MSTR", "Strategy (Saylor)", "strategy.com"),
    ("STRK", "Strategy Pref 8%", "strategy.com"),
    ("IBIT", "iShares BTC ETF", "blackrock.com"),
    ("FBTC", "Fidelity BTC ETF", "fidelity.com"),
    ("SPCX", "SpaceX", "spacex.com"),
    ("NVDA", "NVIDIA", "nvidia.com"),
    ("TSLA", "Tesla", "tesla.com"),
    ("AAPL", "Apple", "apple.com"),
    ("AMZN", "Amazon", "amazon.com"),
    ("GOOGL", "Alphabet", "google.com"),
    ("INTC", "Intel", "intel.com"),
    ("QCOM", "Qualcomm", "qualcomm.com"),
    ("MU", "Micron", "micron.com"),
    ("TSM", "Taiwan Semi", "tsmc.com"),
    ("INOD", "Innodata", "innodata.com"),
]


def fetch(symbol: str) -> dict:
    t = yf.Ticker(symbol)
    info = t.fast_info
    price = getattr(info, "last_price", None)
    prev = getattr(info, "previous_close", None)
    currency = getattr(info, "currency", "USD")
    if price is None or prev is None:
        raise ValueError(f"sem dados pra {symbol}")
    change_abs = price - prev
    change_pct = (change_abs / prev) * 100
    # market state via info dict (pode falhar silenciosamente, tudo bem)
    try:
        market_state = t.info.get("marketState", "UNKNOWN")
    except Exception:
        market_state = "UNKNOWN"
    return {
        "symbol": symbol,
        "price": round(price, 2),
        "previous_close": round(prev, 2),
        "change_abs": round(change_abs, 2),
        "change_pct": round(change_pct, 2),
        "currency": currency or "USD",
        "market_state": market_state,
    }


def main():
    out = {"updated_at": datetime.now(timezone.utc).isoformat(), "tickers": []}
    erros = []
    for sym, name, domain in TICKERS:
        try:
            d = fetch(sym)
            d["name"] = name
            d["logo"] = f"https://cdn.brandfetch.io/{domain}/w/200/h/200"
            out["tickers"].append(d)
            print(f"OK {sym}: {d['price']} {d['currency']} ({d['change_pct']:+.2f}%)")
            time.sleep(0.2)
        except Exception as e:
            erros.append(f"{sym}: {e}")
            print(f"ERRO {sym}: {e}", file=sys.stderr)
    out["errors"] = erros

    with open("stocks.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"Saved stocks.json — {len(out['tickers'])}/{len(TICKERS)} OK")
    return 0 if out["tickers"] else 1


if __name__ == "__main__":
    sys.exit(main())
