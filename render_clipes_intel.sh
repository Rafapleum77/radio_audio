#!/bin/bash
# ============================================================
# RENDER CLIPES — Rádio Bitcoin.org
# Gera clipes monetizáveis 9:16 (Shorts/TikTok/Reels) e
# 16:9 (YouTube) com imagens IA + Ken Burns + branding
#
# Uso local:    ./render_clipes_intel.sh
# Uso via SSH:  ssh user@192.168.1.84 "bash ~/radio_render/render_clipes_intel.sh"
#
# Requer: ffmpeg, curl, python3
# ============================================================

set -e
RADIO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$RADIO_DIR"

CLIPES_DIR="clipes"
TMP_DIR="$CLIPES_DIR/tmp_imgs"
mkdir -p "$CLIPES_DIR" "$TMP_DIR"

FONT=""
for f in \
  "/System/Library/Fonts/Helvetica.ttc" \
  "/System/Library/Fonts/Arial.ttf" \
  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" \
  "C:/Windows/Fonts/Arial.ttf"; do
  [ -f "$f" ] && FONT="$f" && break
done
[ -z "$FONT" ] && echo "❌ Fonte não encontrada" && exit 1

# ─── CATÁLOGO DE MÚSICAS ORIGINAIS ───────────────────────────
# Formato: "arquivo.mp3|Título|prompt_de_imagem_ingles"
TRACKS=(
"Juros Negativos.mp3|Juros Negativos|Bitcoin Lightning bolt glowing gold against collapsing fiat currency banknotes burning dramatic cinematic dark background neon orange glow"
"Bitcoin no Gol.mp3|Bitcoin no Gol|Ronaldinho Gaucho Brazil football player dribbling skill bicycle kick stadium World Cup crowd cheering cinematic golden hour Bitcoin symbol overlay"
"Bitcoin Magnata.mp3|Bitcoin Magnata|Wealthy Bitcoin maximalist elegant dark suit gold Bitcoin coin luxury office skyscraper view dramatic cinematic lighting orange neon reflections"
"Autocustódia Inoxidável.mp3|Autocustódia Inoxidável|Steel vault door opening bright Bitcoin light inside fortress walls digital sovereignty concept dramatic cinematic dark atmosphere"
"Autocustódia.mp3|Autocustódia|Cold wallet hardware device glowing orange in darkness person holding keys to their own Bitcoin freedom concept cinematic dramatic lighting"
"Bitcoin Salvação.mp3|Bitcoin Salvação|Person escaping financial chains Bitcoin rocket launching upward from city crowd below liberation freedom dramatic wide shot cinematic"
"Bitcoin e Salvação.mp3|Bitcoin e Salvação|Golden Bitcoin coin descending like divine light people reaching upward epic cinematic religious liberation concept dramatic lighting"
"Correntes Pesadas.mp3|Correntes Pesadas|Heavy chains breaking apart Bitcoin lightning bolt shattering financial system dark dramatic cinematic orange gold sparks explosion"
"Criptografia Honre.mp3|Criptografia Honre|Digital cryptography code glowing Bitcoin shield protecting family home dramatic cinematic blue orange tech aesthetic futuristic"
"Liberdade em Risco.mp3|Liberdade em Risco|Freedom torch held high against dark storm clouds Bitcoin symbol glowing dramatic cinematic wide shot liberty concept epic"
"Digital Soul in the Delta.mp3|Digital Soul in the Delta|Blues musician playing guitar in Mississippi delta landscape Bitcoin nodes floating above as stars cinematic ethereal night sky"
"Dance the Night Away.mp3|Dance the Night Away|Bitcoin party celebration people dancing laser lights Bitcoin symbols raining down from ceiling club night cinematic neon pink gold"
"2026.mp3|2026|Futuristic city skyline 2026 Bitcoin as global reserve currency digital billboard orange neon dramatic cinematic wide shot utopian"
"Missão Bitcoin Porto.mp3|Missão Bitcoin Porto|Porto Portugal bridge Bitcoin mission agents gathering dramatic cinematic night golden orange light reflections on river Douro"
"A salvação eh individual .mp3|A Salvação é Individual|Single person walking alone toward bright Bitcoin horizon desert road dramatic cinematic warm golden light individual freedom"
)

# ─── FUNÇÕES ──────────────────────────────────────────────────

encode_url() {
  python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$1"
}

get_duration() {
  ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$1" 2>/dev/null | cut -d. -f1
}

baixar_imagens() {
  local TRACK_SLUG="$1"
  local PROMPT_BASE="$2"
  local N_IMGS="$3"
  local OUTDIR="$TMP_DIR/$TRACK_SLUG"
  mkdir -p "$OUTDIR"

  for i in $(seq 0 $((N_IMGS-1))); do
    local FILE="$OUTDIR/img_$(printf '%02d' $i).jpg"
    [ -f "$FILE" ] && continue
    local VARIATION=""
    case $((i % 4)) in
      0) VARIATION="cinematic wide shot golden hour" ;;
      1) VARIATION="dramatic close up neon dark background" ;;
      2) VARIATION="epic aerial view night city lights" ;;
      3) VARIATION="portrait artistic abstract bokeh" ;;
    esac
    local PROMPT="$PROMPT_BASE $VARIATION radiobitcoin brand"
    local ENC
    ENC=$(encode_url "$PROMPT")
    echo "    📸 imagem $((i+1))/$N_IMGS..."
    curl -sL "https://image.pollinations.ai/prompt/${ENC}?width=1080&height=1920&model=flux&nologo=true&seed=$((100+i*7+RANDOM%50))" \
      -o "$FILE" --retry 3 --retry-delay 2
    sleep 1
  done
}

gerar_clipe_vertical() {
  local AUDIO="$1"
  local TITULO="$2"
  local SLUG="$3"
  local N_IMGS="$4"
  local OUTPUT="$CLIPES_DIR/${SLUG}_shorts.mp4"
  [ -f "$OUTPUT" ] && echo "  ✅ Já existe: $OUTPUT" && return

  local DUR
  DUR=$(get_duration "$AUDIO")
  local SEG_POR_IMG=$(( DUR / N_IMGS + 1 ))
  [ "$SEG_POR_IMG" -gt 30 ] && SEG_POR_IMG=30

  local INPUTS=""
  local FILTER=""
  for i in $(seq 0 $((N_IMGS-1))); do
    local F="$TMP_DIR/$SLUG/img_$(printf '%02d' $i).jpg"
    INPUTS="$INPUTS -loop 1 -t $SEG_POR_IMG -i \"$F\""
    case $((i % 4)) in
      0) KB="zoompan=z='min(zoom+0.0012,1.25)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=${SEG_POR_IMG}*25:s=1080x1920:fps=25" ;;
      1) KB="zoompan=z='min(zoom+0.0008,1.18)':x='if(lte(zoom,1),0,x+0.8)':y='ih/2-(ih/zoom/2)':d=${SEG_POR_IMG}*25:s=1080x1920:fps=25" ;;
      2) KB="zoompan=z='if(lte(zoom,1),1.2,max(1,zoom-0.001))':x='iw/2-(iw/zoom/2)':y='if(lte(zoom,1),0,y+0.4)':d=${SEG_POR_IMG}*25:s=1080x1920:fps=25" ;;
      3) KB="zoompan=z='min(zoom+0.001,1.22)':x='iw-(iw/zoom)':y='ih/2-(ih/zoom/2)':d=${SEG_POR_IMG}*25:s=1080x1920:fps=25" ;;
    esac
    FILTER="${FILTER}[$i:v]${KB},setsar=1[v$i];"
  done

  local CONCAT=""
  for i in $(seq 0 $((N_IMGS-1))); do CONCAT="${CONCAT}[v$i]"; done
  FILTER="${FILTER}${CONCAT}concat=n=${N_IMGS}:v=1:a=0[vcombined];"

  # Overlay: faixa escura inferior + textos
  FILTER="${FILTER}[vcombined]
    drawbox=x=0:y=1560:w=1080:h=360:color=black@0.82:t=fill,
    drawtext=fontfile='${FONT}':text='📻 RÁDIO BITCOIN':fontcolor=#f2a900:fontsize=36:x=(w-text_w)/2:y=1582:shadowcolor=black:shadowx=3:shadowy=3,
    drawtext=fontfile='${FONT}':text='${TITULO}':fontcolor=white:fontsize=54:x=(w-text_w)/2:y=1636:shadowcolor=black:shadowx=3:shadowy=3,
    drawtext=fontfile='${FONT}':text='radiobitcoin.org':fontcolor=#f7c948:fontsize=32:x=(w-text_w)/2:y=1718:shadowcolor=black:shadowx=2:shadowy=2,
    drawtext=fontfile='${FONT}':text='⚡ Bitcoin é a saída':fontcolor=#9ca3af:fontsize=26:x=(w-text_w)/2:y=1776
  [vout]"

  echo "  ⚙️  Codificando vertical (Shorts/TikTok/Reels)..."
  eval ffmpeg -y $INPUTS -i \"$AUDIO\" \
    -filter_complex "\"$FILTER\"" \
    -map "[vout]" -map "${N_IMGS}:a" \
    -c:v libx264 -preset slow -crf 18 \
    -c:a aac -b:a 256k \
    -pix_fmt yuv420p \
    -movflags +faststart \
    -shortest \
    "\"$OUTPUT\"" 2>/dev/null

  [ -f "$OUTPUT" ] && echo "  ✅ $(du -sh "$OUTPUT" | cut -f1) → $OUTPUT"
}

gerar_clipe_horizontal() {
  local AUDIO="$1"
  local TITULO="$2"
  local SLUG="$3"
  local N_IMGS="$4"
  local OUTPUT="$CLIPES_DIR/${SLUG}_youtube.mp4"
  [ -f "$OUTPUT" ] && echo "  ✅ Já existe: $OUTPUT" && return

  local DUR
  DUR=$(get_duration "$AUDIO")
  local SEG_POR_IMG=$(( DUR / N_IMGS + 1 ))
  [ "$SEG_POR_IMG" -gt 30 ] && SEG_POR_IMG=30

  local INPUTS=""
  local FILTER=""
  for i in $(seq 0 $((N_IMGS-1))); do
    local F="$TMP_DIR/$SLUG/img_$(printf '%02d' $i).jpg"
    # Para 16:9 usa as mesmas imagens mas re-escala e cropa
    INPUTS="$INPUTS -loop 1 -t $SEG_POR_IMG -i \"$F\""
    case $((i % 3)) in
      0) KB="scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='min(zoom+0.0008,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=${SEG_POR_IMG}*25:s=1920x1080:fps=25" ;;
      1) KB="scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='min(zoom+0.0006,1.12)':x='if(lte(zoom,1),0,x+1)':y='ih/2-(ih/zoom/2)':d=${SEG_POR_IMG}*25:s=1920x1080:fps=25" ;;
      2) KB="scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='if(lte(zoom,1),1.12,max(1,zoom-0.0007))':x='iw/2-(iw/zoom/2)':y='if(lte(zoom,1),0,y+0.3)':d=${SEG_POR_IMG}*25:s=1920x1080:fps=25" ;;
    esac
    FILTER="${FILTER}[$i:v]${KB},setsar=1[v$i];"
  done

  local CONCAT=""
  for i in $(seq 0 $((N_IMGS-1))); do CONCAT="${CONCAT}[v$i]"; done
  FILTER="${FILTER}${CONCAT}concat=n=${N_IMGS}:v=1:a=0[vcombined];"

  FILTER="${FILTER}[vcombined]
    drawbox=x=0:y=860:w=1920:h=220:color=black@0.80:t=fill,
    drawtext=fontfile='${FONT}':text='📻 RÁDIO BITCOIN  ·  ${TITULO}':fontcolor=#f2a900:fontsize=42:x=(w-text_w)/2:y=876:shadowcolor=black:shadowx=3:shadowy=3,
    drawtext=fontfile='${FONT}':text='radiobitcoin.org  ·  ⚡ Bitcoin é a saída':fontcolor=#9ca3af:fontsize=28:x=(w-text_w)/2:y=940:shadowcolor=black:shadowx=2:shadowy=2
  [vout]"

  echo "  ⚙️  Codificando horizontal (YouTube 1080p)..."
  eval ffmpeg -y $INPUTS -i \"$AUDIO\" \
    -filter_complex "\"$FILTER\"" \
    -map "[vout]" -map "${N_IMGS}:a" \
    -c:v libx264 -preset slow -crf 18 \
    -c:a aac -b:a 256k \
    -pix_fmt yuv420p \
    -movflags +faststart \
    -shortest \
    "\"$OUTPUT\"" 2>/dev/null

  [ -f "$OUTPUT" ] && echo "  ✅ $(du -sh "$OUTPUT" | cut -f1) → $OUTPUT"
}

# ─── MAIN ─────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   RÁDIO BITCOIN — Render de Clipes Monetizáveis     ║"
echo "║   $(date '+%Y-%m-%d %H:%M')  ·  radiobitcoin.org          ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

TOTAL=${#TRACKS[@]}
for idx in "${!TRACKS[@]}"; do
  IFS='|' read -r ARQUIVO TITULO PROMPT <<< "${TRACKS[$idx]}"
  SLUG=$(echo "$TITULO" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/_/g' | sed 's/__*/_/g' | sed 's/^_//;s/_$//')

  echo "▸ [$((idx+1))/$TOTAL] $TITULO"

  if [ ! -f "$ARQUIVO" ]; then
    echo "  ⚠️  Arquivo não encontrado: $ARQUIVO — pulando"
    continue
  fi

  # Calcula número de imagens pela duração (1 a cada ~25s, mín 3 máx 8)
  DUR=$(get_duration "$ARQUIVO")
  N_IMGS=$(( DUR / 25 + 1 ))
  [ "$N_IMGS" -lt 3 ] && N_IMGS=3
  [ "$N_IMGS" -gt 8 ] && N_IMGS=8

  echo "  ⏱  Duração: ${DUR}s  |  Imagens: $N_IMGS"

  baixar_imagens "$SLUG" "$PROMPT" "$N_IMGS"
  gerar_clipe_vertical  "$ARQUIVO" "$TITULO" "$SLUG" "$N_IMGS"
  gerar_clipe_horizontal "$ARQUIVO" "$TITULO" "$SLUG" "$N_IMGS"
  echo ""
done

echo "╔══════════════════════════════════════════════════════╗"
echo "║   ✅ RENDER CONCLUÍDO                                ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "Clipes gerados em: $CLIPES_DIR/"
ls -lh "$CLIPES_DIR"/*.mp4 2>/dev/null | awk '{print "  " $5 "  " $NF}'
echo ""
echo "Próximo passo:"
echo "  python3 subir_clipes_yt.py   ← sobe para YouTube"
echo "  (TikTok/Reels: arrastar os *_shorts.mp4 manualmente)"
