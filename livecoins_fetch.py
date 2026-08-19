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
RSS  = "https://livecoins.com.br/feed/"
MAX  = 8

def fetch():
    req = urllib.request.Request(RSS, headers={"User-Agent": "Mozilla/5.0 RadioBitcoin/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read()

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
        xml_bytes = fetch()
        articles  = parse(xml_bytes)
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
        subprocess.run(["git", "pull", "--rebase", "--autostash"], cwd=BASE, check=True, capture_output=True)
        subprocess.run(["git", "add", str(OUT)], cwd=BASE, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "chore(livecoins): atualizar feed [skip ci]"], cwd=BASE, check=True, capture_output=True)
        subprocess.run(["git", "push"], cwd=BASE, check=True, capture_output=True)
        print("  Push feito.")
    except subprocess.CalledProcessError as e:
        print(f"  Git: {e.stderr.decode() if e.stderr else e}")

if __name__ == "__main__":
    main()
