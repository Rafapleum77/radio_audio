#!/usr/bin/env python3
"""
canal_feed.py CHANNEL_ID SAIDA.json — vídeos recentes de um canal do YouTube, para o site.

Tenta o RSS do canal (barato); se o YouTube responder 404 (em 11/10/2026 passou a
cair de vez em quando, para todos os canais), cai para o yt-dlp com data aproximada.
Escreve {"videos":[{id,title,date,published}], "channel"} em ordem do mais novo.
Usado pelo trezoitao_auto.sh para trezoitao.json e ulianov.json.
"""
import json, os, subprocess, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
YTDLP = "/opt/homebrew/bin/yt-dlp"


def via_rss(canal):
    req = urllib.request.Request(f"https://www.youtube.com/feeds/videos.xml?channel_id={canal}",
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        root = ET.fromstring(r.read().decode("utf-8"))
    out = []
    for e in root.findall("a:entry", NS):
        vid, t, pub = e.find("yt:videoId", NS), e.find("a:title", NS), e.find("a:published", NS)
        if vid is None or t is None:
            continue
        out.append({"id": vid.text, "title": t.text, "date": (pub.text or "")[:10], "published": pub.text or ""})
    return out


def via_ytdlp(canal, n=20):
    cmd = [YTDLP, "--no-update", "--flat-playlist", "--playlist-items", f"1:{n}",
           "--extractor-args", "youtubetab:approximate_date",
           "--print", "%(id)s\t%(upload_date)s\t%(timestamp)s\t%(title)s",
           f"https://www.youtube.com/channel/{canal}/videos"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    out = []
    for linha in r.stdout.splitlines():
        partes = linha.split("\t", 3)
        if len(partes) < 4 or not partes[0]:
            continue
        vid, data, ts, titulo = partes
        if ts not in ("NA", ""):
            pub = datetime.fromtimestamp(int(float(ts)), tz=timezone.utc).isoformat()
        elif data not in ("NA", ""):
            pub = f"{data[:4]}-{data[4:6]}-{data[6:8]}T00:00:00+00:00"
        else:
            pub = ""
        out.append({"id": vid, "title": titulo, "date": pub[:10], "published": pub})
    if not out:
        raise RuntimeError("yt-dlp sem resultado: " + r.stderr[-300:])
    return out


def main():
    canal, saida = sys.argv[1], Path(sys.argv[2]).expanduser()
    try:
        videos, fonte = via_rss(canal), "rss"
    except Exception as e:
        videos, fonte = via_ytdlp(canal), f"yt-dlp (rss falhou: {str(e)[:60]})"
    videos.sort(key=lambda v: v.get("published", ""), reverse=True)
    payload = json.dumps({"videos": videos, "channel": canal}, ensure_ascii=False, indent=2)
    tmp = saida.with_suffix(".json.tmp")   # escrita atômica: nunca deixa JSON truncado
    tmp.write_text(payload)
    os.replace(tmp, saida)
    topo = videos[0]["title"][:60] if videos else "(vazio)"
    print(f"{saida.name}: {len(videos)} vídeos via {fonte} | topo: {topo}")


if __name__ == "__main__":
    main()
