#!/usr/bin/env python3
"""
copa2026_update.py — busca todos os jogos da Copa do Mundo 2026 (TheSportsDB)
e escreve copa2026.json no repo da rádio. Resultados + próximos jogos com horário BRT.
Roda diariamente via launchd.
"""
import json, urllib.request
from pathlib import Path
from datetime import datetime, timezone, timedelta

LEAGUE = 4429          # FIFA World Cup
SEASON = "2026"
KEY = "123"            # chave de teste pública do TheSportsDB
BASE = f"https://www.thesportsdb.com/api/v1/json/{KEY}"
OUT = Path.home() / "Desktop" / "radio_audio" / "copa2026.json"
BRT = timezone(timedelta(hours=-3))

# rodadas: grupo 1-3 (24 cada) + mata-mata (códigos TheSportsDB)
ROUNDS = {
    1: "1ª Rodada", 2: "2ª Rodada", 3: "3ª Rodada",
    200: "16-avos", 125: "Oitavas", 150: "Quartas",
    160: "Semifinal", 170: "Disputa 3º", 180: "FINAL",
}

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())

def main():
    jogos = []
    for r, label in ROUNDS.items():
        try:
            d = fetch(f"{BASE}/eventsround.php?id={LEAGUE}&r={r}&s={SEASON}")
        except Exception as e:
            print(f"round {r} erro: {e}"); continue
        for e in (d.get("events") or []):
            # horário UTC → BRT
            data = e.get("dateEvent") or ""
            hora = e.get("strTime") or "00:00:00"
            dt_brt = ""
            try:
                dt = datetime.strptime(f"{data} {hora[:8]}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                dt_brt = dt.astimezone(BRT).strftime("%Y-%m-%d %H:%M")
            except Exception:
                dt_brt = data
            hs = e.get("intHomeScore"); aw = e.get("intAwayScore")
            jogado = hs is not None and aw is not None and str(hs) != "" and str(aw) != ""
            jogos.append({
                "rodada": label,
                "grupo": e.get("strGroup") or "",
                "data": data,
                "datahora_brt": dt_brt,
                "casa": e.get("strHomeTeam"),
                "fora": e.get("strAwayTeam"),
                "placar_casa": int(hs) if jogado else None,
                "placar_fora": int(aw) if jogado else None,
                "jogado": jogado,
                "status": e.get("strStatus") or "",
            })
    # dedup por id casa+fora+data
    vistos = set(); unicos = []
    for j in jogos:
        k = (j["data"], j["casa"], j["fora"])
        if k in vistos: continue
        vistos.add(k); unicos.append(j)
    unicos.sort(key=lambda x: x["datahora_brt"] or x["data"])

    # ── Classificação dos grupos (calculada dos resultados) ──
    tabelas = {}  # grupo -> {time: stats}
    for j in unicos:
        g = j.get("grupo")
        if not g or not j["jogado"]:
            continue
        for time in (j["casa"], j["fora"]):
            tabelas.setdefault(g, {}).setdefault(time, {
                "time": time, "P": 0, "J": 0, "V": 0, "E": 0, "D": 0, "GP": 0, "GC": 0, "SG": 0})
        ch, cf = j["placar_casa"], j["placar_fora"]
        c, f = tabelas[g][j["casa"]], tabelas[g][j["fora"]]
        c["J"] += 1; f["J"] += 1
        c["GP"] += ch; c["GC"] += cf; f["GP"] += cf; f["GC"] += ch
        if ch > cf:   c["V"] += 1; c["P"] += 3; f["D"] += 1
        elif cf > ch: f["V"] += 1; f["P"] += 3; c["D"] += 1
        else:         c["E"] += 1; f["E"] += 1; c["P"] += 1; f["P"] += 1
    grupos = {}
    for g, times in tabelas.items():
        for t in times.values():
            t["SG"] = t["GP"] - t["GC"]
        grupos[g] = sorted(times.values(), key=lambda x: (-x["P"], -x["SG"], -x["GP"]))

    out = {
        "torneio": "Copa do Mundo FIFA 2026",
        "atualizado_em": datetime.now(BRT).isoformat(timespec="seconds"),
        "total_jogos": len(unicos),
        "jogos": unicos,
        "grupos": {g: grupos[g] for g in sorted(grupos)},
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"copa2026.json: {len(unicos)} jogos -> {OUT}")

if __name__ == "__main__":
    main()
