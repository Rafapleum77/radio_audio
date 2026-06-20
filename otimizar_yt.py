#!/usr/bin/env python3
"""
Otimiza todos os videos do canal: titulos SEO, descricoes profissionais, tags, playlists.
Uso: python3.11 otimizar_yt.py
"""
import json, time
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import googleapiclient.discovery

TOKEN  = Path.home() / "yt_token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload","https://www.googleapis.com/auth/youtube"]
UPLOADED = Path(__file__).parent / "uploaded_clipes.json"

# ── Mapa de melhorias ──────────────────────────────────────────────────────────
MELHORIAS = {
    "zw-7zezn96Y": {
        "title": "Bitcoin Magnata 💰 Música Cripto Brasileira — Rádio Bitcoin",
        "description": "Ser rico em Bitcoin não é sorte — é visão.\n\n🎵 Música original da Rádio Bitcoin, a primeira rádio 100% Bitcoin do Brasil.\n\n⚡ Sobre esta música:\nUma homenagem aos que acreditaram cedo. Autocustódia, soberania e liberdade financeira em forma de música.\n\n📻 Ouça ao vivo: https://radiobitcoin.org\n🔐 Aprenda autocustódia: https://bitadict.com\n🤖 Bots Polymarket: https://bitadict.com/curso\n\n#Bitcoin #Cripto #BitcoinBrasil #MúsicaBitcoin #Autocustódia #SoberaniaBitcoin #CriptoBrasil #BTC #RadioBitcoin #BitAdict",
        "tags": ["bitcoin","cripto","bitcoin brasil","música bitcoin","autocustódia","soberania bitcoin","BTC","radio bitcoin","bitadict","crypto brasil"],
        "playlist": "Músicas Bitcoin Brasil",
    },
    "m48cJ9Dv5KA": {
        "title": "Bitcoin em 2026 — O Ano que Tudo Muda 🚀 Música Cripto",
        "description": "2026 chegou. O Bitcoin mudou o mundo — ou o mundo ainda não percebeu?\n\n🎵 Música original da Rádio Bitcoin, a primeira rádio 100% Bitcoin do Brasil.\n\n📻 Ouça ao vivo: https://radiobitcoin.org\n🔐 Aprenda autocustódia: https://bitadict.com\n\n#Bitcoin2026 #Bitcoin #BTC #CriptoBrasil #RadioBitcoin #MúsicaBitcoin #BitAdict",
        "tags": ["bitcoin 2026","bitcoin","BTC","cripto brasil","radio bitcoin","música bitcoin","bitadict","crypto 2026"],
        "playlist": "Músicas Bitcoin Brasil",
    },
    "6JJwYFO1xSg": {
        "title": "Bitcoin no Espaço 🚀 Parceria Bybit × SpaceX — Rádio Bitcoin",
        "description": "O futuro da liberdade financeira está além das fronteiras.\n\n🎵 Música original da Rádio Bitcoin.\n\n🚀 Trade com segurança: https://www.bybit.com\n📻 Ouça ao vivo: https://radiobitcoin.org\n🔐 Aprenda autocustódia: https://bitadict.com\n\n#Bitcoin #Bybit #SpaceX #CriptoBrasil #RadioBitcoin #BTC #BitAdict",
        "tags": ["bitcoin","bybit","spacex","cripto brasil","radio bitcoin","BTC","bitadict","futuros bitcoin"],
        "playlist": "Músicas Bitcoin Brasil",
    },
    "dWqCeOU9q7k": {
        "title": "A Salvação é Individual 🙏 Soberania Bitcoin — Música Cripto",
        "description": "Ninguém vai te salvar. Soberania é uma escolha pessoal.\n\n🎵 Música original da Rádio Bitcoin, a primeira rádio 100% Bitcoin do Brasil.\n\n📻 Ouça ao vivo: https://radiobitcoin.org\n🔐 Aprenda autocustódia: https://bitadict.com\n\n#Bitcoin #Soberania #Autocustódia #CriptoBrasil #RadioBitcoin #BTC #BitAdict #LiberdadeFinanceira",
        "tags": ["bitcoin","soberania","autocustódia","cripto brasil","radio bitcoin","BTC","bitadict","liberdade financeira"],
        "playlist": "Autocustódia & Soberania",
    },
    "fHS0VKpaOek": {
        "title": "Autocustódia Inoxidável 🔐 Suas Chaves, Sua Liberdade — Bitcoin",
        "description": "Não confie. Verifique. Suas chaves, seu Bitcoin.\n\n🎵 Música original da Rádio Bitcoin, a primeira rádio 100% Bitcoin do Brasil.\n\n📻 Ouça ao vivo: https://radiobitcoin.org\n🔐 Kit Autocustódia: https://bitadict.com/recovery\n\n#Autocustódia #Bitcoin #NãoSuasChavesNãoSeuBitcoin #CriptoBrasil #RadioBitcoin #BTC #BitAdict",
        "tags": ["autocustódia","bitcoin","não suas chaves não seu bitcoin","cripto brasil","radio bitcoin","BTC","bitadict","hardware wallet"],
        "playlist": "Autocustódia & Soberania",
    },
    "6595xiZnXa0": {
        "title": "Autocustódia Bitcoin 🔑 Guarde Seu Próprio Bitcoin — Música",
        "description": "A exchange pode falir. Seu Bitcoin não precisa.\n\n🎵 Música original da Rádio Bitcoin, a primeira rádio 100% Bitcoin do Brasil.\n\n📻 Ouça ao vivo: https://radiobitcoin.org\n🔐 Kit Autocustódia: https://bitadict.com/recovery\n\n#Autocustódia #Bitcoin #ColdWallet #CriptoBrasil #RadioBitcoin #BTC #BitAdict",
        "tags": ["autocustódia","bitcoin","cold wallet","cripto brasil","radio bitcoin","BTC","bitadict","segurança bitcoin"],
        "playlist": "Autocustódia & Soberania",
    },
    "4xI0gWCekUs": {
        "title": "Autocustódia Inoxidável 🛡️ Bitcoin que Ninguém Tira de Você",
        "description": "Bitcoin inoxidável: resistente a governos, exchanges e tempo.\n\n🎵 Música original da Rádio Bitcoin, a primeira rádio 100% Bitcoin do Brasil.\n\n📻 Ouça ao vivo: https://radiobitcoin.org\n🔐 Kit Autocustódia: https://bitadict.com/recovery\n\n#Autocustódia #Bitcoin #Inoxidável #CriptoBrasil #RadioBitcoin #BTC #BitAdict",
        "tags": ["autocustódia","bitcoin","inoxidável","cripto brasil","radio bitcoin","BTC","bitadict","soberania"],
        "playlist": "Autocustódia & Soberania",
    },
    "1pbsUAOyE2g": {
        "title": "Bitcoin Salvação 🙌 Liberdade Financeira pela Cripto — Música",
        "description": "Para quem encontrou no Bitcoin mais do que investimento — encontrou propósito.\n\n🎵 Música original da Rádio Bitcoin, a primeira rádio 100% Bitcoin do Brasil.\n\n📻 Ouça ao vivo: https://radiobitcoin.org\n🔐 Aprenda: https://bitadict.com\n\n#Bitcoin #Salvação #LiberdadeFinanceira #CriptoBrasil #RadioBitcoin #BTC #BitAdict",
        "tags": ["bitcoin","salvação","liberdade financeira","cripto brasil","radio bitcoin","BTC","bitadict"],
        "playlist": "Músicas Bitcoin Brasil",
    },
    "NsAIWZfgUT0": {
        "title": "Bitcoin e Salvação ✝️ Fé e Liberdade Financeira — Música Cripto",
        "description": "Dois caminhos para a liberdade. Um é espiritual. O outro é digital.\n\n🎵 Música original da Rádio Bitcoin, a primeira rádio 100% Bitcoin do Brasil.\n\n📻 Ouça ao vivo: https://radiobitcoin.org\n🔐 Aprenda: https://bitadict.com\n\n#Bitcoin #Fé #LiberdadeFinanceira #CriptoBrasil #RadioBitcoin #BTC #BitAdict",
        "tags": ["bitcoin","fé","liberdade financeira","cripto brasil","radio bitcoin","BTC","bitadict","salvação"],
        "playlist": "Músicas Bitcoin Brasil",
    },
    "bhmGcIC0qGA": {
        "title": "Bitcoin e Salvação 🎸 Charlie Brown Jr Style — Música Cripto BR",
        "description": "O estilo Charlie Brown Jr encontrou o Bitcoin. Resultado? Isso aqui.\n\n🎵 Música original da Rádio Bitcoin, a primeira rádio 100% Bitcoin do Brasil.\n\n📻 Ouça ao vivo: https://radiobitcoin.org\n🔐 Aprenda: https://bitadict.com\n\n#Bitcoin #CharlieBrownJr #CriptoBrasil #RadioBitcoin #BTC #BitAdict #RockBitcoin",
        "tags": ["bitcoin","charlie brown jr","cripto brasil","radio bitcoin","BTC","bitadict","rock bitcoin","música cripto"],
        "playlist": "Músicas Bitcoin Brasil",
    },
    "qs72f2KUlho": {
        "title": "Bitcoin e Salvação 🙏 Versão Especial — Rádio Bitcoin Brasil",
        "description": "A versão definitiva. Bitcoin como caminho para a liberdade real.\n\n🎵 Música original da Rádio Bitcoin, a primeira rádio 100% Bitcoin do Brasil.\n\n📻 Ouça ao vivo: https://radiobitcoin.org\n🔐 Aprenda: https://bitadict.com\n\n#Bitcoin #Salvação #CriptoBrasil #RadioBitcoin #BTC #BitAdict",
        "tags": ["bitcoin","salvação","cripto brasil","radio bitcoin","BTC","bitadict","liberdade"],
        "playlist": "Músicas Bitcoin Brasil",
    },
    "0G2nxVfJ8Lo": {
        "title": "Correntes Pesadas ⛓️ O Peso do Sistema Fiat — Música Bitcoin",
        "description": "O sistema fiat é uma corrente invisível. O Bitcoin é a chave.\n\n🎵 Música original da Rádio Bitcoin, a primeira rádio 100% Bitcoin do Brasil.\n\n📻 Ouça ao vivo: https://radiobitcoin.org\n🔐 Aprenda: https://bitadict.com\n\n#Bitcoin #Fiat #LiberdadeFinanceira #CriptoBrasil #RadioBitcoin #BTC #BitAdict #SistemaFiat",
        "tags": ["bitcoin","fiat","liberdade financeira","cripto brasil","radio bitcoin","BTC","bitadict","sistema fiat"],
        "playlist": "Autocustódia & Soberania",
    },
    "c5SPNBaJo54": {
        "title": "Criptografia: Honre Seu Bitcoin 🔐 SHORT — Rádio Bitcoin",
        "description": "30 segundos de verdade sobre criptografia e Bitcoin.\n\n🎵 Rádio Bitcoin — a primeira rádio 100% Bitcoin do Brasil.\n\n📻 Ouça ao vivo: https://radiobitcoin.org\n🔐 Kit Autocustódia: https://bitadict.com/recovery\n\n#Bitcoin #Criptografia #Shorts #CriptoBrasil #RadioBitcoin #BTC #BitAdict",
        "tags": ["bitcoin","criptografia","shorts","cripto brasil","radio bitcoin","BTC","bitadict"],
        "playlist": "Autocustódia & Soberania",
    },
    "DgTc5L_iQ6o": {
        "title": "Dance the Night Away 🕺 Bitcoin Vibes — Música Eletrônica Cripto",
        "description": "Quando o Bitcoin toca, a noite é sua.\n\n🎵 Música original da Rádio Bitcoin, a primeira rádio 100% Bitcoin do Brasil.\n\n📻 Ouça ao vivo: https://radiobitcoin.org\n🔐 Aprenda: https://bitadict.com\n\n#Bitcoin #Dance #MúsicaEletrônica #CriptoBrasil #RadioBitcoin #BTC #BitAdict #ElectronicMusic",
        "tags": ["bitcoin","dance","música eletrônica","cripto brasil","radio bitcoin","BTC","bitadict","electronic music"],
        "playlist": "Músicas Bitcoin Brasil",
    },
    "8OBCHCyBF8E": {
        "title": "Digital Soul in the Delta 🌊 Bitcoin Blues — Rádio Bitcoin",
        "description": "Uma alma digital navegando o delta do Bitcoin.\n\n🎵 Música original da Rádio Bitcoin, a primeira rádio 100% Bitcoin do Brasil.\n\n📻 Ouça ao vivo: https://radiobitcoin.org\n🔐 Aprenda: https://bitadict.com\n\n#Bitcoin #Blues #DigitalSoul #RadioBitcoin #BTC #BitAdict #CriptoBrasil",
        "tags": ["bitcoin","blues","digital soul","radio bitcoin","BTC","bitadict","cripto brasil"],
        "playlist": "Músicas Bitcoin Brasil",
    },
    "MCL84gEV0Bg": {
        "title": "Liberdade em Risco ⚠️ O Bitcoin Pode Salvar Sua Liberdade?",
        "description": "Quando a liberdade está em risco, o Bitcoin é resistência.\n\n🎵 Música original da Rádio Bitcoin, a primeira rádio 100% Bitcoin do Brasil.\n\n📻 Ouça ao vivo: https://radiobitcoin.org\n🔐 Aprenda: https://bitadict.com\n\n#Bitcoin #Liberdade #Resistência #CriptoBrasil #RadioBitcoin #BTC #BitAdict",
        "tags": ["bitcoin","liberdade","resistência","cripto brasil","radio bitcoin","BTC","bitadict","soberania"],
        "playlist": "Autocustódia & Soberania",
    },
    "lZ5UQYfCL-Q": {
        "title": "Missão Bitcoin 🚀 Ep.1 — A Origem da Soberania Digital",
        "description": "Toda missão tem um começo. Esta é a nossa.\n\n🎵 Música original da Rádio Bitcoin, a primeira rádio 100% Bitcoin do Brasil.\n\n⚡ Capítulos:\n00:00 - Introdução\n00:30 - Missão Bitcoin começa\n\n📻 Ouça ao vivo: https://radiobitcoin.org\n🔐 Aprenda: https://bitadict.com\n\n#MissãoBitcoin #Bitcoin #CriptoBrasil #RadioBitcoin #BTC #BitAdict #SoberaniaBitcoin",
        "tags": ["missão bitcoin","bitcoin","cripto brasil","radio bitcoin","BTC","bitadict","soberania bitcoin","ep1"],
        "playlist": "Missão Bitcoin 🚀",
    },
    "AQVk58FxS_Y": {
        "title": "Missão Bitcoin 🚀 Ep.2 — O Caminho da Autocustódia",
        "description": "A missão continua. Ep.2 da série mais importante do Bitcoin brasileiro.\n\n🎵 Música original da Rádio Bitcoin, a primeira rádio 100% Bitcoin do Brasil.\n\n📻 Ouça ao vivo: https://radiobitcoin.org\n🔐 Aprenda: https://bitadict.com\n\n#MissãoBitcoin #Bitcoin #CriptoBrasil #RadioBitcoin #BTC #BitAdict",
        "tags": ["missão bitcoin","bitcoin","cripto brasil","radio bitcoin","BTC","bitadict","ep2","autocustódia"],
        "playlist": "Missão Bitcoin 🚀",
    },
    "WHmJ_pwDeBo": {
        "title": "Missão Bitcoin Porto 🇵🇹 Bitcoin em Portugal — Rádio Bitcoin",
        "description": "Bitcoin não tem fronteiras. Da rádio Bitcoin para Portugal e o mundo.\n\n🎵 Música original da Rádio Bitcoin, a primeira rádio 100% Bitcoin do Brasil.\n\n📻 Ouça ao vivo: https://radiobitcoin.org\n🔐 Aprenda: https://bitadict.com\n\n#Bitcoin #Portugal #Porto #CriptoBrasil #RadioBitcoin #BTC #BitAdict #BitcoinPortugal",
        "tags": ["bitcoin","portugal","porto","cripto brasil","radio bitcoin","BTC","bitadict","bitcoin portugal"],
        "playlist": "Missão Bitcoin 🚀",
    },
    "o-5Hm-tGlQ0": {
        "title": "Missão Bitcoin ⚡ SHORT — 60 Segundos de Soberania Digital",
        "description": "60 segundos. Uma missão. Bitcoin.\n\n🎵 Rádio Bitcoin — a primeira rádio 100% Bitcoin do Brasil.\n\n📻 https://radiobitcoin.org | 🔐 https://bitadict.com\n\n#MissãoBitcoin #Bitcoin #Shorts #CriptoBrasil #RadioBitcoin #BTC #BitAdict",
        "tags": ["missão bitcoin","bitcoin","shorts","cripto brasil","radio bitcoin","BTC","bitadict"],
        "playlist": "Missão Bitcoin 🚀",
    },
    "wu-heN7DWjU": {
        "title": "Missão Bitcoin v2 🚀 A Versão Definitiva — Rádio Bitcoin Brasil",
        "description": "A versão definitiva da Missão Bitcoin. Mais forte, mais clara, mais livre.\n\n🎵 Música original da Rádio Bitcoin, a primeira rádio 100% Bitcoin do Brasil.\n\n📻 Ouça ao vivo: https://radiobitcoin.org\n🔐 Aprenda: https://bitadict.com\n\n#MissãoBitcoin #Bitcoin #CriptoBrasil #RadioBitcoin #BTC #BitAdict #SoberaniaBitcoin",
        "tags": ["missão bitcoin","bitcoin","cripto brasil","radio bitcoin","BTC","bitadict","soberania bitcoin","v2"],
        "playlist": "Missão Bitcoin 🚀",
    },
}

PLAYLISTS = ["Músicas Bitcoin Brasil", "Missão Bitcoin 🚀", "Autocustódia & Soberania"]


def get_youtube():
    creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN.write_text(creds.to_json())
    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)


def criar_playlists(yt):
    print("\n=== Criando playlists ===")
    ids = {}
    # busca playlists existentes
    r = yt.playlists().list(part="snippet", mine=True, maxResults=50).execute()
    for p in r.get("items", []):
        ids[p["snippet"]["title"]] = p["id"]

    for nome in PLAYLISTS:
        if nome in ids:
            print(f"  já existe: {nome} ({ids[nome]})")
            continue
        r = yt.playlists().insert(part="snippet,status", body={
            "snippet": {"title": nome, "description": f"Rádio Bitcoin — {nome}"},
            "status": {"privacyStatus": "public"}
        }).execute()
        ids[nome] = r["id"]
        print(f"  criada: {nome} ({r['id']})")
        time.sleep(1)
    return ids


def adicionar_playlist(yt, video_id, playlist_id):
    try:
        yt.playlistItems().insert(part="snippet", body={
            "snippet": {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}
        }).execute()
    except Exception as e:
        if "duplicate" in str(e).lower():
            pass
        else:
            print(f"    playlist err: {e}")


def atualizar_video(yt, video_id, dados, playlist_ids):
    m = dados
    try:
        yt.videos().update(part="snippet", body={
            "id": video_id,
            "snippet": {
                "title": m["title"],
                "description": m["description"],
                "tags": m["tags"],
                "categoryId": "10",
            }
        }).execute()
        print(f"  ✓ {m['title'][:60]}")
    except Exception as e:
        print(f"  ERRO {video_id}: {e}")
        return

    # adiciona à playlist
    pl_nome = m.get("playlist")
    if pl_nome and pl_nome in playlist_ids:
        adicionar_playlist(yt, video_id, playlist_ids[pl_nome])

    time.sleep(2)


def main():
    yt = get_youtube()
    playlist_ids = criar_playlists(yt)

    print(f"\n=== Otimizando {len(MELHORIAS)} vídeos ===")
    for vid_id, dados in MELHORIAS.items():
        print(f"\n→ {vid_id}")
        atualizar_video(yt, vid_id, dados, playlist_ids)

    print("\n✅ Concluído!")


if __name__ == "__main__":
    main()
