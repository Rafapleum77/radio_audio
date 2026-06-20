#!/bin/bash
# Gera clipe "Bitcoin no Gol" com imagens IA de futebol + Ken Burns
# Requer: ffmpeg, curl, python3

set -e
RADIO_DIR="$(dirname "$0")"
cd "$RADIO_DIR"

AUDIO="Bitcoin no Gol.mp3"
OUTPUT="clipes/Bitcoin_no_Gol.mp4"
TMPDIR="clipes/tmp_btcgol"
mkdir -p "$TMPDIR" clipes

FONT="/System/Library/Fonts/Helvetica.ttc"
[ ! -f "$FONT" ] && FONT="/System/Library/Fonts/Arial.ttf"

echo "🎨 Baixando imagens IA de futebol via Pollinations..."

PROMPTS=(
  "Ronaldinho Gaucho Brazil football player dribbling skill bicycle kick stadium World Cup crowd cheering cinematic dramatic lighting golden hour"
  "Brazil vs France World Cup 2006 stadium packed crowd yellow jersey blue jersey dramatic wide shot cinematic"
  "Bitcoin cryptocurrency golden coin glowing on green football field stadium background neon lightning dramatic"
  "Brazil national football team celebrating goal World Cup trophy crowd confetti yellow gold cinematic epic"
  "Ronaldinho Gaucho iconic smile juggling football Brazil jersey skill street football cinematic dramatic lighting"
  "World Cup trophy golden FIFA Cup stadium lights confetti Brazil flag Bitcoin symbol overlay dramatic"
)

for i in "${!PROMPTS[@]}"; do
  FILE="$TMPDIR/img_$(printf '%02d' $i).jpg"
  if [ ! -f "$FILE" ]; then
    ENCODED=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "${PROMPTS[$i]}")
    echo "  📸 Imagem $((i+1))/${#PROMPTS[@]}..."
    curl -sL "https://image.pollinations.ai/prompt/${ENCODED}?width=1080&height=1920&model=flux&nologo=true&seed=$((42+i))" -o "$FILE"
    sleep 1
  fi
done

echo "🎬 Montando slideshow com Ken Burns..."

# Duração total do áudio: 152s / 6 imagens = ~25s cada
SEG=25
FILTER=""
INPUTS=""

for i in $(seq 0 5); do
  FILE="$TMPDIR/img_$(printf '%02d' $i).jpg"
  INPUTS="$INPUTS -loop 1 -t $SEG -i $FILE"
done

# Ken Burns effect em cada imagem (zoom in alternado com pan)
for i in $(seq 0 5); do
  case $((i % 3)) in
    0) ZOOM="zoompan=z='min(zoom+0.0015,1.3)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=${SEG}*25:s=1080x1920:fps=25" ;;
    1) ZOOM="zoompan=z='min(zoom+0.001,1.2)':x='if(lte(zoom,1),0,x+1)':y='ih/2-(ih/zoom/2)':d=${SEG}*25:s=1080x1920:fps=25" ;;
    2) ZOOM="zoompan=z='if(lte(zoom,1),1.2,max(1,zoom-0.001))':x='iw/2-(iw/zoom/2)':y='if(lte(zoom,1),0,y+0.5)':d=${SEG}*25:s=1080x1920:fps=25" ;;
  esac
  FILTER="${FILTER}[$i:v]${ZOOM},setsar=1[v$i];"
done

# Concatena todas as imagens
CONCAT=""
for i in $(seq 0 5); do CONCAT="${CONCAT}[v$i]"; done
FILTER="${FILTER}${CONCAT}concat=n=6:v=1:a=0[vcombined];"

# Overlay de texto (box escuro + textos)
FILTER="${FILTER}[vcombined]
  drawbox=x=0:y=1550:w=1080:h=370:color=black@0.80:t=fill,
  drawtext=fontfile='${FONT}':text='⚽ BITCOIN NO GOL':fontcolor=#F7931A:fontsize=58:x=(w-text_w)/2:y=1580:shadowcolor=black:shadowx=3:shadowy=3,
  drawtext=fontfile='${FONT}':text='RÁDIO BITCOIN':fontcolor=white:fontsize=44:x=(w-text_w)/2:y=1660:shadowcolor=black:shadowx=2:shadowy=2,
  drawtext=fontfile='${FONT}':text='radiobitcoin.org':fontcolor=#f7c948:fontsize=34:x=(w-text_w)/2:y=1740:shadowcolor=black:shadowx=2:shadowy=2,
  drawtext=fontfile='${FONT}':text='⚡ Bitcoin é o gol que salva':fontcolor=aaaaaa:fontsize=28:x=(w-text_w)/2:y=1800
[vout]"

echo "⚙️  Codificando vídeo final (pode levar 2-3 min)..."

ffmpeg -y $INPUTS -i "$AUDIO" \
  -filter_complex "$FILTER" \
  -map "[vout]" -map "6:a" \
  -c:v libx264 -preset fast -crf 22 \
  -c:a aac -b:a 192k \
  -pix_fmt yuv420p \
  -movflags +faststart \
  -shortest \
  "$OUTPUT" 2>/dev/null

if [ -f "$OUTPUT" ]; then
  SIZE=$(du -sh "$OUTPUT" | cut -f1)
  echo ""
  echo "✅ CLIPE GERADO: $OUTPUT ($SIZE)"
  echo "📱 Pronto para Reels / TikTok / YouTube Shorts"
  echo ""
  echo "Para subir no YouTube:"
  echo "  python3 subir_clipes_yt.py"
else
  echo "❌ Erro ao gerar clipe"
  exit 1
fi
