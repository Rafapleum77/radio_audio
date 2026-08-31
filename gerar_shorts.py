#!/usr/bin/env python3
"""
Converte clipes horizontais (1280x720) em verticais (1080x1920) para Shorts/Reels/TikTok.
Adiciona texto do titulo no topo e branding no rodape.
Uso: python3.11 gerar_shorts.py
"""
import subprocess, json, time
from pathlib import Path
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload

TOKEN   = Path.home() / "yt_token.json"
SCOPES  = ["https://www.googleapis.com/auth/youtube.upload","https://www.googleapis.com/auth/youtube"]
CLIPES  = Path.home() / "radio_audio/clipes"
OUT     = Path.home() / "radio_audio/shorts"
UPLOADED = Path.home() / "radio_audio/uploaded_shorts.json"
OUT.mkdir(exist_ok=True)

SHORTS = {
    "Missao_Bitcoin_SHORT.mp4":     {"titulo": "MISSÃO BITCOIN", "hashtags": "#MissãoBitcoin #Bitcoin #Shorts"},
    "Criptografia_Honre_SHORT.mp4": {"titulo": "CRIPTOGRAFIA BITCOIN", "hashtags": "#Bitcoin #Criptografia #Shorts"},
    "Bitcoin_Magnata.mp4":          {"titulo": "BITCOIN MAGNATA", "hashtags": "#Bitcoin #Magnata #Shorts"},
    "Autocustódia_Inoxidável.mp4":  {"titulo": "AUTOCUSTÓDIA", "hashtags": "#Autocustódia #Bitcoin #Shorts"},
    "Correntes_Pesadas.mp4":        {"titulo": "CORRENTES PESADAS", "hashtags": "#Bitcoin #Liberdade #Shorts"},
    "Liberdade_em_Risco.mp4":       {"titulo": "LIBERDADE EM RISCO", "hashtags": "#Bitcoin #Liberdade #Shorts"},
    "A_Salvação_é_Individual.mp4":  {"titulo": "A SALVAÇÃO", "hashtags": "#Bitcoin #Soberania #Shorts"},
    "Bitcoin_e_Salvacao.mp4":       {"titulo": "BITCOIN E SALVAÇÃO", "hashtags": "#Bitcoin #BTC #Shorts"},
    "Missao_Bitcoin_v2.mp4":        {"titulo": "MISSÃO BITCOIN v2", "hashtags": "#Bitcoin #Missão #Shorts"},
    "Digital_Soul_in_the_Delta.mp4":{"titulo": "DIGITAL SOUL", "hashtags": "#Bitcoin #Blues #Shorts"},
}

def converter_short(src: Path, titulo: str, out: Path) -> bool:
    # crop central + resize pra 1080x1920 + texto
    filtro = (
        "crop=ih*9/16:ih,"         # crop central 9:16
        "scale=1080:1920,"
        "drawtext=text='RÁDIO BITCOIN':fontsize=52:fontcolor=#F7931A:"
        "x=(w-text_w)/2:y=80:shadowcolor=black:shadowx=2:shadowy=2,"
        f"drawtext=text='{titulo}':fontsize=72:fontcolor=white:"
        "x=(w-text_w)/2:y=160:shadowcolor=black:shadowx=3:shadowy=3,"
        "drawtext=text='radiobitcoin.org':fontsize=38:fontcolor=white:"
        "x=(w-text_w)/2:y=h-100:shadowcolor=black:shadowx=2:shadowy=2"
    )
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-vf", filtro,
        "-c:v", "h264_videotoolbox", "-b:v", "3500k",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-r", "30", "-t", "59",
        str(out)
    ]
    r = subprocess.run(cmd, capture_output=True)
    return r.returncode == 0

def get_youtube():
    creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN.write_text(creds.to_json())
    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)

def upload_short(yt, mp4: Path, titulo: str, hashtags: str) -> str:
    from googleapiclient.http import MediaFileUpload
    body = {
        "snippet": {
            "title": f"{titulo} 🎵 #Shorts — Rádio Bitcoin",
            "description": f"{titulo}\n\n🎵 Música original da Rádio Bitcoin — a primeira rádio 100% Bitcoin do Brasil.\n\n📻 https://radiobitcoin.org\n🔐 https://bitadict.com\n\n{hashtags} #RadioBitcoin #BitAdict #CriptoBrasil",
            "tags": ["bitcoin","shorts","cripto brasil","radio bitcoin","música bitcoin"],
            "categoryId": "10",
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(str(mp4), mimetype="video/mp4", resumable=True, chunksize=4*1024*1024)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _, response = req.next_chunk()
    return response["id"]

def main():
    state = json.loads(UPLOADED.read_text()) if UPLOADED.exists() else {}
    yt = get_youtube()
    print(f"Gerando {len(SHORTS)} Shorts...\n")
    pub = pul = falt = err = 0

    for nome, dados in SHORTS.items():
        if nome in state:
            print(f"PULADO {nome} (já subido)")
            pul += 1
            continue
        src = CLIPES / nome
        if not src.exists():
            print(f"FALTANDO {nome}")
            falt += 1
            continue

        out = OUT / nome
        print(f"→ {nome}")

        if not out.exists():
            print("  convertendo para vertical...")
            if not converter_short(src, dados["titulo"], out):
                print("  ERRO ffmpeg")
                err += 1
                continue

        print("  subindo para YouTube Shorts...")
        try:
            vid_id = upload_short(yt, out, dados["titulo"], dados["hashtags"])
            state[nome] = vid_id
            UPLOADED.write_text(json.dumps(state, indent=2))
            print(f"  ✓ https://youtu.be/{vid_id}")
            pub += 1
        except Exception as e:
            print(f"  ERRO upload: {e}")
            err += 1

        time.sleep(5)

    # Antes daqui saia sempre "Shorts concluidos!", mesmo quando a esteira
    # publicava ZERO -- e ela vinha publicando zero havia dias, porque todos os
    # itens de SHORTS ja estavam no uploaded_shorts.json. Olhando o log atras de
    # erro nao se achava nada: o sinal honesto e quanto SUBIU, nao se rodou.
    print(f"\nRESULTADO: {pub} publicado(s) | {pul} ja no ar | {falt} faltando | {err} com erro")
    if pub == 0 and err == 0:
        print("NADA NOVO -- a esteira rodou sem publicar. Precisa de material novo em SHORTS.")
    elif pub == 0:
        print("NAO PUBLICOU NADA e houve erro -- ver acima.")
    else:
        print("✅ Shorts concluídos!")

    # deixa o desfecho legivel por outro processo (vigia/painel), nao so por gente
    try:
        (Path.home() / "radio_audio/estado_shorts.json").write_text(json.dumps({
            "quando": datetime.now().isoformat(timespec="seconds"),
            "publicados": pub, "ja_no_ar": pul, "faltando": falt, "erros": err,
        }, indent=2))
    except Exception as e:
        print(f"  (nao consegui gravar estado_shorts.json: {e})")

if __name__ == "__main__":
    main()
