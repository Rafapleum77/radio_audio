#!/usr/bin/env python3
"""Busca RSS da LiveCoins e salva livecoins.json no diretório da rádio.
Faz commit+push apenas se o conteúdo mudou.
Roda via launchd a cada hora."""
import json, hashlib, subprocess, os, sys
from pathlib import Path
from datetime import datetime
import urllib.request, xml.etree.ElementTree as ET

BASE = Path(__file__).parent
OUT  = BASE / "livecoins.json"
# 2026-08-31: a LiveCoins passou a devolver 403 pra esta maquina — no site
# inteiro, nao so no feed, e com qualquer User-Agent. Bloqueio deles, nada que
# se conserte daqui. Fonte unica e ponto unico de falha: agora sao varias, e a
# primeira que responder ganha. O nome do arquivo continua livecoins.json
# porque o site inteiro ja aponta pra ele.
FONTES = [
    ("LiveCoins",   "https://livecoins.com.br/feed/"),
    ("CriptoFacil", "https://www.criptofacil.com/feed/"),
    ("Portal do Bitcoin", "https://portaldobitcoin.uol.com.br/feed/"),
    ("Cointelegraph BR",  "https://br.cointelegraph.com/rss"),
]
NAVEGADOR = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36")
MAX  = 8

def fetch():
    """Tenta as fontes na ordem e devolve (xml, nome da fonte que respondeu)."""
    erros = []
    for nome, url in FONTES:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": NAVEGADOR})
            with urllib.request.urlopen(req, timeout=20) as r:
                bruto = r.read()
            ET.fromstring(bruto)          # so vale se for XML de verdade
            if nome != FONTES[0][0]:
                print(f"  (LiveCoins fora do ar; usando {nome})")
            return bruto, nome
        except Exception as e:
            erros.append(f"{nome}: {type(e).__name__}")
    raise RuntimeError("nenhuma fonte respondeu — " + " | ".join(erros))

def parse(xml_bytes):
    root = ET.fromstring(xml_bytes)
    items = []
    for it in root.findall(".//item")[:MAX]:
        desc = it.findtext("description") or ""
        # Remove tags HTML da descrição
        import re
        desc = re.sub(r"<[^>]+>", "", desc).strip()[:220]
        items.append({
            "title": (it.findtext("title") or "").strip(),
            "link":  (it.findtext("link") or "").strip(),
            "date":  (it.findtext("pubDate") or "").strip(),
            "desc":  desc,
        })
    return items

def main():
    print(f"[{datetime.now():%H:%M}] Buscando LiveCoins RSS...")
    try:
        xml_bytes, fonte = fetch()
        articles  = parse(xml_bytes)
        for a in articles:
            a["fonte"] = fonte
    except Exception as e:
        print(f"  Erro: {e}")
        sys.exit(1)

    payload = {"updated": datetime.utcnow().isoformat() + "Z", "articles": articles}
    new_json = json.dumps(payload, ensure_ascii=False, indent=2)
    new_hash = hashlib.md5(new_json.encode()).hexdigest()

    # Verifica se mudou
    if OUT.exists():
        old_hash = hashlib.md5(OUT.read_text(encoding="utf-8").encode()).hexdigest()
        if old_hash == new_hash:
            print("  Sem mudanças — nada a fazer.")
            return

    OUT.write_text(new_json, encoding="utf-8")
    print(f"  {len(articles)} artigos salvos em {OUT.name}")

    # Commit + push
    try:
        # 31/08: nao mexer na arvore de trabalho. O `pull --rebase --autostash`
        # reescreve arquivos, e 5 mp3 versionados estao na playlist.txt que o
        # ffmpeg le AO VIVO — trocar um deles derruba a radio. Quem publica e o
        # com.radiobitcoin.git-guardiao (15min), que espera a playlist ficar livre.
        subprocess.run(["git", "add", str(OUT)], cwd=BASE, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "chore(livecoins): atualizar feed [skip ci]"], cwd=BASE, check=True, capture_output=True)
        print("  Commitado; o guardiao publica.")
    except subprocess.CalledProcessError as e:
        print(f"  Git: {e.stderr.decode() if e.stderr else e}")

if __name__ == "__main__":
    main()
