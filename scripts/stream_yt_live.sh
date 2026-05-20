#!/usr/bin/env bash
# ============================================================================
# RÁDIO BITCOIN · STREAM 24/7 PRO YOUTUBE LIVE
# ============================================================================
# Pega todos os MP3s da pasta /Users/rafaelrioscrosara/Bots/radio/, embaralha,
# loopa pra sempre, e empurra pro RTMP do YouTube com uma imagem estática
# (capa) + visualização de audio (waveform).
#
# COMO USAR:
#   1. No YouTube Studio: Criar > Transmitir ao vivo > Stream key copia.
#   2. export YT_STREAM_KEY="cole-aqui"   # OU edita o arquivo abaixo
#   3. bash stream_yt_live.sh
#
# RODA EM BACKGROUND COMO LAUNCHAGENT (mac):
#   ver  ~/Library/LaunchAgents/com.bitadict.yt-live.plist  (template no fim)
# ============================================================================

set -u

# --- CONFIG -----------------------------------------------------------------
RADIO_DIR="/Users/rafaelrioscrosara/Bots/radio"
POSTER="${RADIO_DIR}/radiobitcoin_logo_square.webp"
PLAYLIST_M3U="/tmp/radio_yt_playlist.m3u"
YT_RTMP="rtmp://a.rtmp.youtube.com/live2"
YT_STREAM_KEY="${YT_STREAM_KEY:-COLOQUE_SUA_STREAM_KEY_AQUI}"
LOG="/tmp/yt_live.log"
# ----------------------------------------------------------------------------

if [ "$YT_STREAM_KEY" = "COLOQUE_SUA_STREAM_KEY_AQUI" ]; then
  echo "ERRO: defina YT_STREAM_KEY (export YT_STREAM_KEY=...)" >&2
  echo "      ou edita esse arquivo na linha 23." >&2
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ERRO: ffmpeg nao instalado. brew install ffmpeg" >&2
  exit 1
fi

# 1. monta playlist embaralhada (todas os MP3s da pasta)
{
  echo "#EXTM3U"
  ls "$RADIO_DIR"/*.mp3 2>/dev/null | shuf | while read f; do
    echo "file '$f'" | sed "s/'/'\\\\''/g"
  done
} > "$PLAYLIST_M3U"

TOTAL=$(grep -c "^file " "$PLAYLIST_M3U")
if [ "$TOTAL" -lt 5 ]; then
  echo "ERRO: so $TOTAL MP3s em $RADIO_DIR. Sobe mais musica." >&2
  exit 1
fi
echo "[`date +%H:%M:%S`] Playlist com $TOTAL faixas." | tee -a "$LOG"

# 2. converte playlist M3U pro formato concat do ffmpeg
CONCAT_LIST="/tmp/radio_yt_concat.txt"
grep "^file " "$PLAYLIST_M3U" > "$CONCAT_LIST"

# 3. ffmpeg: loop infinito do concat, imagem estatica como video, mix pra YT
echo "[`date +%H:%M:%S`] Iniciando stream pra YouTube Live..." | tee -a "$LOG"

exec ffmpeg \
  -re \
  -stream_loop -1 \
  -f concat -safe 0 -i "$CONCAT_LIST" \
  -loop 1 -framerate 2 -i "$POSTER" \
  -filter_complex "
    [1:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=0x07090d,setsar=1[bg];
    [0:a]showwaves=s=1280x120:mode=cline:colors=0xf2a900:rate=25,format=yuva420p,colorchannelmixer=aa=0.7[wave];
    [bg][wave]overlay=0:H-h-20[v]
  " \
  -map "[v]" -map 0:a \
  -c:v libx264 -preset veryfast -tune zerolatency -pix_fmt yuv420p \
  -b:v 2500k -maxrate 2500k -bufsize 5000k -g 50 -keyint_min 50 \
  -c:a aac -b:a 128k -ar 44100 \
  -f flv "${YT_RTMP}/${YT_STREAM_KEY}" \
  2>&1 | tee -a "$LOG"
