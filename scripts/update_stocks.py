#!/usr/bin/env python3
"""Atualiza stocks.json com cotacao Yahoo Finance dos picks do Rafael."""
import json
import sys
import time
from datetime import datetime, timezone
import urllib.request
import urllib.error

TICKERS = [
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

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"

def fetch(symbol: str) -> dict:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    result = data["chart"]["result"][0]
    meta = result["meta"]
    price = meta.get("regularMarketPrice")
    prev = meta.get("chartPreviousClose") or meta.get("previousClose")
    if price is None or prev is None:
        raise ValueError(f"sem dados pra {symbol}")
    change_abs = price - prev
    change_pct = (change_abs / prev) * 100
    return {
        "symbol": symbol,
        "price": round(price, 2),
        "previous_close": round(prev, 2),
        "change_abs": round(change_abs, 2),
        "change_pct": round(change_pct, 2),
        "currency": meta.get("currency", "USD"),
        "market_state": meta.get("marketState", "UNKNOWN"),
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
            time.sleep(0.3)
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
