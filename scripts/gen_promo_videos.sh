#!/usr/bin/env bash
# Gera 4 vídeos promo 9:16 1080x1920 · 15 segundos · pra IG Reels / TikTok / YouTube Shorts.
# Cada vídeo tem 3 cenas (HOOK · BENEFÍCIO · CTA) com música ambiente da rádio.
set -e

cd "$(dirname "$0")/.."
OUT="downloads/promo_videos"
mkdir -p "$OUT"

FONT_BOLD="/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG="/Library/Fonts/Arial Unicode.ttf"
BG="0x07090d"
BTC="0xf2a900"
WHITE="0xffffff"
DIM="0x9ca3af"

# Música ambiente — uma faixa instrumental seria ideal, mas usamos uma da rádio.
MUSIC="Autocustódia Inoxidável.mp3"
if [ ! -f "$MUSIC" ]; then
  echo "ERRO: $MUSIC não existe" >&2
  exit 1
fi

# Gera 1 vídeo
gen() {
  local name="$1" tag="$2" hook="$3" benefit="$4" cta="$5" price="$6"

  ffmpeg -y \
    -f lavfi -i "color=c=${BG}:s=1080x1920:d=15" \
    -ss 20 -t 15 -i "$MUSIC" \
    -filter_complex "
      [0:v]
        drawbox=x=0:y=0:w=1080:h=12:color=${BTC}:t=fill,
        drawbox=x=0:y=1908:w=1080:h=12:color=${BTC}:t=fill,
        drawtext=fontfile='${FONT_REG}':text='RADIOBITCOIN.ORG':fontsize=28:fontcolor=${DIM}:x=(w-text_w)/2:y=80:expansion=none,
        drawtext=fontfile='${FONT_REG}':text='${tag}':fontsize=34:fontcolor=${BTC}:x=(w-text_w)/2:y=150:expansion=none,
        drawtext=fontfile='${FONT_BOLD}':text='${hook}':fontsize=110:fontcolor=${WHITE}:x=(w-text_w)/2:y=700:expansion=none:enable='between(t,0,5)',
        drawtext=fontfile='${FONT_BOLD}':text='${benefit}':fontsize=72:fontcolor=${WHITE}:x=(w-text_w)/2:y=720:expansion=none:enable='between(t,5,11)',
        drawtext=fontfile='${FONT_BOLD}':text='${cta}':fontsize=84:fontcolor=${WHITE}:x=(w-text_w)/2:y=720:expansion=none:enable='between(t,11,15)',
        drawtext=fontfile='${FONT_BOLD}':text='${price}':fontsize=80:fontcolor=${BTC}:x=(w-text_w)/2:y=920:expansion=none:enable='between(t,11,15)',
        drawtext=fontfile='${FONT_REG}':text='BIT ADICT':fontsize=44:fontcolor=${BTC}:x=(w-text_w)/2:y=1780:expansion=none,
        drawtext=fontfile='${FONT_REG}':text='radiobitcoin.org':fontsize=32:fontcolor=${DIM}:x=(w-text_w)/2:y=1830:expansion=none
      [v]
    " \
    -map "[v]" -map 1:a \
    -c:v libx264 -preset slow -crf 22 -pix_fmt yuv420p \
    -c:a aac -b:a 128k -af "afade=t=in:st=0:d=0.5,afade=t=out:st=14.5:d=0.5,volume=0.6" \
    -shortest -t 15 \
    "${OUT}/${name}.mp4" 2>&1 | tail -2
  echo "✓ ${OUT}/${name}.mp4"
}

# 1. EBOOK
gen "promo_ebook" \
    "EBOOK GRATIS" \
    "10 ERROS" \
    "Que fazem voce perder Bitcoin" \
    "BAIXA GRATIS" \
    "PDF 28 PG"

# 2. VIP
gen "promo_vip" \
    "ACESSO RESTRITO" \
    "VIP" \
    "Sinais dos 3 bots em tempo real" \
    "ENTRA AGORA" \
    "EUR 19 / USD 19"

# 3. MENTORIA
gen "promo_mentoria" \
    "1 PARA 1" \
    "MENTORIA" \
    "Setup completo bots em 4 horas" \
    "AGENDA HOJE" \
    "EUR 497 / USD 497"

# 4. CURSO
gen "promo_curso" \
    "PRE-VENDA" \
    "CURSO" \
    "8 modulos · soberania digital" \
    "GARANTE TEU" \
    "EUR 297 / USD 297"

echo ""
echo "Vídeos gerados em: ${OUT}/"
ls -la "${OUT}/"
