#!/bin/bash
# Gera clipe de 60s pronto para Reels/TikTok/Shorts
# Uso: ./gerar_clipe.sh "titulo" "arquivo.mp3" "imagem.png"

TITLE="${1:-Bitcoin e Salvação}"
AUDIO="${2:-Bitcoin Salvação.mp3}"
IMAGE="${3:-ia_gemini_entry.png}"
OUTPUT="clipes/$(echo "$TITLE" | tr ' ' '_' | tr -d '/'| head -c 40).mp4"

RADIO_DIR="$(dirname "$0")"
cd "$RADIO_DIR"
mkdir -p clipes

# Cores e fonte
FONT="/System/Library/Fonts/Helvetica.ttc"
[ ! -f "$FONT" ] && FONT="/System/Library/Fonts/Arial.ttf"

echo "🎬 Gerando clipe: $TITLE"

ffmpeg -y \
  -loop 1 -i "$IMAGE" \
  -i "$AUDIO" \
  -t 60 \
  -vf "
    scale=1080:1920:force_original_aspect_ratio=increase,
    crop=1080:1920,
    drawrect=x=0:y=1550:w=1080:h=370:color=black@0.75:t=fill,
    drawtext=fontfile='$FONT':text='📻 Rádio Bitcoin':fontcolor=00ff41:fontsize=42:x=(w-text_w)/2:y=1580:shadowcolor=black:shadowx=2:shadowy=2,
    drawtext=fontfile='$FONT':text='$TITLE':fontcolor=white:fontsize=52:x=(w-text_w)/2:y=1650:shadowcolor=black:shadowx=2:shadowy=2,
    drawtext=fontfile='$FONT':text='radiobitcoin.bitadict.com':fontcolor=f7c948:fontsize=36:x=(w-text_w)/2:y=1740:shadowcolor=black:shadowx=2:shadowy=2,
    drawtext=fontfile='$FONT':text='⚡ texugorecords@walletofsatoshi.com':fontcolor=aaaaaa:fontsize=28:x=(w-text_w)/2:y=1800
  " \
  -c:v libx264 -preset fast -crf 23 \
  -c:a aac -b:a 192k \
  -pix_fmt yuv420p \
  -movflags +faststart \
  "$OUTPUT" 2>/dev/null

if [ -f "$OUTPUT" ]; then
  SIZE=$(du -sh "$OUTPUT" | cut -f1)
  echo "✅ Clipe gerado: $OUTPUT ($SIZE)"
  echo "📱 Pronto para postar no Instagram Reels / TikTok / YouTube Shorts"
else
  echo "❌ Erro ao gerar clipe"
fi
