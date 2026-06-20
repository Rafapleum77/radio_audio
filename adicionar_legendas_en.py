#!/usr/bin/env python3
"""
Adiciona legendas em inglês via YouTube API (caption tracks).
Usa traducao automatica baseada no titulo/tema de cada video.
Uso: python3.11 adicionar_legendas_en.py
"""
import json, time, io
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import googleapiclient.discovery
from googleapiclient.http import MediaIoBaseUpload

TOKEN  = Path.home() / "yt_token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload","https://www.googleapis.com/auth/youtube","https://www.googleapis.com/auth/youtube.force-ssl"]

# Legenda SRT em inglês para cada video
LEGENDAS = {
    "zw-7zezn96Y": """1
00:00:00,000 --> 00:00:05,000
Bitcoin Magnate

2
00:00:05,000 --> 00:00:12,000
Original music from Radio Bitcoin
Brazil's first 100% Bitcoin radio

3
00:00:12,000 --> 00:00:20,000
Bitcoin is not just money
It's sovereignty and freedom

4
00:00:20,000 --> 00:00:30,000
Those who understood early
became the new magnates

5
00:00:30,000 --> 00:00:40,000
Your keys, your Bitcoin
Your life, your rules
""",
    "lZ5UQYfCL-Q": """1
00:00:00,000 --> 00:00:05,000
Mission Bitcoin — Episode 1

2
00:00:05,000 --> 00:00:15,000
Every revolution has a beginning
This is ours

3
00:00:15,000 --> 00:00:25,000
Bitcoin: the peaceful revolution
of digital sovereignty

4
00:00:25,000 --> 00:00:35,000
The mission has started
Will you join us?

5
00:00:35,000 --> 00:00:45,000
Radio Bitcoin — radiobitcoin.org
""",
    "AQVk58FxS_Y": """1
00:00:00,000 --> 00:00:05,000
Mission Bitcoin — Episode 2

2
00:00:05,000 --> 00:00:15,000
The path of self-custody
begins with knowledge

3
00:00:15,000 --> 00:00:25,000
Not your keys, not your coins
Learn to protect yourself

4
00:00:25,000 --> 00:00:35,000
The mission continues
Bitcoin is freedom

5
00:00:35,000 --> 00:00:45,000
Radio Bitcoin — radiobitcoin.org
""",
    "WHmJ_pwDeBo": """1
00:00:00,000 --> 00:00:05,000
Mission Bitcoin — Porto, Portugal

2
00:00:05,000 --> 00:00:15,000
Bitcoin has no borders
From Brazil to Portugal

3
00:00:15,000 --> 00:00:25,000
The orange revolution
crosses the Atlantic

4
00:00:25,000 --> 00:00:35,000
Porto, Lisbon, São Paulo
One mission, one sound

5
00:00:35,000 --> 00:00:45,000
Radio Bitcoin — radiobitcoin.org
""",
    "fHS0VKpaOek": """1
00:00:00,000 --> 00:00:05,000
Indestructible Self-Custody

2
00:00:05,000 --> 00:00:15,000
Your Bitcoin, your responsibility
No bank, no government

3
00:00:15,000 --> 00:00:25,000
Hardware wallet, seed phrase
Your sovereignty is in your hands

4
00:00:25,000 --> 00:00:35,000
Indestructible: resistant to
governments, exchanges and time

5
00:00:35,000 --> 00:00:45,000
Learn at bitadict.com
""",
    "0G2nxVfJ8Lo": """1
00:00:00,000 --> 00:00:05,000
Heavy Chains

2
00:00:05,000 --> 00:00:15,000
The fiat system is an invisible chain
You just don't feel it yet

3
00:00:15,000 --> 00:00:25,000
Inflation, taxes, control
Break free with Bitcoin

4
00:00:25,000 --> 00:00:35,000
The chain is heavy
Bitcoin is the key

5
00:00:35,000 --> 00:00:45,000
Radio Bitcoin — radiobitcoin.org
""",
    "MCL84gEV0Bg": """1
00:00:00,000 --> 00:00:05,000
Freedom at Risk

2
00:00:05,000 --> 00:00:15,000
When freedom is under threat
Bitcoin is resistance

3
00:00:15,000 --> 00:00:25,000
Censorship-resistant, borderless
Decentralized and unstoppable

4
00:00:25,000 --> 00:00:35,000
Your freedom is worth protecting
Start with Bitcoin

5
00:00:35,000 --> 00:00:45,000
Radio Bitcoin — radiobitcoin.org
""",
    "dWqCeOU9q7k": """1
00:00:00,000 --> 00:00:05,000
Salvation is Individual

2
00:00:05,000 --> 00:00:15,000
Nobody will save you
Sovereignty is a personal choice

3
00:00:15,000 --> 00:00:25,000
Financial freedom starts
with a single decision

4
00:00:25,000 --> 00:00:35,000
Bitcoin: your personal
path to sovereignty

5
00:00:35,000 --> 00:00:45,000
Radio Bitcoin — radiobitcoin.org
""",
    "m48cJ9Dv5KA": """1
00:00:00,000 --> 00:00:05,000
Bitcoin 2026

2
00:00:05,000 --> 00:00:15,000
The year everything changes
Are you ready?

3
00:00:15,000 --> 00:00:25,000
Bitcoin rewrites the rules
of money and freedom

4
00:00:25,000 --> 00:00:35,000
2026: the orange revolution
reaches its peak

5
00:00:35,000 --> 00:00:45,000
Radio Bitcoin — radiobitcoin.org
""",
    "DgTc5L_iQ6o": """1
00:00:00,000 --> 00:00:05,000
Dance the Night Away

2
00:00:05,000 --> 00:00:15,000
When Bitcoin plays
the night belongs to you

3
00:00:15,000 --> 00:00:25,000
Freedom sounds like music
Bitcoin feels like liberation

4
00:00:25,000 --> 00:00:35,000
Radio Bitcoin original music
Dance. Be free. Stack sats.

5
00:00:35,000 --> 00:00:45,000
Radio Bitcoin — radiobitcoin.org
""",
}


def get_youtube():
    creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN.write_text(creds.to_json())
    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)


def adicionar_legenda(yt, video_id, srt_text):
    try:
        media = MediaIoBaseUpload(
            io.BytesIO(srt_text.encode("utf-8")),
            mimetype="text/plain",
            resumable=False
        )
        r = yt.captions().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "language": "en",
                    "name": "English",
                    "isDraft": False,
                }
            },
            media_body=media
        ).execute()
        print(f"  ✓ legenda EN adicionada ({r['id']})")
    except Exception as e:
        if "duplicate" in str(e).lower() or "alreadyExists" in str(e):
            print(f"  já existe legenda EN")
        else:
            print(f"  ERRO: {e}")


def main():
    yt = get_youtube()
    print(f"Adicionando legendas EN em {len(LEGENDAS)} vídeos prioritários...\n")
    for vid_id, srt in LEGENDAS.items():
        print(f"→ {vid_id}")
        adicionar_legenda(yt, vid_id, srt)
        time.sleep(2)
    print("\n✅ Legendas concluídas!")


if __name__ == "__main__":
    main()
