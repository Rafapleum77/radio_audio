#!/usr/bin/env python3
"""
Sobe mp4s de ~/radio_audio/clipes/ pro YouTube.

Uso:
    python3.11 subir_clipes_yt.py              # todos pendentes
    python3.11 subir_clipes_yt.py <arquivo>    # ex: Bitcoin_Magnata.mp4
"""
import sys, json, time
from pathlib import Path

CLIPES = Path(__file__).parent / "clipes"
STATE_FILE = Path(__file__).parent / "uploaded_clipes.json"
YT_TOKEN = Path("~/yt_token.json").expanduser()
YT_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]
HASHTAGS = "#Bitcoin #Crypto #BTC #Lightning #RadioBitcoin #BitAdict #SoberaniaBitcoin"

DESCRICAO_BASE = """\
🎵 Música original da Rádio Bitcoin — a primeira rádio Bitcoin do Brasil.

Soberania digital, autocustódia e liberdade financeira em formato de música.

📻 Ouça ao vivo: https://radiobitcoin.org
🤖 Bots e automações: https://bitadict.com

{hashtags}"""


def nome_para_titulo(nome: str) -> str:
    return nome.replace("_", " ").replace("-", " ").strip()


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(s):
    STATE_FILE.write_text(json.dumps(s, indent=2, ensure_ascii=False))


def get_youtube():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    import googleapiclient.discovery

    creds = Credentials.from_authorized_user_file(str(YT_TOKEN), YT_SCOPES)
    if not creds.valid and creds.expired and creds.refresh_token:
        print("  refrescando token YouTube...")
        creds.refresh(Request())
        YT_TOKEN.write_text(creds.to_json())
    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)


def upload(yt, mp4: Path) -> str:
    from googleapiclient.http import MediaFileUpload

    titulo = nome_para_titulo(mp4.stem)[:100]
    descricao = DESCRICAO_BASE.format(hashtags=HASHTAGS)

    body = {
        "snippet": {
            "title": titulo,
            "description": descricao,
            "tags": [t.lstrip("#") for t in HASHTAGS.split()],
            "categoryId": "10",  # Music
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(mp4), mimetype="video/mp4", resumable=True, chunksize=4 * 1024 * 1024)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            print(f"    {int(status.progress() * 100)}%", end="\r")

    vid_id = response["id"]
    print(f"  ✓ https://youtu.be/{vid_id}")
    return vid_id


def main():
    state = load_state()
    yt = get_youtube()

    if len(sys.argv) > 1:
        alvo = Path(sys.argv[1])
        if not alvo.is_absolute():
            alvo = CLIPES / sys.argv[1]
        arquivos = [alvo]
    else:
        arquivos = sorted(CLIPES.glob("*.mp4"))
        arquivos = [f for f in arquivos if f.name not in state]
        print(f"{len(arquivos)} vídeo(s) pendentes")

    for mp4 in arquivos:
        if mp4.name in state:
            print(f"PULADO {mp4.name} (já subido)")
            continue
        print(f"\n→ {mp4.name}")
        try:
            vid_id = upload(yt, mp4)
            state[mp4.name] = vid_id
            save_state(state)
            time.sleep(5)  # pausa entre uploads
        except Exception as e:
            print(f"  ERRO: {e}")

    print("\nConcluído.")


if __name__ == "__main__":
    main()
