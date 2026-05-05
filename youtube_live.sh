#!/bin/bash
# YouTube Live 24/7 — Rádio Bitcoin
# Uso: YTKEY=sua_chave_stream bash youtube_live.sh
#
# Para obter a chave:
# 1. youtube.com/live_dashboard
# 2. Criar stream → copiar "Chave de stream"
# 3. Rodar: YTKEY=xxxx-xxxx-xxxx-xxxx bash youtube_live.sh

YTKEY="${YTKEY:-COLE_SUA_CHAVE_AQUI}"
RADIO_DIR="$(dirname "$0")"
RTMP_URL="rtmp://a.rtmp.youtube.com/live2/$YTKEY"

cd "$RADIO_DIR"

if [ "$YTKEY" = "COLE_SUA_CHAVE_AQUI" ]; then
  echo "❌ Configure a chave do YouTube:"
  echo "   YTKEY=sua-chave bash youtube_live.sh"
  exit 1
fi

# Cria playlist de áudio (loop infinito)
python3 -c "
import json, os
with open('tracks.json') as f:
    tracks = json.load(f)
lines = []
for t in tracks:
    f = t['file']
    if os.path.exists(f):
        lines.append(f\"file '{f}'\")
with open('/tmp/radio_playlist.txt','w') as f:
    f.write('\n'.join(lines))
print(f'Playlist: {len(lines)} faixas')
"

# Background visual (imagem rotacionando a cada 30s)
# Usa ia_gemini_entry.png como padrão
IMAGE="ia_gemini_entry.png"
FONT="/System/Library/Fonts/Helvetica.ttc"

echo "🔴 Iniciando YouTube Live..."
echo "📡 RTMP: $RTMP_URL"

# Stream: áudio da playlist + visual estático + texto dinâmico
ffmpeg \
  -re \
  -stream_loop -1 -f concat -safe 0 -i /tmp/radio_playlist.txt \
  -loop 1 -i "$IMAGE" \
  -filter_complex "
    [1:v]scale=1280:720:force_original_aspect_ratio=increase,
    crop=1280:720,
    drawrect=x=0:y=580:w=1280:h=140:color=black@0.8:t=fill,
    drawtext=fontfile='$FONT':text='📻 RÁDIO BITCOIN — AO VIVO':fontcolor=00ff41:fontsize=40:x=(w-text_w)/2:y=595:shadowcolor=black:shadowx=2:shadowy=2,
    drawtext=fontfile='$FONT':text='radiobitcoin.bitadict.com  ⚡ Zap\\: texugorecords@walletofsatoshi.com':fontcolor=f7c948:fontsize=26:x=(w-text_w)/2:y=650:shadowcolor=black:shadowx=1:shadowy=1,
    drawtext=fontfile='$FONT':text='%{pts\\:localtime\\:$(date +%s)\\:%H\\:%M\\:%S}':fontcolor=aaaaaa:fontsize=22:x=w-120:y=10[vout]
  " \
  -map "[vout]" -map 0:a \
  -c:v libx264 -preset veryfast -b:v 2500k -maxrate 2500k -bufsize 5000k \
  -pix_fmt yuv420p -g 50 -keyint_min 50 \
  -c:a aac -b:a 128k -ar 44100 \
  -f flv "$RTMP_URL"
