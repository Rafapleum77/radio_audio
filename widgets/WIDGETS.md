# Widgets reusáveis — Radio Bitcoin

Componentes HTML standalone que vivem em `radio/widgets/` e podem ser incluídos em qualquer página do site.

## Inventário atual

| Widget | Arquivo | O que faz | Quando usar |
|---|---|---|---|
| **nav** | [nav.html](nav.html) | Barra superior 4 links (Rádio · Carteira · Recovery · Agenda) | Em todas as páginas do site pra navegação consistente |
| **social** | [social.html](social.html) | Painel "🟢 ACOMPANHE A GENTE" com 5 cards de redes (YT/TT/IG/FB/X) + janelas ótimas | Logo após nav, em páginas com foco de awareness |
| **mini-carteira** | [mini-carteira.html](mini-carteira.html) | Card snapshot da carteira (BUY/HOLD/SELL + top picks ao vivo via `/carteira.json`) | Em sidebars ou colunas estreitas (precisa `/carteira.json` no domínio) |
| **cta-sticky-mobile** | [cta-sticky-mobile.html](cta-sticky-mobile.html) | Barra dourada fixa no rodapé só em mobile ≤768px (CTA WhatsApp) | Em qualquer página comercial — boost de conversão mobile |

## Como usar

### Método 1 — include dinâmico (recomendado, 1 linha)

```html
<head>
  <!-- ... outros meta tags ... -->
  <script src="/widgets/include.js" defer></script>
</head>
<body>
  <div data-widget="nav"></div>
  <div data-widget="social"></div>
  <main>
    <!-- conteúdo da página -->
    <div data-widget="mini-carteira"></div>
  </main>
  <div data-widget="cta-sticky-mobile"></div>
</body>
```

O [include.js](include.js) detecta todo `<div data-widget="X">`, fetcha `/widgets/X.html`, substitui inline e re-executa scripts. Cache de sessão evita re-fetch.

### Método 2 — copia/cola estático

Abre o arquivo do widget e cola o conteúdo direto na página. Pior pra manutenção mas zero dependência de JS.

## Convenções de naming

- Classes CSS sempre prefixadas `.rb-<widget>__<elemento>` (ex: `rb-social__card`, `rb-mini-carteira`)
- Estilos inline `<style>` ficam dentro do próprio widget (não vazam global)
- Texto/links dentro do widget ficam estáticos no HTML — pra parametrizar, edita o arquivo direto
- IDs evitados (preferir classes) pra permitir múltiplas instâncias

## Páginas atuais que usam widgets

| Página | Widgets usados |
|---|---|
| `index.html` | nav + social + cta-sticky-mobile + mini-carteira (inline ainda, não via include.js — refactor pendente) |
| `recovery.html` | nav + cta-sticky-mobile (inline) |
| `agenda.html` | (nada por enquanto — candidata pra refactor) |
| `carteira.html` | (nada por enquanto) |

## Próximos widgets candidatos

- **header-logo**: bloco do logo principal + clock + BTC price (header do index.html)
- **ticker**: ticker rolante (BTC/ETH/SOL/etc) — refactor da `<div id="ticker">`
- **stats-row**: 4 cards de stats (DOM/MCAP/FEAR/HALVING)
- **partners-grid**: grid de logos de parceiros
- **nostr-broadcast**: bloco do feed Nostr ao vivo

## Manutenção

Cada widget deve ser **autocontido**:
- HTML + CSS (`<style>`) + JS (`<script>`) no mesmo arquivo
- Sem depender de variáveis globais externas
- Comportamento degrada graciosamente se backend offline (ex: `mini-carteira` mostra "offline" se `/carteira.json` falhar)

Pra editar um widget que aparece em várias páginas: **edita só o arquivo em `widgets/X.html` e todas as páginas que usam `data-widget="X"` atualizam no próximo reload**.
