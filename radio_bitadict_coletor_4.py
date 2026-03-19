# -*- coding: utf-8 -*-
import os, json, time, hashlib, requests, feedparser, re, subprocess
from pathlib import Path
from gtts import gTTS

# --- CONFIGURAÇÃO DE PASTA ---
DIR_BASE = Path(__file__).parent
ARQUIVO_AUDIO_FINAL = DIR_BASE / "noticias.mp3" 
DIR_DADOS = DIR_BASE / "radio_dados"
DIR_DADOS.mkdir(exist_ok=True)
ARQUIVO_HISTORICO = DIR_DADOS / "historico_v4.json"

# --- SUA LISTA DE ELITE ---
PERFIS_X = [
    "bitadict", "saylor", "elonmusk", "polymarketeiro", "NickSzabo4", 
    "0xCVYH", "adamuchigabriel", "namcios", "jpmayall", "PaladinRood", 
    "PesquisadorLunar", "FragmentedDjinn", "livecoinsBR", "zerqfer"
]

def limpar_texto(texto):
    """ Remove links, arrobas e lixo para a voz ficar profissional """
    texto = re.sub(r'http\S+|www\S+|https\S+', '', texto, flags=re.MULTILINE)
    texto = re.sub(r'@\w+', '', texto) 
    texto = re.sub(r'[^\w\s,.:!?-]', '', texto)
    return " ".join(texto.split())

def noticia_ja_lida(uid):
    if not ARQUIVO_HISTORICO.exists(): return False
    with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
        return uid in json.load(f)

def salvar_historico(uid):
    hist = []
    if ARQUIVO_HISTORICO.exists():
        with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
            hist = json.load(f)
    hist.append(uid)
    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(hist[-200:], f)

def subir_para_github():
    """ Envia o áudio para o site automaticamente """
    try:
        # Com o Git instalado, esses comandos agora funcionam!
        subprocess.run(["git", "add", "noticias.mp3"], check=True)
        subprocess.run(["git", "commit", "-m", "Radio Update: Auto"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("🚀 SUCESSO! Noticia enviada para o site.")
    except Exception as e:
        print(f"⚠️ Erro no Push (Verifique o login): {e}")

def gerar_audio(texto):
    try:
        limpo = limpar_texto(texto)
        print(f"🎙️ Gravando noticia: {limpo[:60]}...")
        tts = gTTS(text=limpo, lang='pt', slow=False)
        tts.save(str(ARQUIVO_AUDIO_FINAL))
        return True
    except: return False

def rodar_radio():
    print("🤖 RADIO BITADICT ATIVA - MONITORANDO ELITE")
    while True:
        for usuario in PERFIS_X:
            url = f"https://nitter.net/{usuario}/rss"
            try:
                feed = feedparser.parse(url)
                if feed.entries:
                    post = feed.entries[0]
                    uid = hashlib.md5(f"{usuario}_{post.title}".encode()).hexdigest()
                    if not noticia_ja_lida(uid):
                        if gerar_audio(f"Destaque de {usuario}: {post.title}"):
                            salvar_historico(uid)
                            subir_para_github()
                            time.sleep(15) 
            except: continue
        time.sleep(600) # Checa a cada 10 minutos

if __name__ == "__main__":
    rodar_radio()