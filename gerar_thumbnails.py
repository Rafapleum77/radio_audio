#!/usr/bin/env python3
"""
Gera thumbnails profissionais para cada video:
1. Imagem de fundo via Pollinations.ai (cinematic AI)
2. Overlay bold com titulo + branding Rádio Bitcoin
3. Faz upload via YouTube API

Uso:
    python3.11 gerar_thumbnails.py           # todos
    python3.11 gerar_thumbnails.py <video_id> # 1 especifico
"""
import sys, json, time, textwrap, urllib.request, urllib.parse, io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import googleapiclient.discovery
from googleapiclient.http import MediaIoBaseUpload

TOKEN  = Path.home() / "yt_token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload","https://www.googleapis.com/auth/youtube"]
OUT    = Path(__file__).parent / "thumbnails"
OUT.mkdir(exist_ok=True)

# ── Dados de cada vídeo ──────────────────────────────────────────────────────
VIDEOS = {
    "zw-7zezn96Y": {"titulo": "BITCOIN\nMAGNATA", "prompt": "golden bitcoin coins rain cinematic dark luxury wealth", "tema": "gold"},
    "m48cJ9Dv5KA": {"titulo": "BITCOIN\n2026", "prompt": "futuristic city bitcoin orange neon 2026 cinematic skyline", "tema": "neon"},
    "6JJwYFO1xSg": {"titulo": "BITCOIN\nNO ESPAÇO", "prompt": "rocket launch spacex night bitcoin orange glow cinematic", "tema": "space"},
    "dWqCeOU9q7k": {"titulo": "A SALVAÇÃO\nÉ INDIVIDUAL", "prompt": "lone figure mountain top sunrise epic cinematic liberation", "tema": "dawn"},
    "fHS0VKpaOek": {"titulo": "AUTOCUSTÓDIA\nINOXIDÁVEL", "prompt": "steel vault bitcoin cold wallet security dark cinematic", "tema": "steel"},
    "6595xiZnXa0": {"titulo": "AUTOCUSTÓDIA\nBITCOIN", "prompt": "hardware wallet bitcoin key glowing dark background cinematic", "tema": "steel"},
    "4xI0gWCekUs": {"titulo": "BITCOIN\nINOXIDÁVEL", "prompt": "indestructible bitcoin steel fire resistance epic cinematic", "tema": "fire"},
    "1pbsUAOyE2g": {"titulo": "BITCOIN\nSALVAÇÃO", "prompt": "light rays hands reaching bitcoin orange glow cinematic spiritual", "tema": "light"},
    "NsAIWZfgUT0": {"titulo": "BITCOIN E\nSALVAÇÃO", "prompt": "cross and bitcoin symbol divine light cinematic dramatic", "tema": "light"},
    "bhmGcIC0qGA": {"titulo": "BITCOIN\nROCK", "prompt": "electric guitar bitcoin symbol rock concert dark stage cinematic", "tema": "rock"},
    "qs72f2KUlho": {"titulo": "BITCOIN E\nSALVAÇÃO", "prompt": "golden light bitcoin freedom liberation epic cinematic sky", "tema": "gold"},
    "0G2nxVfJ8Lo": {"titulo": "CORRENTES\nPESADAS", "prompt": "breaking chains bitcoin freedom dark dramatic cinematic", "tema": "dark"},
    "c5SPNBaJo54": {"titulo": "CRIPTOGRAFIA\nBITCOIN", "prompt": "binary code encryption bitcoin lock security dark cinematic blue", "tema": "cyber"},
    "DgTc5L_iQ6o": {"titulo": "DANCE THE\nNIGHT AWAY", "prompt": "neon dance floor bitcoin party night club cinematic purple", "tema": "neon"},
    "8OBCHCyBF8E": {"titulo": "DIGITAL SOUL\nIN THE DELTA", "prompt": "blues musician delta river bitcoin digital soul cinematic moody", "tema": "moody"},
    "MCL84gEV0Bg": {"titulo": "LIBERDADE\nEM RISCO", "prompt": "broken chains freedom risk alert bitcoin dramatic cinematic red", "tema": "warning"},
    "lZ5UQYfCL-Q": {"titulo": "MISSÃO\nBITCOIN EP.1", "prompt": "space mission launch bitcoin rocket fire epic cinematic", "tema": "space"},
    "AQVk58FxS_Y": {"titulo": "MISSÃO\nBITCOIN EP.2", "prompt": "astronaut bitcoin flag moon surface cinematic epic", "tema": "space"},
    "WHmJ_pwDeBo": {"titulo": "MISSÃO\nBITCOIN PORTO", "prompt": "portugal porto bridge sunset bitcoin orange cinematic beautiful", "tema": "gold"},
    "o-5Hm-tGlQ0": {"titulo": "MISSÃO\nBITCOIN", "prompt": "bitcoin mission short sharp cinematic dramatic dark orange", "tema": "dark"},
    "wu-heN7DWjU": {"titulo": "MISSÃO\nBITCOIN v2", "prompt": "ultimate bitcoin mission space earth cinematic dramatic final", "tema": "space"},
}

TEMAS = {
    "gold":    {"accent": (247,147,26),  "bg": (10,8,2)},
    "neon":    {"accent": (0,212,255),   "bg": (5,0,15)},
    "space":   {"accent": (247,147,26),  "bg": (2,2,12)},
    "dawn":    {"accent": (255,180,50),  "bg": (8,4,2)},
    "steel":   {"accent": (200,220,255), "bg": (5,8,12)},
    "fire":    {"accent": (255,80,20),   "bg": (12,3,0)},
    "light":   {"accent": (255,220,100), "bg": (5,5,10)},
    "rock":    {"accent": (220,50,255),  "bg": (5,0,10)},
    "dark":    {"accent": (247,147,26),  "bg": (5,5,5)},
    "cyber":   {"accent": (0,255,180),   "bg": (0,5,12)},
    "moody":   {"accent": (150,100,50),  "bg": (5,3,2)},
    "warning": {"accent": (255,50,50),   "bg": (12,2,2)},
}

W, H = 1280, 720


def buscar_imagem_pollinations(prompt: str) -> Image.Image | None:
    prompt_enc = urllib.parse.quote(f"{prompt}, 16:9 widescreen, ultra HD, dark moody cinematic")
    url = f"https://image.pollinations.ai/prompt/{prompt_enc}?width=1280&height=720&nologo=true&seed=42"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return Image.open(io.BytesIO(r.read())).convert("RGB")
    except Exception as e:
        print(f"    Pollinations falhou: {e}")
        return None


def montar_thumbnail(img_bg: Image.Image | None, titulo: str, tema: str) -> Image.Image:
    cores = TEMAS.get(tema, TEMAS["gold"])
    accent = cores["accent"]
    bg_cor = cores["bg"]

    # base
    canvas = Image.new("RGB", (W, H), bg_cor)

    if img_bg:
        img_bg = img_bg.resize((W, H), Image.LANCZOS)
        img_bg = ImageEnhance.Brightness(img_bg).enhance(0.45)
        img_bg = ImageEnhance.Contrast(img_bg).enhance(1.2)
        canvas.paste(img_bg, (0, 0))

    # gradiente lateral escuro (lado esquerdo para texto)
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_grad = ImageDraw.Draw(grad)
    for x in range(700):
        alpha = int(220 * (1 - x / 700))
        draw_grad.line([(x, 0), (x, H)], fill=(bg_cor[0], bg_cor[1], bg_cor[2], alpha))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), grad).convert("RGB")

    draw = ImageDraw.Draw(canvas)

    # barra accent lateral
    draw.rectangle([(0, 0), (8, H)], fill=accent)

    # tenta carregar fonte bold
    font_titulo = None
    font_sub    = None
    font_marca  = None
    for fname in ["/System/Library/Fonts/Supplemental/Impact.ttf",
                  "/System/Library/Fonts/Helvetica.ttc",
                  "/Library/Fonts/Arial Bold.ttf"]:
        try:
            font_titulo = ImageFont.truetype(fname, 110)
            font_sub    = ImageFont.truetype(fname, 36)
            font_marca  = ImageFont.truetype(fname, 28)
            break
        except:
            pass
    if not font_titulo:
        font_titulo = ImageFont.load_default()
        font_sub    = font_titulo
        font_marca  = font_titulo

    linhas = titulo.split("\n")
    y = 120
    for linha in linhas:
        # sombra
        draw.text((54, y+4), linha, font=font_titulo, fill=(0,0,0,180))
        # texto principal
        draw.text((50, y), linha, font=font_titulo, fill=(255,255,255))
        bbox = draw.textbbox((0,0), linha, font=font_titulo)
        y += (bbox[3] - bbox[1]) + 16

    # linha accent abaixo do titulo
    draw.rectangle([(50, y+10), (50 + min(500, W-100), y+14)], fill=accent)

    # subtítulo
    draw.text((52, y+30), "RÁDIO BITCOIN • bitadict.com", font=font_sub, fill=accent)

    # logo canto inferior direito
    draw.text((W-320, H-50), "📻 radiobitcoin.org", font=font_marca, fill=(200,200,200))

    # borda accent inferior
    draw.rectangle([(0, H-6), (W, H)], fill=accent)

    return canvas


def get_youtube():
    creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN.write_text(creds.to_json())
    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)


def upload_thumbnail(yt, video_id: str, img_path: Path):
    with open(img_path, "rb") as f:
        media = MediaIoBaseUpload(f, mimetype="image/jpeg", resumable=False)
        yt.thumbnails().set(videoId=video_id, media_body=media).execute()


def processar(video_id: str, yt):
    dados = VIDEOS[video_id]
    thumb_path = OUT / f"{video_id}.jpg"

    print(f"\n→ {video_id} | {dados['titulo'].replace(chr(10),' ')}")

    if not thumb_path.exists():
        print("    buscando imagem Pollinations...")
        img_bg = buscar_imagem_pollinations(dados["prompt"])
        print("    montando thumbnail...")
        thumb = montar_thumbnail(img_bg, dados["titulo"], dados["tema"])
        thumb.save(str(thumb_path), "JPEG", quality=92)
        print(f"    salvo: {thumb_path.name} ({thumb_path.stat().st_size//1024}KB)")
    else:
        print(f"    usando cache: {thumb_path.name}")

    print("    fazendo upload...")
    try:
        upload_thumbnail(yt, video_id, thumb_path)
        print("    ✓ thumbnail aplicada!")
    except Exception as e:
        print(f"    ERRO upload: {e}")

    time.sleep(3)


def main():
    yt = get_youtube()
    alvo = sys.argv[1] if len(sys.argv) > 1 else None

    if alvo:
        if alvo not in VIDEOS:
            print(f"ID não encontrado: {alvo}")
            sys.exit(1)
        processar(alvo, yt)
    else:
        print(f"Gerando thumbnails para {len(VIDEOS)} vídeos...")
        for vid_id in VIDEOS:
            processar(vid_id, yt)

    print("\n✅ Concluído!")


if __name__ == "__main__":
    main()
