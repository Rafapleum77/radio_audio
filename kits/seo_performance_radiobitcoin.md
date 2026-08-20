# Estratégia específica de SEO e performance — radiobitcoin.org

**Data-base:** auditoria pública realizada em 20 de agosto de 2026.  
**Objetivo:** aumentar descoberta orgânica, velocidade percebida, retenção, reproduções, inscrições, participação em eventos e contatos comerciais.

## Diagnóstico que orienta o plano

A radiobitcoin.org já possui título, meta description, canonical, Open Graph, `Organization`, `RadioStation`, `ListenAction` e `WebSite` em JSON-LD. Porém, a inspeção pública encontrou uma homepage muito extensa, com aproximadamente 27.732 px de altura, 256 imagens no DOM inicial, 5 elementos de áudio, 1 vídeo, 6 iframes e 136 imagens sem `alt` em uma amostra do DOM. Também não foi encontrada entidade `Event` no JSON-LD inicial, embora a homepage divulgue 11 eventos globais.

Esses sinais não substituem um teste de Lighthouse, PageSpeed Insights, Search Console ou dados de usuários reais. Eles indicam onde começar a medição e quais ações têm maior probabilidade de reduzir fricção.

## Plano técnico de SEO

### 1. Criar uma arquitetura de URLs por intenção

A homepage não deve ser a única porta de entrada. Recomenda-se criar URLs estáveis, curtas e descritivas para as principais intenções:

| Intenção | URL recomendada | Conteúdo mínimo |
|---|---|---|
| Rádio ao vivo | `/radio-bitcoin-ao-vivo/` | Player, programa atual, grade, descrição, apps de rádio e FAQ. |
| Agenda | `/agenda-bitcoin/` | Lista filtrável, mês, país, status e links oficiais. |
| Evento individual | `/eventos/bitcoin-asia-2026/` | Nome, cidade, datas, organizador, link oficial, cobertura e lembrete. |
| Notícias | `/noticias/` | Feed com categorias, autor, data, atualização e páginas individuais. |
| Vídeos | `/videos/` | Último vídeo, filtros, playlists e páginas individuais. |
| Música | `/musicas/` | Capas, faixas, contexto, player e links de compartilhamento. |
| Parceiros | `/parceiros/` ou `/anuncie/` | Mídia kit, formatos, processo comercial e contato. |

Segundo o guia oficial de SEO do Google, URLs descritivas e uma estrutura lógica ajudam usuários e mecanismos de busca a entender a relação entre as páginas.[1]

### 2. Fazer cada evento trabalhar para SEO e conversão

Cada evento precisa ter uma página própria, com um título único, descrição editorial, cidade, país, data de início, data final quando houver, fuso horário, organizador, link oficial, status de credenciamento, imagem 16:9 e CTA para adicionar ao calendário.

Nas páginas individuais, implementar JSON-LD `Event` com `name`, `startDate`, `endDate` quando conhecido, `location`, `description`, `image`, `eventStatus`, `organizer` e `offers` somente quando houver informação real. O Google recomenda que cada evento tenha uma URL única e uma página focada naquele evento, não apenas uma linha dentro de uma lista.[5]

Criar também uma taxonomia interna por região e tema: América Latina, Estados Unidos, Europa, Ásia, África, Oriente Médio, autocustódia, mineração, Lightning, adoção e infraestrutura. Isso melhora a ligação interna e permite páginas de coleção sem duplicar conteúdo.

### 3. Reescrever títulos e descrições por página

A meta description da homepage está funcional, mas cada página precisa de título e descrição próprios. Evitar títulos genéricos como “Página 1”, nomes duplicados e palavras-chave empilhadas.

Exemplos:

| Página | Title sugerido | Meta description sugerida |
|---|---|---|
| Rádio ao vivo | `Rádio Bitcoin ao vivo 24h — notícias, música e mercado` | `Ouça a Rádio Bitcoin ao vivo, acompanhe boletins, música, mercado, programas e a agenda global do ecossistema Bitcoin.` |
| Agenda | `Agenda Bitcoin 2026–2027 — eventos globais e cobertura` | `Veja eventos de Bitcoin em 2026 e 2027, com datas, locais, links oficiais, cobertura da Rádio Bitcoin e lembretes.` |
| Música | `Músicas Bitcoin e liberdade financeira — Rádio Bitcoin` | `Explore capas, faixas e lançamentos musicais da Rádio Bitcoin sobre Bitcoin, soberania, liberdade e inovação financeira.` |
| Parceiros | `Anuncie na Rádio Bitcoin — mídia, eventos e parcerias` | `Conheça formatos de patrocínio, cobertura de eventos, entrevistas e conteúdos especiais da Rádio Bitcoin.` |

O Google recomenda títulos únicos, claros e precisos, além de descrições curtas e específicas para cada página.[1]

### 4. Construir clusters editoriais, não páginas genéricas

Priorizar cinco clusters de conteúdo que combinam a pauta da rádio com buscas recorrentes:

| Cluster | Exemplos de pautas | Conversão associada |
|---|---|---|
| Bitcoin no Brasil | adoção, Pix, regulação, autocustódia, educação | newsletter e rádio ao vivo |
| Eventos Bitcoin | calendário, credenciamento, cobertura, entrevistas | lembrete e contato de imprensa |
| Liberdade e soberania digital | censura, privacidade, seed, comunicação offline | episódios, músicas e comunidade |
| Mercado e infraestrutura | stablecoins, segurança, mineração, Lightning | episódios especiais e parceiros |
| Cultura Bitcoin | música, locutores IA, Trezoitão, entrevistas | compartilhamento, voto e inscrição |

Cada publicação deve responder uma pergunta concreta, apresentar fonte quando usar dados externos, conter links internos para dois conteúdos relacionados e terminar com uma ação clara. Não criar textos apenas para “preencher palavras-chave”; o próprio Google alerta que qualidade, utilidade, atualização e organização importam mais do que uma contagem artificial de palavras.[1]

### 5. SEO para imagens e novas capas

As novas capas devem ser publicadas em páginas de música, não apenas como arquivos soltos. Para cada capa:

1. Usar nome descritivo, como `radio-bitcoin-a-voz-nao-se-apaga-capa.jpg`.
2. Preferir AVIF ou WebP para entrega web, mantendo PNG apenas para download quando necessário.
3. Usar `<img>` ou `<picture>` com `src`, `srcset`, `sizes` e fallback.
4. Definir `width`, `height` ou `aspect-ratio` para evitar deslocamento de layout.
5. Escrever `alt` contextual, por exemplo: “Capa da música A Voz Não Se Apaga, com Bitcoin dourado rompendo uma grade de censura digital”.
6. Incluir título, legenda e texto relevante próximo da imagem.
7. Adicionar URLs de imagens ao image sitemap, se a quantidade de capas crescer.
8. Definir `og:image` e `primaryImageOfPage` nas páginas de música.

O Google recomenda elementos HTML de imagem, imagens responsivas, nomes descritivos, `alt` útil e otimização de tamanho/qualidade.[2]

### 6. SEO para vídeos e áudio

Para o painel Trezoitão, cada vídeo deve ter uma página individual indexável com título único, descrição, thumbnail, data, duração, canal, transcrição ou resumo e links para episódios relacionados. Implementar `VideoObject` quando os dados estiverem disponíveis e usar títulos que expressem o assunto, não apenas a série.

Para episódios em áudio, criar páginas com `PodcastEpisode` ou `AudioObject` quando a implementação estiver de acordo com o conteúdo real. Incluir título, convidado, tema, data, player, transcrição/resumo e links para a fonte. A página do episódio deve ser carregável sem depender apenas de JavaScript para exibir o título e o texto essencial.

## Plano de performance

### 1. Medir antes de alterar

Configurar uma linha de base com PageSpeed Insights, Lighthouse, Chrome UX Report quando houver dados, WebPageTest e monitoramento de usuários reais. Registrar, por dispositivo e página:

| Métrica | Meta inicial |
|---|---|
| LCP | até 2,5 s no p75, conforme referência do web.dev.[3] |
| INP | acompanhar responsividade das interações e tarefas longas. |
| CLS | reservar espaço para imagens, vídeos, iframes e módulos dinâmicos. |
| TTFB | acompanhar o tempo até o primeiro byte e a distância do servidor. |
| Peso total | estabelecer orçamento por página e por tipo de dispositivo. |

O web.dev recomenda priorizar dados de usuários reais, complementados por testes de laboratório, porque os dois podem mostrar problemas diferentes.[3]

### 2. Otimizar a primeira dobra e o LCP

O elemento LCP deve ser descoberto no HTML inicial e carregado com prioridade. Se o herói for a agenda ou o player, usar `<img src>`/`srcset` ou markup server-rendered; evitar esconder a imagem principal atrás de JavaScript. Não aplicar `loading="lazy"` ao LCP. Usar `fetchpriority="high"` apenas no recurso principal, não em dezenas de imagens.

Comprimir a arte de agenda e o background acima da dobra, criar versões responsivas e usar CDN. O guia do web.dev recomenda tornar o recurso LCP descobrível cedo, priorizá-lo e reduzir atrasos de rede e de renderização.[3][4]

### 3. Reduzir o trabalho inicial de JavaScript

A homepage reúne player, dados de mercado, notícias, votação, mapas, weather, vídeos, bots, chat, widgets e painéis. Separar o código por módulo e carregar sob demanda tudo que não é necessário para ouvir a rádio ou entender a proposta inicial.

Ações práticas:

- usar `defer`/`async` em scripts não críticos;
- dividir bundles por rota e por módulo;
- iniciar mapas, iframes, bots e painéis apenas quando entram no viewport;
- usar fachadas para iframes de terceiros e carregar o embed após o clique;
- aplicar `content-visibility: auto` com cuidado em blocos longos;
- evitar tarefas JavaScript superiores a 50 ms no carregamento inicial;
- remover bibliotecas, tags e polling que não produzam ação mensurável.

O web.dev recomenda reduzir JavaScript desnecessário, quebrar tarefas longas e limitar atualizações grandes de renderização para melhorar INP.[4]

### 4. Evitar CLS em dados ao vivo

Reservar dimensões para imagens, banners, cards, tabelas, iframes e widgets de preço. Todos os módulos que hoje mostram “Carregando…”, “—”, “STANDBY” ou “IDLE” devem ter altura mínima definida e estados previsíveis.

Atribuir `width`/`height` a imagens, `aspect-ratio` a embeds e `min-height` a blocos dinâmicos. Não inserir banners ou promoções no topo depois que o conteúdo já apareceu. Essas ações seguem as recomendações do web.dev para reduzir deslocamentos de layout.[4]

### 5. Cache, CDN e entrega

Configurar CDN para imagens, capas, thumbnails, CSS e JavaScript. Usar cache de longa duração para assets versionados, compressão Brotli, HTTP/2 ou HTTP/3 e `Cache-Control` coerente. Para HTML, usar cache curto ou edge cache quando a atualização em tempo real permitir.

As capas e thumbnails devem ter três variantes: 1:1 para cards e música, 4:3 para componentes intermediários e 16:9 para hero, vídeos e compartilhamento. O Google recomenda imagens responsivas e formatos suportados como WebP e AVIF.[2]

## Checklist técnico de indexação

| Item | Estado a confirmar | Ação |
|---|---|---|
| `robots.txt` | verificar no servidor | Permitir páginas públicas e bloquear somente áreas privadas/experimentais. |
| `sitemap.xml` | verificar e enviar | Incluir páginas de notícias, vídeos, músicas, eventos e parceiros. |
| Search Console | confirmar propriedade | Monitorar indexação, consultas, cobertura, links e experiência. |
| Canonical | presente na homepage | Replicar em cada página canônica e revisar parâmetros. |
| JSON-LD | presente para rádio/produto | Adicionar `Event`, `VideoObject`, `BreadcrumbList` e tipos de conteúdo quando verdadeiros. |
| Status HTTP | medir por rota | Corrigir 404, cadeias de redirect e páginas vazias. |
| Links internos | ampliar | Usar âncoras descritivas entre agenda, episódios, vídeos, músicas e parceiros. |
| Imagens | 136 sem `alt` na inspeção | Corrigir em lote, distinguindo imagem decorativa de editorial. |

## Roadmap de execução

| Prazo | Implementação | Critério de sucesso |
|---|---|---|
| Semana 1 | Medição base; sitemap/robots/Search Console; correção dos estados comerciais vencidos; CTA “Ouvir / Newsletter / Agenda”. | Linha de base registrada e nenhuma campanha encerrada aparecendo como ativa. |
| Semanas 2–3 | Páginas de música e episódios; alt; dimensões; WebP/AVIF; lazy load fora da dobra; melhoria do menu. | Mais páginas indexáveis e redução de imagens sem descrição. |
| Semanas 4–6 | Páginas individuais de eventos; `Event`; calendário; links oficiais; breadcrumbs. | Eventos rastreáveis, compartilháveis e com lembrete. |
| Semanas 7–9 | Code splitting, fachadas de iframe, CDN, cache, prioridade do LCP e módulos sob demanda. | Melhora de LCP/INP/CLS em laboratório e campo. |
| Semanas 10–12 | Conteúdo por cluster; templates de notícias/vídeos/música; testes A/B do topo; relatório de conversão. | Crescimento de cliques orgânicos, play, newsletter, retorno e contatos de parceiros. |

## Instrumentação mínima

Registrar, com consentimento e privacidade adequada, `play_live`, `play_30s`, `newsletter_start`, `newsletter_complete`, `event_view`, `event_reminder`, `video_play`, `video_complete`, `cover_view`, `music_play`, `share_click`, `vote_ai`, `telegram_click`, `partner_contact` e `affiliate_click`.

Separar os relatórios por dispositivo, origem, novo/recorrente, página de entrada e tipo de conteúdo. As metas devem ser definidas após duas a quatro semanas de linha de base; não é recomendável inventar metas de audiência ou conversão sem histórico próprio.

## Referências

[1]: https://developers.google.com/search/docs/fundamentals/seo-starter-guide "Google Search Central — SEO Starter Guide"

[2]: https://developers.google.com/search/docs/appearance/google-images "Google Search Central — Google image SEO best practices"

[3]: https://web.dev/articles/optimize-lcp "web.dev — Optimize Largest Contentful Paint"

[4]: https://web.dev/articles/top-cwv "web.dev — The most effective ways to improve Core Web Vitals"

[5]: https://developers.google.com/search/docs/appearance/structured-data/event "Google Search Central — Event structured data"

[6]: https://www.w3.org/WAI/alt/ "W3C WAI — Resources on Alternative Text for Images"

[7]: https://radiobitcoin.org/ "Rádio Bitcoin — homepage pública auditada"
