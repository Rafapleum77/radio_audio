#!/bin/bash
# Gera clipes em lote para músicas autorais Bitcoin
# Uso: ./gerar_lote.sh
set -e
RADIO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$RADIO_DIR"

FONT="/System/Library/Fonts/Helvetica.ttc"
[ ! -f "$FONT" ] && FONT="/System/Library/Fonts/Arial.ttf"
mkdir -p clipes

gerar() {
  local TITLE="$1"
  local AUDIO="$2"
  local IMAGE="$3"
  local OUTPUT="clipes/$(echo "$TITLE" | tr ' ' '_' | tr -d '/()' | head -c 50).mp4"

  if [ -f "$OUTPUT" ]; then
    echo "⏭  Já existe: $OUTPUT"
    return 0
  fi
  if [ ! -f "$AUDIO" ]; then
    echo "⚠  Áudio não encontrado: $AUDIO"
    return 0
  fi

  echo "🎬 Gerando: $TITLE"
  ffmpeg -y \
    -loop 1 -i "$IMAGE" \
    -i "$AUDIO" \
    -t 60 \
    -vf "
      scale=1080:1920:force_original_aspect_ratio=increase,
      crop=1080:1920,
      drawbox=x=0:y=1550:w=1080:h=370:color=black@0.80:t=fill,
      drawtext=fontfile='$FONT':text='📻 Rádio Bitcoin':fontcolor=00ff41:fontsize=42:x=(w-text_w)/2:y=1580:shadowcolor=black:shadowx=2:shadowy=2,
      drawtext=fontfile='$FONT':text='$TITLE':fontcolor=white:fontsize=52:x=(w-text_w)/2:y=1650:shadowcolor=black:shadowx=2:shadowy=2,
      drawtext=fontfile='$FONT':text='radiobitcoin.org':fontcolor=f7c948:fontsize=36:x=(w-text_w)/2:y=1740:shadowcolor=black:shadowx=2:shadowy=2,
      drawtext=fontfile='$FONT':text='⚡ texugorecords@walletofsatoshi.com':fontcolor=aaaaaa:fontsize=28:x=(w-text_w)/2:y=1800
    " \
    -c:v libx264 -preset fast -crf 23 \
    -c:a aac -b:a 192k \
    -pix_fmt yuv420p \
    -movflags +faststart \
    "$OUTPUT" 2>/dev/null

  if [ -f "$OUTPUT" ]; then
    echo "✅ $OUTPUT ($(du -sh "$OUTPUT" | cut -f1))"
  else
    echo "❌ Falhou: $TITLE"
  fi
}

SUNO="$HOME/Bots/suno/downloads"
CAMP="img/bitadict/campanha"
OG="img/og"

gerar "Bitcoin e Salvação"        "Bitcoin e Salvação.mp3"             "$SUNO/Bitcoin_e_Salvacao_38831d37.jpg"
gerar "Bitcoin Salvação"          "Bitcoin Salvação.mp3"               "$SUNO/Bitcoin_Salvacao_87ec83c6.jpg"
gerar "Missao Bitcoin Porto"      "Missao Bitcoin Porto.mp3"           "$SUNO/Missao_Bitcoin_a18d39a3.jpg"
gerar "Autocustódia Inoxidável"   "Autocustódia Inoxidável.mp3"        "$CAMP/01_hero_recovery_kit.webp"
gerar "Autocustódia"              "Autocustódia.mp3"                   "$CAMP/01_hero_recovery_kit.webp"
gerar "Correntes Pesadas"         "Correntes Pesadas.mp3"              "$OG/og_home.jpg"
gerar "Dance the Night Away"      "Dance the Night Away.mp3"           "$OG/og_home.jpg"
gerar "Digital Soul in the Delta" "Digital Soul in the Delta.mp3"      "$OG/og_home.jpg"
gerar "Liberdade em Risco"        "Liberdade em Risco.mp3"             "$OG/og_home.jpg"
gerar "Bitcoin Magnata"           "Bitcoin Magnata.mp3"                "$OG/og_home.jpg"
gerar "A Salvação é Individual"   "A salvação eh individual .mp3"      "$CAMP/03_familia_protegida.webp"
gerar "2026"                      "2026.mp3"                           "$OG/og_home.jpg"

echo ""
echo "🏁 Lote concluído. Clipes em: $RADIO_DIR/clipes/"
ls -lh clipes/*.mp4 2>/dev/null | awk '{print $5, $9}'
