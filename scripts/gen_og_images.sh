#!/usr/bin/env bash
# Gera 4 OG images (1200x630) pra link previews do Facebook/Twitter/WhatsApp/LinkedIn.
set -e

cd "$(dirname "$0")/.."
OUT="img/og"
mkdir -p "$OUT"

FONT_BOLD="/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG="/Library/Fonts/Arial Unicode.ttf"
BG="0x07090d"
BTC="0xf2a900"
WHITE="0xffffff"
DIM="0x9ca3af"

gen() {
  local name="$1" tag="$2" title="$3" sub="$4" price="$5"

  ffmpeg -y -f lavfi -i "color=c=${BG}:s=1200x630:d=1" \
    -vf "
      drawbox=x=0:y=0:w=1200:h=8:color=${BTC}:t=fill,
      drawbox=x=0:y=622:w=1200:h=8:color=${BTC}:t=fill,
      drawtext=fontfile='${FONT_REG}':text='${tag}':fontsize=18:fontcolor=${BTC}:x=(w-text_w)/2:y=80:expansion=none,
      drawtext=fontfile='${FONT_BOLD}':text='${title}':fontsize=84:fontcolor=${WHITE}:x=(w-text_w)/2:y=180:expansion=none,
      drawtext=fontfile='${FONT_REG}':text='${sub}':fontsize=28:fontcolor=${DIM}:x=(w-text_w)/2:y=330:expansion=none,
      drawtext=fontfile='${FONT_BOLD}':text='${price}':fontsize=70:fontcolor=${BTC}:x=(w-text_w)/2:y=430:expansion=none,
      drawtext=fontfile='${FONT_REG}':text='radiobitcoin.org':fontsize=22:fontcolor=${DIM}:x=(w-text_w)/2:y=560:expansion=none
    " \
    -frames:v 1 "${OUT}/${name}.png" 2>&1 | tail -3
  echo "✓ ${OUT}/${name}.png"
}

# VIP — sinais tempo real
gen "og_vip" \
    "ASSINATURA MENSAL · BIT ADICT" \
    "VIP" \
    "Sinais dos 3 bots em tempo real · WhatsApp privado" \
    "EUR 19 / USD 19 mes"

# MENTORIA
gen "og_mentoria" \
    "ATENDIMENTO 1 PARA 1 · BIT ADICT" \
    "MENTORIA" \
    "Setup completo dos bots + opsec + self-custody" \
    "EUR 150 / USD 150 h"

# EBOOK
gen "og_ebook" \
    "DOWNLOAD GRATUITO · BIT ADICT" \
    "10 ERROS" \
    "Os 10 erros de quem perde Bitcoin (e como evitar)" \
    "PDF GRATIS"

# CURSO
gen "og_curso" \
    "PRE-VENDA · BIT ADICT" \
    "CURSO" \
    "8 modulos · 30+ aulas · acesso vitalicio" \
    "EUR 297 / USD 297"

# Converte pra WebP (mais leve)
if command -v cwebp >/dev/null 2>&1; then
  for f in "${OUT}"/og_*.png; do
    cwebp -q 88 "$f" -o "${f%.png}.webp" >/dev/null 2>&1
    echo "✓ ${f%.png}.webp"
  done
fi

echo ""
echo "OG images geradas em: ${OUT}/"
ls -la "${OUT}/"
