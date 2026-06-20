#!/usr/bin/env python3
"""
Gera um trailer de 60s do canal Radio Bitcoin:
- Cortes rapidos dos melhores clipes (5s cada)
- Texto animado com identidade visual
- Chamada para inscrever + link
Uso: python3.11 gerar_trailer.py
"""
import subprocess
from pathlib import Path

CLIPES = Path.home() / "radio_audio/clipes"
OUT    = Path.home() / "radio_audio/trailer_canal.mp4"

# melhores clipes na ordem certa para o trailer
SELECAO = [
    ("Missao_Bitcoin_v2.mp4",        5),
    ("Bitcoin_Magnata.mp4",           5),
    ("Autocustódia_Inoxidável.mp4",  5),
    ("Correntes_Pesadas.mp4",         5),
    ("Missao_Bitcoin_Porto.mp4",      5),
    ("Liberdade_em_Risco.mp4",        5),
    ("Dance_the_Night_Away.mp4",      5),
    ("Digital_Soul_in_the_Delta.mp4", 5),
    ("A_Salvação_é_Individual.mp4",   5),
    ("Bitcoin_e_Salvacao.mp4",        5),
    ("2026.mp4",                      5),
    ("Missao_Bitcoin_v2.mp4",         5),  # fecha com missão
]

TEXTO_FINAL = "RÁDIO BITCOIN\\nA PRIMEIRA RÁDIO\\n100% BITCOIN DO BRASIL\\nradiobitcoin.org"


def cortar_clipe(src: Path, duracao: int, idx: int) -> Path | None:
    out = Path(f"/tmp/trailer_part_{idx:02d}.mp4")
    if not src.exists():
        print(f"  arquivo não encontrado: {src.name}")
        return None
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-t", str(duracao),
        "-vf", f"scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1",
        "-c:v", "h264_videotoolbox", "-b:v", "2000k",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-r", "30",
        str(out)
    ]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        print(f"  ERRO ffmpeg: {r.stderr[-200:]}")
        return None
    return out


def juntar_clipes(partes: list[Path]) -> Path:
    lista = Path("/tmp/trailer_lista.txt")
    lista.write_text("\n".join(f"file '{p}'" for p in partes))
    out = Path("/tmp/trailer_sem_encerramento.mp4")
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(lista),
        "-c:v", "h264_videotoolbox", "-b:v", "3000k",
        "-c:a", "aac", "-b:a", "128k",
        str(out)
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return out


def adicionar_encerramento(video_in: Path) -> Path:
    out = Path("/tmp/trailer_final.mp4")
    # adiciona 8s de tela preta com texto no final
    filtro = (
        f"[0:v]"
        f"drawtext=text='RÁDIO BITCOIN':fontsize=72:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2-80:"
        f"enable='gte(t,{_dur(video_in)})',"
        f"drawtext=text='radiobitcoin.org':fontsize=40:fontcolor=#F7931A:x=(w-text_w)/2:y=(h-text_h)/2:"
        f"enable='gte(t,{_dur(video_in)+1})',"
        f"drawtext=text='Inscreva-se ↓':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2+60:"
        f"enable='gte(t,{_dur(video_in)+2})'[v]"
    )
    # mais simples: só adiciona texto overlay no ultimo segundo
    cmd = [
        "ffmpeg", "-y", "-i", str(video_in),
        "-vf",
        "drawtext=text='RÁDIO BITCOIN':fontsize=60:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2-60:enable='gte(t,55)',"
        "drawtext=text='radiobitcoin.org':fontsize=42:fontcolor=#F7931A:x=(w-text_w)/2:y=(h-text_h)/2:enable='gte(t,56)',"
        "drawtext=text='Inscreva-se ↓':fontsize=34:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2+60:enable='gte(t,57)'",
        "-c:v", "h264_videotoolbox", "-b:v", "3000k",
        "-c:a", "copy",
        str(out)
    ]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        print(f"  aviso drawtext: {r.stderr[-100:]}")
        return video_in
    return out


def _dur(p: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(p)
    ])
    return float(out.decode().strip())


def main():
    print("=== Gerando trailer do canal Rádio Bitcoin ===\n")
    partes = []

    for i, (nome, dur) in enumerate(SELECAO):
        src = CLIPES / nome
        print(f"  [{i+1}/{len(SELECAO)}] {nome} ({dur}s)...")
        part = cortar_clipe(src, dur, i)
        if part:
            partes.append(part)

    if not partes:
        print("Nenhum clipe processado.")
        return

    print(f"\nJuntando {len(partes)} partes...")
    video = juntar_clipes(partes)

    print("Adicionando texto final...")
    video_final = adicionar_encerramento(video)

    # copia pro destino
    import shutil
    shutil.copy(str(video_final), str(OUT))
    dur = _dur(OUT)
    print(f"\n✅ Trailer gerado: {OUT}")
    print(f"   Duração: {dur:.1f}s | Tamanho: {OUT.stat().st_size//1024//1024}MB")
    print(f"\nPara subir como trailer do canal:")
    print(f"   python3.11 subir_clipes_yt.py {OUT}")


if __name__ == "__main__":
    main()
