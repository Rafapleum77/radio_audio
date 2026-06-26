#!/usr/bin/env python3
"""
trezoitao_feed.py — busca o RSS do canal Rotina do Trezoitão (server-side, sem CORS)
e escreve trezoitao.json no repo da rádio. O frontend lê esse estático (confiável),
sem depender de proxies CORS instáveis.
"""
import json, re, urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

CHANNEL_ID = "UCC-r6vnXtcwBYq0VxZYhoXg"
RSS = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
OUT = Path.home() / "Desktop" / "radio_audio" / "trezoitao.json"
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}

def main():
    req = urllib.request.Request(RSS, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        xml = r.read().decode("utf-8")
    root = ET.fromstring(xml)
    videos = []
    for e in root.findall("a:entry", NS):
        vid = e.find("yt:videoId", NS)
        title = e.find("a:title", NS)
        pub = e.find("a:published", NS)
        if vid is None or title is None:
            continue
        videos.append({
            "id": vid.text,
            "title": title.text,
            "date": (pub.text or "")[:10],
        })
    OUT.write_text(json.dumps({"videos": videos, "channel": CHANNEL_ID}, ensure_ascii=False, indent=2))
    print(f"trezoitao.json: {len(videos)} vídeos -> {OUT}")

if __name__ == "__main__":
    main()
