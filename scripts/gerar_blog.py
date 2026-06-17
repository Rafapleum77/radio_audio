#!/usr/bin/env python3
"""
Gera paginas de blog SEO para cada musica da Radio Bitcoin.
Salva em ~/Desktop/radio_audio/blog/musica-nome.html
Uso: python3.11 gerar_blog.py
"""
import json, re
from pathlib import Path

OUT = Path(__file__).parent.parent / "blog"
OUT.mkdir(exist_ok=True)

MUSICAS = [
    {
        "slug": "bitcoin-magnata",
        "titulo": "Bitcoin Magnata",
        "yt_id": "zw-7zezn96Y",
        "descricao": "Uma ode aos visionários que acreditaram no Bitcoin antes de todos. Soberania digital em forma de música.",
        "keywords": "bitcoin magnata, música bitcoin, cripto brasil, radio bitcoin",
        "letra_tema": "Riqueza verdadeira vem de visão, não de sorte. Bitcoin é para quem entende o jogo antes dos outros.",
    },
    {
        "slug": "missao-bitcoin",
        "titulo": "Missão Bitcoin",
        "yt_id": "lZ5UQYfCL-Q",
        "descricao": "A série Missão Bitcoin narra a jornada de quem escolheu a soberania digital. Ep.1 — A origem.",
        "keywords": "missão bitcoin, soberania digital, música bitcoin brasil, radio bitcoin",
        "letra_tema": "Toda grande jornada começa com uma decisão. A missão Bitcoin é escolher sua própria liberdade financeira.",
    },
    {
        "slug": "autocustodia-inoxidavel",
        "titulo": "Autocustódia Inoxidável",
        "yt_id": "fHS0VKpaOek",
        "descricao": "Suas chaves, seu Bitcoin. A música que todo hodler deveria ouvir antes de deixar a exchange guardar suas moedas.",
        "keywords": "autocustódia bitcoin, hardware wallet, não suas chaves não seu bitcoin, música cripto",
        "letra_tema": "Bitcoin inoxidável: não enferruja, não some, não é confiscado. Guarde você mesmo.",
    },
    {
        "slug": "correntes-pesadas",
        "titulo": "Correntes Pesadas",
        "yt_id": "0G2nxVfJ8Lo",
        "descricao": "O sistema fiat é uma corrente invisível. Inflação, impostos, controle. O Bitcoin é a chave.",
        "keywords": "sistema fiat, inflação bitcoin, liberdade financeira, música bitcoin brasil",
        "letra_tema": "Cada real que o governo imprime é mais um elo na corrente. Bitcoin quebra esse ciclo.",
    },
    {
        "slug": "liberdade-em-risco",
        "titulo": "Liberdade em Risco",
        "yt_id": "MCL84gEV0Bg",
        "descricao": "Quando governos e instituições ameaçam a liberdade individual, o Bitcoin surge como resistência pacífica.",
        "keywords": "liberdade bitcoin, resistência, censura bitcoin, soberania digital brasil",
        "letra_tema": "Bitcoin é resistência pacífica. Sem violência, sem revolução armada. Só matemática e código.",
    },
    {
        "slug": "a-salvacao-e-individual",
        "titulo": "A Salvação é Individual",
        "yt_id": "dWqCeOU9q7k",
        "descricao": "Ninguém vai te salvar. Nem banco, nem governo, nem Exchange. A soberania financeira começa com uma decisão pessoal.",
        "keywords": "soberania individual bitcoin, autocustódia, liberdade financeira, bitcoin brasil",
        "letra_tema": "A responsabilidade pela sua liberdade é sua. Bitcoin é o veículo — você é o piloto.",
    },
    {
        "slug": "bitcoin-2026",
        "titulo": "Bitcoin em 2026",
        "yt_id": "m48cJ9Dv5KA",
        "descricao": "2026 e o Bitcoin ainda surpreende quem duvidou. A música que captura o espírito do momento.",
        "keywords": "bitcoin 2026, preço bitcoin, halving bitcoin, música cripto brasil",
        "letra_tema": "Cada ciclo de halving reescreve a história. 2026 não será diferente.",
    },
    {
        "slug": "missao-bitcoin-porto",
        "titulo": "Missão Bitcoin Porto",
        "yt_id": "WHmJ_pwDeBo",
        "descricao": "Da Rádio Bitcoin para Portugal. A revolução laranja não tem fronteiras.",
        "keywords": "bitcoin portugal, bitcoin porto, cripto portugal, radio bitcoin brasil portugal",
        "letra_tema": "Do Brasil para Portugal, o Bitcoin une culturas em torno de um ideal: liberdade financeira universal.",
    },
    {
        "slug": "dance-the-night-away",
        "titulo": "Dance the Night Away",
        "yt_id": "DgTc5L_iQ6o",
        "descricao": "Bitcoin vibes eletrônicas. Quando a liberdade financeira encontra a pista de dança.",
        "keywords": "bitcoin música eletrônica, dance bitcoin, cripto brasil música, radio bitcoin",
        "letra_tema": "Celebre cada satoshi. A noite é livre quando seu Bitcoin é seu.",
    },
    {
        "slug": "digital-soul-in-the-delta",
        "titulo": "Digital Soul in the Delta",
        "yt_id": "8OBCHCyBF8E",
        "descricao": "Blues digital à beira do delta do Bitcoin. Uma alma navegando entre blocos e transações.",
        "keywords": "bitcoin blues, digital soul, música bitcoin instrumental, radio bitcoin",
        "letra_tema": "A blockchain é o delta digital. Cada bloco, um verso. Cada transação, uma nota.",
    },
]

TEMPLATE = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{titulo} — Rádio Bitcoin | Música Cripto Brasileira</title>
  <meta name="description" content="{descricao}">
  <meta name="keywords" content="{keywords}">
  <meta property="og:title" content="{titulo} — Rádio Bitcoin">
  <meta property="og:description" content="{descricao}">
  <meta property="og:image" content="https://img.youtube.com/vi/{yt_id}/maxresdefault.jpg">
  <meta property="og:url" content="https://radiobitcoin.org/blog/{slug}.html">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="canonical" href="https://radiobitcoin.org/blog/{slug}.html">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #07090d; color: #c8d0d8; font-family: -apple-system, Segoe UI, sans-serif; line-height: 1.7; }}
    header {{ background: #0b0e11; border-bottom: 1px solid #1f2937; padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; }}
    header a {{ color: #f7931a; text-decoration: none; font-weight: bold; font-size: 1.1rem; }}
    nav a {{ color: #9ca3af; text-decoration: none; margin-left: 20px; font-size: 0.9rem; }}
    nav a:hover {{ color: #f7931a; }}
    .hero {{ max-width: 860px; margin: 40px auto; padding: 0 20px; }}
    .breadcrumb {{ font-size: 0.8rem; color: #666; margin-bottom: 16px; }}
    .breadcrumb a {{ color: #f7931a; text-decoration: none; }}
    h1 {{ font-size: 2.4rem; color: #fff; margin-bottom: 12px; line-height: 1.2; }}
    .meta {{ color: #666; font-size: 0.85rem; margin-bottom: 24px; }}
    .video-wrapper {{ position: relative; padding-bottom: 56.25%; height: 0; margin-bottom: 32px; border-radius: 12px; overflow: hidden; background: #111; }}
    .video-wrapper iframe {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0; }}
    .content {{ max-width: 860px; margin: 0 auto; padding: 0 20px 60px; }}
    .content p {{ margin-bottom: 18px; font-size: 1.05rem; }}
    h2 {{ color: #f7931a; font-size: 1.3rem; margin: 32px 0 12px; }}
    .cta-box {{ background: #111721; border: 1px solid #f7931a; border-radius: 12px; padding: 24px; margin: 32px 0; text-align: center; }}
    .cta-box h3 {{ color: #f7931a; margin-bottom: 10px; }}
    .cta-btn {{ display: inline-block; background: #f7931a; color: #000; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: bold; margin: 8px; }}
    .cta-btn.outline {{ background: transparent; color: #f7931a; border: 1px solid #f7931a; }}
    .tags {{ margin-top: 32px; }}
    .tag {{ display: inline-block; background: #1a1a2a; color: #9ca3af; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; margin: 4px; }}
    .mais-musicas {{ background: #0b0e11; padding: 40px 20px; margin-top: 40px; }}
    .mais-musicas h2 {{ text-align: center; color: #f7931a; margin-bottom: 24px; }}
    .grid-musicas {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; max-width: 860px; margin: 0 auto; }}
    .card-musica {{ background: #111721; border: 1px solid #1f2937; border-radius: 8px; overflow: hidden; text-decoration: none; }}
    .card-musica img {{ width: 100%; aspect-ratio: 16/9; object-fit: cover; }}
    .card-musica span {{ display: block; padding: 10px; color: #c8d0d8; font-size: 0.85rem; }}
    footer {{ text-align: center; padding: 24px; color: #444; font-size: 0.8rem; border-top: 1px solid #1f2937; }}
  </style>
</head>
<body>
<header>
  <a href="/">📻 Rádio Bitcoin</a>
  <nav>
    <a href="/">Início</a>
    <a href="/blog/">Blog</a>
    <a href="https://radiobitcoin.org" target="_blank">Rádio ao vivo</a>
    <a href="/ebook.html">eBook grátis</a>
  </nav>
</header>

<div class="hero">
  <div class="breadcrumb"><a href="/">Início</a> › <a href="/blog/">Blog</a> › {titulo}</div>
  <h1>{titulo} 🎵</h1>
  <div class="meta">Rádio Bitcoin · Música Original · <a href="https://www.youtube.com/watch?v={yt_id}" style="color:#f7931a">Ver no YouTube</a></div>
  <div class="video-wrapper">
    <iframe src="https://www.youtube.com/embed/{yt_id}?autoplay=0&rel=0" allowfullscreen loading="lazy"></iframe>
  </div>
</div>

<div class="content">
  <p><strong>{descricao}</strong></p>

  <h2>Sobre esta música</h2>
  <p>{letra_tema}</p>
  <p>Esta é uma das músicas originais da <strong>Rádio Bitcoin</strong> — a primeira rádio 100% Bitcoin do Brasil. Nossa missão é levar a mensagem da soberania digital e da autocustódia para o maior número de pessoas possível, de um jeito que ninguém nunca fez: através da música.</p>

  <h2>O que é a Rádio Bitcoin?</h2>
  <p>A Rádio Bitcoin transmite 24 horas por dia, 7 dias por semana, com músicas originais sobre Bitcoin, notícias do mercado cripto e conteúdo educacional sobre autocustódia e soberania financeira. Tudo isso gratuitamente em <a href="https://radiobitcoin.org" style="color:#f7931a">radiobitcoin.org</a>.</p>

  <div class="cta-box">
    <h3>🔐 Aprenda a guardar seu Bitcoin do jeito certo</h3>
    <p>Download grátis: <strong>10 Erros Fatais que Brasileiros Cometem com Bitcoin</strong></p>
    <a href="/ebook.html" class="cta-btn">Baixar eBook Grátis</a>
    <a href="https://radiobitcoin.org" class="cta-btn outline" target="_blank">Ouvir a Rádio</a>
  </div>

  <h2>Playlist completa</h2>
  <p>Esta música faz parte da nossa coleção no YouTube. <a href="https://www.youtube.com/@radiobitcoinorg" style="color:#f7931a">Inscreva-se no canal</a> para não perder nenhuma música nova.</p>

  <div class="tags">
    {tags_html}
  </div>
</div>

<div class="mais-musicas">
  <h2>Mais músicas da Rádio Bitcoin</h2>
  <div class="grid-musicas" id="mais"></div>
</div>

<footer>
  © 2026 Rádio Bitcoin · <a href="/privacidade.html" style="color:#666">Privacidade</a> · <a href="https://radiobitcoin.org" style="color:#f7931a">radiobitcoin.org</a>
</footer>

<script>
const outras = {outras_json};
const grid = document.getElementById('mais');
outras.forEach(m => {{
  grid.innerHTML += `<a href="/blog/${{m.slug}}.html" class="card-musica">
    <img src="https://img.youtube.com/vi/${{m.yt_id}}/mqdefault.jpg" alt="${{m.titulo}}" loading="lazy">
    <span>${{m.titulo}}</span>
  </a>`;
}});
</script>
</body>
</html>
'''

def gerar(musica: dict, todas: list):
    outras = [m for m in todas if m["slug"] != musica["slug"]][:6]
    tags = musica["keywords"].split(", ")
    tags_html = "".join(f'<span class="tag">{t}</span>' for t in tags)
    html = TEMPLATE.format(
        **musica,
        tags_html=tags_html,
        outras_json=json.dumps(outras),
    )
    out = OUT / f"{musica['slug']}.html"
    out.write_text(html, encoding="utf-8")
    return out

def gerar_indice(todas: list):
    cards = ""
    for m in todas:
        cards += f'''
    <a href="/blog/{m["slug"]}.html" class="card-musica">
      <img src="https://img.youtube.com/vi/{m["yt_id"]}/mqdefault.jpg" alt="{m["titulo"]}" loading="lazy">
      <span>{m["titulo"]}</span>
      <p style="padding:0 10px 10px;font-size:0.8rem;color:#666">{m["descricao"][:80]}...</p>
    </a>'''

    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Blog — Músicas Bitcoin | Rádio Bitcoin Brasil</title>
  <meta name="description" content="Todas as músicas originais da Rádio Bitcoin — a primeira rádio 100% Bitcoin do Brasil. Ouça e leia sobre soberania digital, autocustódia e liberdade financeira.">
  <link rel="canonical" href="https://radiobitcoin.org/blog/">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #07090d; color: #c8d0d8; font-family: -apple-system, Segoe UI, sans-serif; }}
    header {{ background: #0b0e11; border-bottom: 1px solid #1f2937; padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; }}
    header a {{ color: #f7931a; text-decoration: none; font-weight: bold; }}
    nav a {{ color: #9ca3af; text-decoration: none; margin-left: 20px; font-size: 0.9rem; }}
    h1 {{ text-align: center; color: #fff; font-size: 2rem; padding: 40px 20px 10px; }}
    .sub {{ text-align: center; color: #666; padding-bottom: 32px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; max-width: 1100px; margin: 0 auto; padding: 0 20px 60px; }}
    .card-musica {{ background: #111721; border: 1px solid #1f2937; border-radius: 10px; overflow: hidden; text-decoration: none; transition: border-color 0.2s; }}
    .card-musica:hover {{ border-color: #f7931a; }}
    .card-musica img {{ width: 100%; aspect-ratio: 16/9; object-fit: cover; }}
    .card-musica span {{ display: block; padding: 12px 12px 4px; color: #fff; font-weight: bold; }}
    footer {{ text-align: center; padding: 24px; color: #444; font-size: 0.8rem; border-top: 1px solid #1f2937; }}
  </style>
</head>
<body>
<header>
  <a href="/">📻 Rádio Bitcoin</a>
  <nav><a href="/">Início</a><a href="https://radiobitcoin.org" target="_blank">Ao vivo</a><a href="/ebook.html">eBook grátis</a></nav>
</header>
<h1>🎵 Músicas da Rádio Bitcoin</h1>
<p class="sub">Soberania digital em forma de música. Ouça, compartilhe, se liberte.</p>
<div class="grid">{cards}</div>
<footer>© 2026 Rádio Bitcoin · <a href="https://radiobitcoin.org" style="color:#f7931a">radiobitcoin.org</a></footer>
</body>
</html>'''
    idx = OUT / "index.html"
    idx.write_text(html, encoding="utf-8")
    return idx

def main():
    print(f"Gerando {len(MUSICAS)} páginas de blog...\n")
    for m in MUSICAS:
        out = gerar(m, MUSICAS)
        print(f"  ✓ {out.name}")
    idx = gerar_indice(MUSICAS)
    print(f"\n  ✓ índice: {idx}")
    print(f"\n✅ Blog gerado em {OUT}")
    print(f"   {len(list(OUT.glob('*.html')))} páginas HTML")

if __name__ == "__main__":
    main()
