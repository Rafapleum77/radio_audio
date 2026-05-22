#!/usr/bin/env python3
"""
Relatório diário de fluxo de capital nos mercados globais.
Roda às 22h via LaunchAgent. Cobre: Cryptos, Metais, Energia, Indices, FX.

Output:
 - ~/Bots/RESULTADOS/mercado_global_<YYYY-MM-DD>.json
 - ~/Bots/RESULTADOS/mercado_global_latest.md
 - Telegram (quando token estiver configurado)
"""
import os, json, sys, requests
from datetime import datetime, timedelta
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print("yfinance não instalado. Roda: py -3.11 -m pip install yfinance", file=sys.stderr)
    sys.exit(1)

OUT_DIR = Path.home() / "Bots/RESULTADOS"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TG_TOKEN = os.getenv("TG_WATCHDOG_TOKEN", "")
TG_CHAT  = os.getenv("TG_WATCHDOG_CHAT", "6239727715")

# Tickers organizados por classe
ATIVOS = {
    "🪙 Cryptos": {
        "BTC":  "BTC-USD",
        "ETH":  "ETH-USD",
        "XRP":  "XRP-USD",
        "SOL":  "SOL-USD",
        "BNB":  "BNB-USD",
    },
    "🥇 Metais": {
        "Ouro (GC=F)":    "GC=F",
        "Prata (SI=F)":   "SI=F",
        "Platina (PL=F)": "PL=F",
        "Cobre (HG=F)":   "HG=F",
    },
    "⛽ Energia": {
        "WTI (CL=F)":      "CL=F",
        "Brent (BZ=F)":    "BZ=F",
        "Nat Gas (NG=F)":  "NG=F",
    },
    "📈 Índices": {
        "S&P 500":  "^GSPC",
        "Nasdaq":   "^IXIC",
        "Dow":      "^DJI",
        "VIX":      "^VIX",
    },
    "💵 FX / Dollar": {
        "DXY (Dollar Index)": "DX-Y.NYB",
        "EUR/USD":            "EURUSD=X",
        "USD/BRL":            "USDBRL=X",
    },
    "💸 ETFs (fluxo institucional)": {
        "IBIT (Bitcoin ETF)":   "IBIT",
        "GLD (Gold ETF)":       "GLD",
        "SLV (Silver ETF)":     "SLV",
        "USO (Oil ETF)":        "USO",
        "DBC (Commodities)":    "DBC",
        "TLT (20y Treasury)":   "TLT",
    },
}

def coletar(ticker):
    """Retorna dict com price, %1d, %7d, %30d, volume, notional_usd.
    Ajuste por tipo: crypto volume já é USD; stocks/ETFs volume×price=USD; futures/FX sem notional confiável."""
    try:
        import math
        t = yf.Ticker(ticker)
        hist = t.history(period="35d", interval="1d", auto_adjust=False)
        if hist.empty or len(hist) < 2:
            return None
        last = hist.iloc[-1]
        prev = hist.iloc[-2]
        week_ago = hist.iloc[-6] if len(hist) >= 6 else prev
        month_ago = hist.iloc[0]

        price = float(last["Close"])
        vol = float(last.get("Volume") or 0)
        if math.isnan(price) or price <= 0:
            return None

        # Classifica notional USD
        if ticker.endswith("-USD"):  # crypto: volume yfinance já em USD
            notional = vol
        elif ticker.endswith("=F"):  # futures: volume = contratos, ignora
            notional = 0
        elif ticker.endswith("=X") or ticker.startswith("^"):  # FX/indices: sem volume USD confiável
            notional = 0
        else:  # equities/ETFs: shares × price
            notional = price * vol

        def safe_pct(a, b):
            try:
                if b == 0 or math.isnan(b) or math.isnan(a):
                    return 0.0
                return round((a - b) / b * 100, 2)
            except Exception:
                return 0.0

        return {
            "price":   round(price, 4),
            "ch_1d":   safe_pct(price, float(prev["Close"])),
            "ch_7d":   safe_pct(price, float(week_ago["Close"])),
            "ch_30d":  safe_pct(price, float(month_ago["Close"])),
            "volume":  round(vol, 2),
            "notional_usd": round(notional, 2),
            "high_30d": round(float(hist["High"].max()), 4),
            "low_30d":  round(float(hist["Low"].min()), 4),
        }
    except Exception as e:
        print(f"  [WARN] {ticker}: {e}", file=sys.stderr)
        return None

def categoria_score(dados_categoria):
    """Soma %1d dos ativos da categoria pra medir 'pra onde dinheiro está fluindo'."""
    import math
    valores = [d["ch_1d"] for d in dados_categoria.values() if d and not math.isnan(d.get("ch_1d") or 0)]
    if not valores:
        return 0.0
    return round(sum(valores) / len(valores), 2)

def main():
    hoje = datetime.now().strftime("%Y-%m-%d")
    relatorio = {"data": hoje, "gerado_em": datetime.now().isoformat(), "classes": {}}

    print(f"=== Relatório Mercado Global — {hoje} ===\n", flush=True)

    todos_ativos = []
    for categoria, tickers in ATIVOS.items():
        print(f"\n{categoria}:", flush=True)
        dados_cat = {}
        for nome, ticker in tickers.items():
            d = coletar(ticker)
            if d is None:
                print(f"  {nome}: sem dados", flush=True)
                continue
            dados_cat[nome] = d
            todos_ativos.append({"nome": nome, "categoria": categoria, **d})
            seta = "🟢" if d["ch_1d"] >= 0 else "🔴"
            print(f"  {seta} {nome:30s}  ${d['price']:>10,.2f}  1d:{d['ch_1d']:+6.2f}%  7d:{d['ch_7d']:+6.2f}%  30d:{d['ch_30d']:+7.2f}%  vol${d['notional_usd']/1e9:>6.2f}B", flush=True)
        relatorio["classes"][categoria] = {
            "ativos": dados_cat,
            "score_1d": categoria_score(dados_cat),
        }

    # ── Ranking onde o dinheiro está indo (por classe) ─────
    print("\n\n=== RANKING DE FLUXO (média %1d por classe) ===", flush=True)
    ranking_classes = sorted(
        [(c, relatorio["classes"][c]["score_1d"]) for c in relatorio["classes"]],
        key=lambda x: x[1], reverse=True
    )
    for c, score in ranking_classes:
        seta = "🟢" if score >= 0 else "🔴"
        print(f"  {seta} {c:35s} {score:+6.2f}%", flush=True)
    relatorio["ranking_classes"] = ranking_classes

    # ── Maior volume notional do dia (em USD) ──────────────
    print("\n=== TOP 5 MAIOR VOLUME NEGOCIADO (USD) ===", flush=True)
    com_volume = [a for a in todos_ativos if a.get("notional_usd", 0) > 0]
    com_volume.sort(key=lambda x: x.get("notional_usd", 0), reverse=True)
    top_volume = []
    for a in com_volume[:5]:
        print(f"  {a['nome']:30s}  ${a['notional_usd']/1e9:>8.2f}B   {a['ch_1d']:+6.2f}%", flush=True)
        top_volume.append({"nome": a["nome"], "notional_usd": a["notional_usd"], "ch_1d": a["ch_1d"]})
    relatorio["top_volume_dia"] = top_volume

    # ── Top performers e perdedores do dia ─────────────────
    print("\n=== TOP GAINERS 1d ===", flush=True)
    gainers = sorted([a for a in todos_ativos if a.get("ch_1d")], key=lambda x: x["ch_1d"], reverse=True)[:5]
    for a in gainers:
        print(f"  🟢 {a['nome']:30s}  {a['ch_1d']:+6.2f}%  (${a['price']:,.2f})", flush=True)

    print("\n=== TOP LOSERS 1d ===", flush=True)
    losers = sorted([a for a in todos_ativos if a.get("ch_1d")], key=lambda x: x["ch_1d"])[:5]
    for a in losers:
        print(f"  🔴 {a['nome']:30s}  {a['ch_1d']:+6.2f}%  (${a['price']:,.2f})", flush=True)

    relatorio["top_gainers"]  = [{"nome": a["nome"], "ch_1d": a["ch_1d"], "price": a["price"]} for a in gainers]
    relatorio["top_losers"]   = [{"nome": a["nome"], "ch_1d": a["ch_1d"], "price": a["price"]} for a in losers]

    # ── Salva JSON ─────────────────────────────────────────
    out_json = OUT_DIR / f"mercado_global_{hoje}.json"
    with open(out_json, "w") as f:
        json.dump(relatorio, f, indent=2)
    print(f"\n💾 JSON: {out_json}", flush=True)

    # ── Markdown ───────────────────────────────────────────
    md = [f"# Mercado Global — {hoje}\n"]
    md.append(f"_Gerado: {datetime.now().strftime('%H:%M:%S')}_\n")
    md.append("## Ranking de fluxo (média %1d por classe)\n")
    for c, score in ranking_classes:
        s = "🟢" if score >= 0 else "🔴"
        md.append(f"- {s} **{c}** — `{score:+.2f}%`")
    md.append("\n## Top 5 volume negociado (USD)\n")
    md.append("| Ativo | Volume Notional | %1d |")
    md.append("|-------|-----------------|-----|")
    for a in top_volume:
        md.append(f"| {a['nome']} | ${a['notional_usd']/1e9:.2f}B | {a['ch_1d']:+.2f}% |")
    md.append("\n## Top gainers / losers\n")
    md.append("| Ativo | %1d | Preço |")
    md.append("|-------|-----|-------|")
    for a in gainers + losers:
        s = "🟢" if a["ch_1d"] >= 0 else "🔴"
        md.append(f"| {s} {a['nome']} | {a['ch_1d']:+.2f}% | ${a['price']:,.2f} |")

    md.append("\n## Detalhe por classe\n")
    for categoria, info in relatorio["classes"].items():
        md.append(f"### {categoria}\n")
        md.append("| Ativo | Preço | %1d | %7d | %30d | Volume |")
        md.append("|-------|-------|-----|-----|------|--------|")
        for nome, d in info["ativos"].items():
            s = "🟢" if d["ch_1d"] >= 0 else "🔴"
            vol_b = d["notional_usd"]/1e9 if d["notional_usd"] > 1e9 else d["notional_usd"]/1e6
            vol_unit = "B" if d["notional_usd"] > 1e9 else "M"
            md.append(f"| {s} {nome} | ${d['price']:,.2f} | {d['ch_1d']:+.2f}% | {d['ch_7d']:+.2f}% | {d['ch_30d']:+.2f}% | ${vol_b:.2f}{vol_unit} |")
        md.append("")

    out_md = OUT_DIR / "mercado_global_latest.md"
    with open(out_md, "w") as f:
        f.write("\n".join(md))
    print(f"📝 MD:   {out_md}", flush=True)

    # ── Telegram summary (curtinho) ────────────────────────
    if TG_TOKEN:
        try:
            tg_msg = f"📊 *Mercado Global {hoje}*\n\n*Fluxo por classe (%1d):*\n"
            for c, s in ranking_classes:
                emoji = "🟢" if s >= 0 else "🔴"
                tg_msg += f"{emoji} {c}: `{s:+.2f}%`\n"
            tg_msg += "\n*Top 3 volume hoje:*\n"
            for a in top_volume[:3]:
                tg_msg += f"• {a['nome']}: `${a['notional_usd']/1e9:.1f}B` ({a['ch_1d']:+.2f}%)\n"
            tg_msg += f"\n📝 Detalhe: `mercado_global_latest.md`"
            requests.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                data={"chat_id": TG_CHAT, "text": tg_msg, "parse_mode": "Markdown"},
                timeout=10,
            )
        except Exception as e:
            print(f"[Telegram] {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
