#!/bin/bash
# Envia músicas pro Intel (192.168.1.84) e renderiza lá
# O Intel tem ffmpeg 8.1.1 + 24GB RAM — muito mais rápido
# Uso: ./render_intel.sh
set -e

INTEL="user@192.168.1.84"
RADIO_DIR="$(cd "$(dirname "$0")" && pwd)"
SUNO="$HOME/Bots/suno/downloads"
CAMP="$RADIO_DIR/img/bitadict/campanha"
OG="$RADIO_DIR/img/og"
REMOTE_DIR="/tmp/radio_render"

# Verifica conexão
echo "🔌 Verificando Intel..."
if ! ssh -o ConnectTimeout=5 "$INTEL" "echo ok" 2>/dev/null | grep -q ok; then
  echo "❌ Intel offline (192.168.1.84) — ligue a máquina e tente novamente"
  exit 1
fi
echo "✅ Intel online"

# Cria diretório remoto
ssh "$INTEL" "mkdir -p $REMOTE_DIR/imgs $REMOTE_DIR/audio $REMOTE_DIR/output"

# Lista de jobs: "titulo|audio_local|imagem_local|output_nome"
declare -a JOBS=(
  "Bitcoin e Salvação|Bitcoin e Salvação.mp3|$SUNO/Bitcoin_e_Salvacao_38831d37.jpg|Bitcoin_e_Salvação"
  "Bitcoin Salvação|Bitcoin Salvação.mp3|$SUNO/Bitcoin_Salvacao_87ec83c6.jpg|Bitcoin_Salvação"
  "Missao Bitcoin Porto|Missao Bitcoin Porto.mp3|$SUNO/Missao_Bitcoin_a18d39a3.jpg|Missao_Bitcoin_Porto"
  "Autocustódia Inoxidável|Autocustódia Inoxidável.mp3|$CAMP/01_hero_recovery_kit.webp|Autocustodia_Inoxidavel"
  "Autocustódia|Autocustódia.mp3|$CAMP/01_hero_recovery_kit.webp|Autocustodia"
  "Correntes Pesadas|Correntes Pesadas.mp3|$OG/og_home.jpg|Correntes_Pesadas"
  "Dance the Night Away|Dance the Night Away.mp3|$OG/og_home.jpg|Dance_the_Night_Away"
  "Digital Soul in the Delta|Digital Soul in the Delta.mp3|$OG/og_home.jpg|Digital_Soul_in_the_Delta"
  "Liberdade em Risco|Liberdade em Risco.mp3|$OG/og_home.jpg|Liberdade_em_Risco"
  "Bitcoin Magnata|Bitcoin Magnata.mp3|$OG/og_home.jpg|Bitcoin_Magnata"
  "A Salvação é Individual|A salvação eh individual .mp3|$CAMP/03_familia_protegida.webp|A_Salvacao_Individual"
  "2026|2026.mp3|$OG/og_home.jpg|2026"
)

echo ""
echo "📤 Enviando arquivos para o Intel..."

for job in "${JOBS[@]}"; do
  IFS='|' read -r titulo audio img output_name <<< "$job"

  audio_path="$RADIO_DIR/$audio"
  out_mp4="$RADIO_DIR/clipes/${output_name}.mp4"

  # Pula se já existe
  if [ -f "$out_mp4" ]; then
    echo "⏭  Já existe: $output_name.mp4"
    continue
  fi

  if [ ! -f "$audio_path" ]; then
    echo "⚠  Áudio não encontrado: $audio"
    continue
  fi

  img_base=$(basename "$img")
  audio_base=$(basename "$audio")

  # Copia imagem e áudio
  scp -q "$img" "$INTEL:$REMOTE_DIR/imgs/$img_base" 2>/dev/null || true
  scp -q "$audio_path" "$INTEL:$REMOTE_DIR/audio/$audio_base"

  echo "🎬 Renderizando no Intel: $titulo"

  # Roda ffmpeg remoto — usa todos os cores do Intel
  ssh "$INTEL" "
    FONT=\"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf\"
    [ ! -f \"\$FONT\" ] && FONT=\"\$(fc-list : file | head -1 | cut -d: -f1)\"
    ffmpeg -y \
      -loop 1 -i '$REMOTE_DIR/imgs/$img_base' \
      -i '$REMOTE_DIR/audio/$audio_base' \
      -t 60 \
      -vf \"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,drawbox=x=0:y=1550:w=1080:h=370:color=black@0.80:t=fill,drawtext=fontfile='\$FONT':text='📻 Rádio Bitcoin':fontcolor=00ff41:fontsize=42:x=(w-text_w)/2:y=1580:shadowcolor=black:shadowx=2:shadowy=2,drawtext=fontfile='\$FONT':text='$titulo':fontcolor=white:fontsize=52:x=(w-text_w)/2:y=1650:shadowcolor=black:shadowx=2:shadowy=2,drawtext=fontfile='\$FONT':text='radiobitcoin.org':fontcolor=f7c948:fontsize=36:x=(w-text_w)/2:y=1740:shadowcolor=black:shadowx=2:shadowy=2,drawtext=fontfile='\$FONT':text='texugorecords@walletofsatoshi.com':fontcolor=aaaaaa:fontsize=28:x=(w-text_w)/2:y=1800\" \
      -c:v libx264 -preset fast -crf 23 -threads 0 \
      -c:a aac -b:a 192k \
      -pix_fmt yuv420p -movflags +faststart \
      '$REMOTE_DIR/output/$output_name.mp4' 2>/dev/null && echo OK
  "

  # Baixa o resultado
  if scp -q "$INTEL:$REMOTE_DIR/output/$output_name.mp4" "$out_mp4" 2>/dev/null; then
    SIZE=$(du -sh "$out_mp4" | cut -f1)
    echo "✅ $output_name.mp4 ($SIZE)"
  else
    echo "❌ Falhou ao baixar: $output_name"
  fi
done

# Limpa temporários no Intel
ssh "$INTEL" "rm -rf $REMOTE_DIR" 2>/dev/null || true

echo ""
echo "🏁 Render remoto concluído!"
echo "Clipes em: $RADIO_DIR/clipes/"
ls -lh "$RADIO_DIR/clipes/"*.mp4 2>/dev/null | awk '{print $5, $9}'
