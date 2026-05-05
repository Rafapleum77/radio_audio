#!/bin/bash
# Gera clipes de todas as músicas IA (categoria IA)
RADIO_DIR="$(dirname "$0")"
cd "$RADIO_DIR"

python3 -c "
import json
with open('tracks.json') as f:
    tracks = json.load(f)
ia = [t for t in tracks if t.get('category','') == 'IA']
for t in ia:
    print(t['title'] + '|' + t['file'])
" | while IFS='|' read -r title file; do
    # Escolhe imagem: usa ia_gemini_entry.png para músicas IA
    IMAGE="ia_gemini_entry.png"
    [ -f "kit_presente_futuro.jpg" ] && IMAGE="kit_presente_futuro.jpg"
    bash gerar_clipe.sh "$title" "$file" "$IMAGE"
    sleep 1
done

echo ""
echo "✅ Todos os clipes gerados em ./clipes/"
echo "📊 Total: $(ls clipes/*.mp4 2>/dev/null | wc -l | tr -d ' ') vídeos prontos"
