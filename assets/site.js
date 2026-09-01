(function(){
  // Backend Flask local exposto via Cloudflare Tunnel
  const RB_API = 'https://radio.radiobitcoin.org';

  // 4 locutores neste bloco do topo (Gemini fica no bloco existente)
  const LOCUTORES = [
    { id:'manus',  nome:'Manus',  modelo:'Llama 3.1:8b' },
    { id:'grok',   nome:'Grok',   modelo:'Auditor Sarcastico' },
    { id:'claude', nome:'Claude', modelo:'Llama 3.1:8b' },
    { id:'gpt',    nome:'GPT',    modelo:'radiobot' },
  ];

  const elPoly  = document.getElementById('rb-poly-list');
  const elGrid  = document.getElementById('rb-loc-grid');
  const elPill  = document.getElementById('rb-noar-pill');

  function pct(n, total) { return total > 0 ? Math.round((n/total)*100) : 0; }
  function esc(s){ return String(s||'').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

  // ---------------- POLYMARKET ----------------
  async function loadPoly() {
    try {
      const r = await fetch(`${RB_API}/api/polymarket/btc`, { cache: 'no-store' });
      const j = await r.json();
      const items = (j.questions || []).slice(0, 4);
      if (!items.length) { elPoly.innerHTML = '<div class="rb-loading">Sem mercados ativos</div>'; return; }
      elPoly.innerHTML = items.map(q => `
        <div class="rb-poly__item">
          <div class="rb-poly__q">${esc(q.pergunta)}</div>
          <div class="rb-poly__labels">
            <div class="rb-poly__label-grp">
              <span class="rb-poly__label-txt">▲ SIM</span>
              <span class="rb-poly__label-pct up">${q.up}%</span>
            </div>
            <div class="rb-poly__label-grp" style="text-align:right">
              <span class="rb-poly__label-txt">▼ NÃO</span>
              <span class="rb-poly__label-pct down">${q.down}%</span>
            </div>
          </div>
          <div class="rb-poly__bar">
            <div class="rb-poly__up"   style="width:${q.up}%"></div>
            <div class="rb-poly__down" style="width:${q.down}%"></div>
          </div>
        </div>
      `).join('');
    } catch(e) {
      elPoly.innerHTML = '<div class="rb-loading">Erro ao carregar mercados</div>';
    }
  }

  // ---------------- LOCUTORES ----------------
  async function loadLocutores() {
    try {
      const r = await fetch(`${RB_API}/placar`, { cache: 'no-store' });
      const j = await r.json();
      const total = j.total || 0;
      const noAr  = j.no_ar || null;

      // Pill "NO AR" no header
      if (noAr) {
        elPill.textContent = `NO AR · ${noAr.toUpperCase()}`;
        elPill.classList.add('is-live');
        elPill.dataset.id = noAr;
      } else {
        elPill.textContent = '—'; elPill.classList.remove('is-live'); delete elPill.dataset.id;
      }

      elGrid.innerHTML = LOCUTORES.map(loc => {
        const v = (j.votos && j.votos[loc.id]) || 0;
        const p = pct(v, total);
        const live = noAr === loc.id;
        return `
          <div class="rb-loc ${live?'is-live':''}" data-id="${loc.id}">
            <div class="rb-loc__nome">${loc.nome}</div>
            <div class="rb-loc__model">${esc(loc.modelo)}</div>
            <div class="rb-loc__row">
              <span class="rb-loc__votos">${v}</span>
              <span class="rb-loc__pct">VOTOS · ${p}%</span>
            </div>
            <div class="rb-loc__bar"><div class="rb-loc__fill" style="width:${p}%"></div></div>
            <button class="rb-loc__btn" onclick="rbVotar('${loc.id}', this)">&gt; Votar</button>
          </div>
        `;
      }).join('');
    } catch(e) {
      elGrid.innerHTML = '<div class="rb-loading">Erro ao carregar locutores</div>';
    }
  }

  // ---------------- LOCUTORES IA 24H ----------------
  function rvzUpdateClock() {
    const el = document.getElementById('rvz-clock');
    if (!el) return;
    const n = new Date();
    el.textContent = `${String(n.getHours()).padStart(2,'0')}:${String(n.getMinutes()).padStart(2,'0')}:${String(n.getSeconds()).padStart(2,'0')}`;
  }

  function rvzUpdateStatus() {
    const h = new Date().getHours();
    let active = 'grok';
    if (h >= 0  && h < 6)  active = 'gpt';
    else if (h >= 6  && h < 12) active = 'claude';
    else if (h >= 12 && h < 18) active = 'gpt';
    else if (h >= 18 && h < 21) active = 'gemini';

    ['gpt','claude','gemini','grok'].forEach(ia => {
      const card = document.getElementById(`rvz-card-${ia}`);
      if (!card) return;
      card.className = `rvz-locutor-card ${ia === active ? 'active' : 'standby'}`;
      const badge = card.querySelector('.rvz-status-badge');
      if (badge) {
        badge.className = `rvz-status-badge rvz-status-${ia === active ? 'online' : 'standby'}`;
        badge.textContent = ia === active ? '● ONLINE' : '● STANDBY';
      }
    });

    const slotMap = {
      'rvz-slot-0006': h >= 0  && h < 6,
      'rvz-slot-0612': h >= 6  && h < 12,
      'rvz-slot-1218': h >= 12 && h < 18,
      'rvz-slot-1821': h >= 18 && h < 21,
      'rvz-slot-2100': h >= 21
    };
    Object.entries(slotMap).forEach(([id, isCurrent]) => {
      const slot = document.getElementById(id);
      if (slot) slot.classList.toggle('current', isCurrent);
    });
  }

  setInterval(rvzUpdateClock, 1000);
  setInterval(rvzUpdateStatus, 60000);
  rvzUpdateClock();

  // ---------------- CLIQUE NO LOCUTOR → TOCA A LOCUÇÃO FALADA ----------------
  // Cada locutor tem um MP3 de fala gerado por IA (radiobot + edge-tts) em
  // /locucoes/<ia>.mp3, atualizado de hora em hora com preço BTC ao vivo.
  // Ao clicar: pausa a música, toca a locução, mostra o texto, e ao terminar
  // volta a música automaticamente.
  (function rvzLocucao(){
    const ids = ['gpt','claude','gemini','grok'];
    let manifest = {};
    let locAudio = new Audio();
    let falando = false;

    // Carrega o manifesto das locuções
    fetch('locucoes/manifest.json?t=' + Date.now())
      .then(function(r){ return r.ok ? r.json() : {}; })
      .then(function(m){ manifest = m || {}; })
      .catch(function(){});

    function pararMusica(){
      const a = document.getElementById('audioEl');
      window._musWasPlaying = !!(a && !a.paused);
      if (window._musWasPlaying) { try { if(typeof pauseTrack==='function') pauseTrack(); else a.pause(); } catch(e){} }
    }
    function voltarMusica(){
      if(!window._musWasPlaying) return;
      try {
        const a = document.getElementById('audioEl');
        if (a) { if (typeof playTrack==='function') playTrack(); else a.play().catch(function(){}); }
      } catch(e){}
    }

    function mostrarTexto(ia){
      const info = manifest[ia];
      let box = document.getElementById('rvz-locucao-box');
      if (!box) return;
      if (info && info.texto) {
        box.innerHTML = '<strong style="color:#00ff88;">🎙 ' + (info.nome||ia) +
          ' está no ar:</strong><br>' + info.texto;
        box.style.display = 'block';
      }
    }

    function bindCards(){
    ids.forEach(function(ia){
      const card = document.getElementById('rvz-card-'+ia);
      if(!card || card._rvzBound) return;
      card._rvzBound = true;
      card.style.cursor = 'pointer';
      card.title = 'Clique para ouvir a locução de ' + ia.toUpperCase();
      card.addEventListener('click', function(){
        try {
          const pp = document.getElementById('player-panel');
          if (pp) pp.scrollIntoView({behavior:'smooth', block:'center'});
          card.style.transition = 'box-shadow .3s';
          card.style.boxShadow = '0 0 24px rgba(0,255,136,.7)';
          setTimeout(function(){ card.style.boxShadow = ''; }, 700);

          // Para qualquer locução em andamento
          if (falando) { locAudio.pause(); falando = false; }

          // Toca a locução falada deste locutor
          pararMusica();
          locAudio = new Audio('locucoes/' + ia + '.mp3?t=' + Date.now());
          locAudio.volume = 1.0;
          falando = true;
          mostrarTexto(ia);
          locAudio.onended = function(){ falando = false; voltarMusica(); };
          locAudio.onerror = function(){
            // Sem locução disponível → cai pra música
            falando = false;
            const box = document.getElementById('rvz-locucao-box');
            if (box){ box.innerHTML = '🎵 Locução indisponível — tocando a playlist da rádio.'; box.style.display='block'; }
            voltarMusica();
          };
          locAudio.play().catch(function(){
            falando = false; voltarMusica();
          });
        } catch(e) { console.warn('rvz locucao', e); }
      });
    });
    }
    // O painel pode carregar DEPOIS deste script (mudou de coluna) —
    // liga os cliques no DOM pronto e re-tenta por garantia.
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', bindCards);
    } else {
      bindCards();
    }
    setTimeout(bindCards, 1500);
    setTimeout(bindCards, 4000);
  })();

  // ---------------- L402 HEALTH ----------------
  (function l402Health() {
    const satsEl = document.getElementById('l402-sats-24h');
    const agentsEl = document.getElementById('l402-agents');
    const uptimeEl = document.getElementById('l402-uptime');
    const statusEl = document.querySelector('.l402-status');
    function check() {
      // Servidor exposto publicamente via cloudflared (l402.radiobitcoin.org).
      // Localhost como fallback pra quando acessado da própria máquina.
      const urls = ['https://l402.radiobitcoin.org/health', 'http://localhost:8402/health'];
      (function tryUrl(i){
        if(i >= urls.length){
          if(statusEl){ statusEl.textContent = 'OFFLINE'; statusEl.style.color='#ff4444'; }
          if(uptimeEl) uptimeEl.textContent = '---';
          return;
        }
        fetch(urls[i], {signal: AbortSignal.timeout(4000)})
          .then(r => r.json())
          .then(() => {
            if(statusEl){ statusEl.textContent = 'ENDPOINT ONLINE · PORT 8402'; statusEl.style.color=''; }
            if(uptimeEl) uptimeEl.textContent = '100%';
          })
          .catch(() => tryUrl(i+1));
      })(0);
    }
    // Simular contadores crescentes (dados reais viriam do server)
    let sats = 1248, calls = 156;
    function tickCounters() {
      sats += Math.floor(Math.random() * 3);
      calls += Math.floor(Math.random() * 2);
      if(satsEl) satsEl.textContent = sats.toLocaleString('pt-BR');
      if(agentsEl) agentsEl.textContent = calls;
    }
    check();
    tickCounters();
    setInterval(check, 30000);
    setInterval(tickCounters, 15000);
  })();
  rvzUpdateStatus();

  // ---------------- TICK ----------------
  function tick() { loadPoly(); }
  tick();
  setInterval(tick, 30000);
})();
;
/* ═══ bloco ═══ */
(function(){
          var _map=null,_markers=[],_allData=[],_curCat='all';
          var _userLat=null,_userLng=null;
          var _modalId=null,_modalName='',_curStar=0,_curOpt=null;
          var _CHECKINS_KEY='btcmap_checkins_v1';
          var _anuncioTxt='';

          /* ─ CHECKINS LOCAL STORAGE ─ */
          function loadCheckins(){try{return JSON.parse(localStorage.getItem(_CHECKINS_KEY)||'{}');}catch(e){return {};}}
          function saveCheckin(id,data){var c=loadCheckins();c[id]=data;localStorage.setItem(_CHECKINS_KEY,JSON.stringify(c));}
          function countCheckins(){return Object.keys(loadCheckins()).length;}
          function updateCheckinCount(){document.getElementById('bm-checkins').textContent=countCheckins();}

          /* ─ MAPA ─ */
          function initMap(lat,lng){
            if(_map)return;
            document.getElementById('btcmap-leaflet').innerHTML='';
            _map=L.map('btcmap-leaflet',{zoomControl:true}).setView([lat,lng],13);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{
              attribution:'© OSM © Carto',subdomains:'abcd',maxZoom:20
            }).addTo(_map);
          }

          /* ─ HELPERS ─ */
          function dist(a,b,c,d){var R=6371,dL=(c-a)*Math.PI/180,dO=(d-b)*Math.PI/180;var x=Math.sin(dL/2)*Math.sin(dL/2)+Math.cos(a*Math.PI/180)*Math.cos(c*Math.PI/180)*Math.sin(dO/2)*Math.sin(dO/2);return R*2*Math.atan2(Math.sqrt(x),Math.sqrt(1-x));}
          function tagStr(t){return JSON.stringify(t||{}).toLowerCase();}
          function isLN(t){return t['payment:lightning']||t['payment:lightning_contactless'];}
          function isWifi(t){return t['internet_access']||t['wifi']||t['internet_access:fee']==='no';}
          function isATM(t){var s=tagStr(t);return s.includes('atm')||t.amenity==='atm';}
          function isApoio(t){return isLN(t)&&isWifi(t);}
          function getEmoji(t){
            if(isATM(t)) return'🏧';
            var s=tagStr(t);
            if(s.includes('cafe')||s.includes('coffee')||s.includes('bakery')) return'☕';
            if(s.includes('restaurant')||s.includes('food')||s.includes('bar')) return'🍽️';
            if(s.includes('hotel')||s.includes('hostel')||s.includes('lodging')) return'🏨';
            if(s.includes('shop')||s.includes('store')||s.includes('boutique')) return'🛍️';
            return'₿';
          }
          function catMatch(t,cat){
            if(cat==='all') return true;
            if(cat==='apoio') return isApoio(t);
            var s=tagStr(t);
            if(cat==='atm') return isATM(t);
            if(cat==='food') return s.includes('cafe')||s.includes('coffee')||s.includes('restaurant')||s.includes('bar')||s.includes('food')||s.includes('bakery');
            if(cat==='hotel') return s.includes('hotel')||s.includes('hostel')||s.includes('lodging');
            if(cat==='shop') return s.includes('shop')||s.includes('store')||s.includes('boutique');
            return true;
          }
          function getIcon(t,id){
            var checkins=loadCheckins();
            var verified=checkins[id]&&checkins[id].opt!=='problema';
            var border=verified?'#f2a900':isApoio(t)?'#a855f7':'#00ff88';
            var glow=verified?'rgba(242,169,0,0.5)':isApoio(t)?'rgba(168,85,247,0.4)':'rgba(0,255,136,0.4)';
            return L.divIcon({
              html:'<div style="background:#050c07;border:2px solid '+border+';border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-size:12px;box-shadow:0 0 8px '+glow+';">'+(verified?'✅':getEmoji(t))+'</div>',
              className:'',iconSize:[28,28],iconAnchor:[14,14]
            });
          }

          /* ─ ANÚNCIO DE VOZ ─ */
          function gerarAnuncio(nearby){
            if(!nearby.length) return;
            var top=nearby[0];
            var c=top.f.osm_json,t=c.tags||{};
            var name=t.name||t['name:pt']||t['name:en']||'um local';
            var distStr=top.d<1?(Math.round(top.d*1000)+' metros'):(top.d.toFixed(1)+' quilômetros');
            var tipo=isATM(t)?'um caixa eletrônico Bitcoin':isWifi(t)&&isLN(t)?'um ponto de apoio com Wi-Fi e Lightning':'um local que aceita Lightning Network';
            _anuncioTxt='Radio Bitcoin informa: A '+distStr+' de você existe '+tipo+': '+name+'. Use o botão Waze ou Maps para chegar lá. Missão Bitcoin — construindo a economia circular.';
            var bar=document.getElementById('bm-voice-bar');
            document.getElementById('bm-voice-text').innerHTML='<b>Radio Bitcoin:</b> A '+distStr+' de você — <b>'+name+'</b> '+(isLN(t)?'⚡ Lightning':'₿')+(isWifi(t)?' 📶 Wi-Fi':'');
            bar.classList.remove('hidden');
          }
          window.bmFalarAnuncio=function(){
            if(!_anuncioTxt||!window.speechSynthesis) return;
            speechSynthesis.cancel();
            var u=new SpeechSynthesisUtterance(_anuncioTxt);
            u.lang='pt-BR';u.rate=1.05;u.pitch=0.92;u.volume=1;
            // tenta voz pt-BR
            var voices=speechSynthesis.getVoices();
            var vBR=voices.find(function(v){return v.lang==='pt-BR';});
            if(vBR) u.voice=vBR;
            speechSynthesis.speak(u);
          };

          /* ─ MARKERS ─ */
          function renderMarkers(){
            if(!_map) return;
            _markers.forEach(function(m){_map.removeLayer(m);});
            _markers=[];
            var filtered=_allData.filter(function(f){var c=f.osm_json;return c&&c.lat&&c.lon&&catMatch(c.tags||{},_curCat);});
            filtered.slice(0,600).forEach(function(f){
              var c=f.osm_json,t=c.tags||{};
              var id=f.id||f.osm_id||(c.lat+''+c.lon);
              var name=t.name||t['name:pt']||t['name:en']||'Local Bitcoin';
              var addr=[t['addr:street'],t['addr:city'],t['addr:country']].filter(Boolean).join(', ');
              var mk=L.marker([c.lat,c.lon],{icon:getIcon(t,id)}).addTo(_map);
              var mapUrl='https://www.google.com/maps/dir/?api=1&destination='+c.lat+','+c.lon;
              var wazeUrl='https://waze.com/ul?ll='+c.lat+','+c.lon+'&navigate=yes';
              var checkins=loadCheckins();var ck=checkins[id];
              mk.bindPopup(
                '<div style="background:#050c07;color:#e5e7eb;font-family:ui-monospace,monospace;min-width:210px;padding:4px;">'+
                '<div style="font-size:12px;font-weight:900;color:#00ff88;margin-bottom:3px;">'+name+'</div>'+
                (addr?'<div style="font-size:8px;color:#6b7280;margin-bottom:5px;">📍 '+addr+'</div>':'')+
                (isLN(t)?'<div style="font-size:8px;color:#00ff88;margin-bottom:2px;">⚡ Lightning Network</div>':'')+
                (isWifi(t)?'<div style="font-size:8px;color:#c084fc;margin-bottom:2px;">📶 Wi-Fi disponível</div>':'')+
                (isApoio(t)?'<div style="font-size:8px;color:#f2a900;font-weight:900;margin-bottom:5px;">🏅 PONTO DE APOIO TURISTA BITCOIN</div>':'')+
                (ck?'<div style="font-size:8px;color:#00ff88;margin-bottom:5px;">✅ Seu check-in: '+ck.opt+'</div>':'')+
                '<div style="display:flex;gap:5px;margin-top:6px;">'+
                '<a href="'+mapUrl+'" target="_blank" style="background:rgba(66,133,244,0.2);color:#60a5fa;border:1px solid rgba(66,133,244,0.35);border-radius:4px;padding:4px 8px;text-decoration:none;font-size:8px;font-weight:700;">🗺️ Maps</a>'+
                '<a href="'+wazeUrl+'" target="_blank" style="background:rgba(0,212,70,0.1);color:#00d446;border:1px solid rgba(0,212,70,0.25);border-radius:4px;padding:4px 8px;text-decoration:none;font-size:8px;font-weight:700;">🚗 Waze</a>'+
                '<span onclick="bmAbrirModal(\''+id+'\',\''+name.replace(/'/g,'')+'\',event)" style="background:rgba(0,255,136,0.1);color:#00ff88;border:1px solid rgba(0,255,136,0.3);border-radius:4px;padding:4px 8px;font-size:8px;font-weight:700;cursor:pointer;">✅ Check-in</span>'+
                '</div></div>',
                {className:'',maxWidth:240}
              );
              _markers.push(mk);
            });
          }

          /* ─ LISTA ─ */
          function renderLista(lat,lng){
            var scored=_allData.map(function(f){
              var c=f.osm_json;if(!c||!c.lat||!c.lon) return null;
              return {f:f,d:dist(lat,lng,c.lat,c.lon)};
            }).filter(Boolean).sort(function(a,b){return a.d-b.d;});

            document.getElementById('bm-nearby').textContent=scored.filter(function(x){return x.d<5;}).length;
            document.getElementById('bm-apoio').textContent=_allData.filter(function(f){var t=f.osm_json&&f.osm_json.tags||{};return isApoio(t);}).length;
            gerarAnuncio(scored.slice(0,3));

            document.getElementById('btcmap-list-wrap').style.display='block';
            var checkins=loadCheckins();
            var el=document.getElementById('btcmap-list');
            el.innerHTML=scored.slice(0,15).map(function(x){
              var c=x.f.osm_json,t=c.tags||{};
              var id=x.f.id||x.f.osm_id||(c.lat+''+c.lon);
              var name=t.name||t['name:pt']||t['name:en']||'Local Bitcoin';
              var addr=[t['addr:street'],t['addr:city']].filter(Boolean).join(', ')||t['addr:country']||'';
              var distStr=x.d<1?(Math.round(x.d*1000)+'m'):(x.d.toFixed(1)+'km');
              var mapUrl='https://www.google.com/maps/dir/?api=1&destination='+c.lat+','+c.lon;
              var wazeUrl='https://waze.com/ul?ll='+c.lat+','+c.lon+'&navigate=yes';
              var ck=checkins[id];
              var nameEsc=name.replace(/'/g,'');
              return '<div class="btcmap-item'+(isApoio(t)?' apoio':'')+'">'+ 
                '<div class="btcmap-item-icon">'+getEmoji(t)+'</div>'+
                '<div class="btcmap-item-body">'+
                  '<div class="btcmap-item-name">'+name+(isApoio(t)?' 🏅':'')+'</div>'+
                  '<div class="btcmap-item-addr">'+distStr+' · '+addr+'</div>'+
                  '<div class="btcmap-item-tags">'+
                    (isLN(t)?'<span class="btcmap-tag ln">⚡ LN</span>':'')+
                    (isATM(t)?'<span class="btcmap-tag atm">🏧 ATM</span>':'<span class="btcmap-tag onchain">₿</span>')+
                    (isWifi(t)?'<span class="btcmap-tag wifi">📶 Wi-Fi</span>':'')+
                    (isApoio(t)?'<span class="btcmap-tag apoio">🏅 APOIO</span>':'')+
                    (ck?'<span class="btcmap-tag checkin">✅ Check-in</span>':'')+
                  '</div>'+
                '</div>'+
                '<div class="btcmap-item-right">'+
                  '<a href="'+mapUrl+'" target="_blank" class="btcmap-navbtn maps">Maps</a>'+
                  '<a href="'+wazeUrl+'" target="_blank" class="btcmap-navbtn waze">Waze</a>'+
                  '<span onclick="bmAbrirModal(\''+id+'\',\''+nameEsc+'\',event)" class="btcmap-navbtn checkin-btn'+(ck?' checked':'')+'">'+( ck?'✅':'⚡ Check-in')+'</span>'+
                '</div>'+
              '</div>';
            }).join('');
          }

          /* ─ LOAD BTCMAP API ─ */
          function loadBTCMap(lat,lng){
            var delta=0.45;
            var url='https://api.btcmap.org/v2/elements?lat_min='+(lat-delta)+'&lon_min='+(lng-delta)+'&lat_max='+(lat+delta)+'&lon_max='+(lng+delta);
            fetch(url).then(function(r){return r.json();}).then(function(data){
              _allData=(data||[]).filter(function(f){return f.osm_json&&f.osm_json.lat&&f.osm_json.lon&&!f['deleted_at'];});
              var ln=_allData.filter(function(f){var t=f.osm_json.tags||{};return isLN(t);}).length;
              document.getElementById('bm-ln').textContent=ln;
              renderMarkers();
              renderLista(lat,lng);
            }).catch(function(e){console.warn('BTCMap API erro:',e);});
          }

          /* ─ MINHA LOC ─ */
          window.bmMinhaLoc=function(){
            if(!navigator.geolocation){alert('Geolocalização não suportada');return;}
            navigator.geolocation.getCurrentPosition(function(pos){
              var lat=pos.coords.latitude,lng=pos.coords.longitude;
              _userLat=lat;_userLng=lng;
              initMap(lat,lng);
              L.marker([lat,lng],{icon:L.divIcon({html:'<div style="background:#f2a900;border:3px solid #fff;border-radius:50%;width:16px;height:16px;box-shadow:0 0 12px rgba(242,169,0,0.8);"></div>',className:'',iconSize:[16,16],iconAnchor:[8,8]})}).addTo(_map).bindPopup('<b style="color:#f2a900;">Você está aqui</b>').openPopup();
              _map.setView([lat,lng],14);
              loadBTCMap(lat,lng);
            },function(){alert('Permita o acesso à localização.');});
          };

          /* ─ FILTRO ─ */
          window.bmFilter=function(btn,cat){
            document.querySelectorAll('.btcmap-filter').forEach(function(b){b.classList.remove('active');});
            btn.classList.add('active');_curCat=cat;renderMarkers();
          };

          /* ─ MODAL CHECK-IN ─ */
          window.bmAbrirModal=function(id,name,e){
            if(e){e.stopPropagation();e.preventDefault();}
            _modalId=id;_modalName=name;_curStar=0;_curOpt=null;
            document.getElementById('bm-modal-name').textContent=name;
            document.querySelectorAll('.btcmap-star').forEach(function(s){s.classList.remove('lit');});
            document.querySelectorAll('.btcmap-checkin-opt').forEach(function(o){o.classList.remove('sel');});
            document.getElementById('bm-modal').classList.add('open');
          };
          window.bmCloseModal=function(){document.getElementById('bm-modal').classList.remove('open');};
          window.bmSelOpt=function(el){
            document.querySelectorAll('.btcmap-checkin-opt').forEach(function(o){o.classList.remove('sel');});
            el.classList.add('sel');_curOpt=el.dataset.v;
          };
          document.getElementById('bm-stars').addEventListener('click',function(e){
            var s=e.target.closest('.btcmap-star');if(!s) return;
            _curStar=parseInt(s.dataset.s);
            document.querySelectorAll('.btcmap-star').forEach(function(x){x.classList.toggle('lit',parseInt(x.dataset.s)<=_curStar);});
          });
          window.bmConfirmCheckin=function(){
            if(!_curOpt){alert('Selecione uma opção.');return;}
            saveCheckin(_modalId,{name:_modalName,opt:_curOpt,stars:_curStar,ts:Date.now()});
            updateCheckinCount();bmCloseModal();
            renderMarkers();
            if(_userLat) renderLista(_userLat,_userLng);
            // voz de confirmação
            if(window.speechSynthesis){
              var u=new SpeechSynthesisUtterance('Check-in confirmado em '+_modalName+'. Obrigado por contribuir com a rede Bitcoin!');
              u.lang='pt-BR';u.rate=1.05;speechSynthesis.speak(u);
            }
          };
          document.getElementById('bm-modal').addEventListener('click',function(e){if(e.target===this) bmCloseModal();});

          /* ─ INIT: São Paulo ─ */
          updateCheckinCount();
          setTimeout(function(){initMap(-23.5505,-46.6333);loadBTCMap(-23.5505,-46.6333);},400);
        })();
;
/* ═══ bloco ═══ */
/* ═══════════════════════════════════════════
   STACKBIT 1248 — JavaScript
   Namespace: stk* (sem conflito com o site)
═══════════════════════════════════════════ */
(function() {
  const STK_BIP39 = ["abandon","ability","able","about","above","absent","absorb","abstract","absurd","abuse","access","accident","account","accuse","achieve","acid","acoustic","acquire","across","act","action","actor","actress","actual","adapt","add","addict","address","adjust","admit","adult","advance","advice","aerobic","afford","afraid","again","age","agent","agree","ahead","aim","air","airport","aisle","alarm","album","alcohol","alert","alien","all","alley","allow","almost","alone","alpha","already","also","alter","always","amateur","amazing","among","amount","amused","analyst","anchor","ancient","anger","angle","angry","animal","ankle","announce","annual","another","answer","antenna","antique","anxiety","any","apart","apology","appear","apple","approve","april","arch","arctic","area","arena","argue","arm","armed","armor","army","around","arrange","arrest","arrive","arrow","art","artefact","artist","artwork","ask","aspect","assault","asset","assist","assume","asthma","athlete","atom","attack","attend","attitude","attract","auction","audit","august","aunt","author","auto","autumn","average","avocado","avoid","awake","aware","away","awesome","awful","awkward","axis","baby","balance","bamboo","banana","banner","bar","barely","bargain","barrel","base","basic","basket","battle","beach","bean","beauty","because","become","beef","before","begin","behave","behind","believe","below","belt","bench","benefit","best","betray","better","between","beyond","bicycle","bid","bike","bind","biology","bird","birth","bitter","black","blade","blame","blanket","blast","bleak","bless","blind","blood","blossom","blouse","blue","blur","blush","board","boat","body","boil","bomb","bone","book","boost","border","boring","borrow","boss","bottom","bounce","box","boy","bracket","brain","brand","brave","bread","breeze","brick","bridge","brief","bright","bring","brisk","broccoli","broken","bronze","broom","brother","brown","brush","bubble","buddy","budget","buffalo","build","bulb","bulk","bullet","bundle","bunker","burden","burger","burst","bus","business","busy","butter","buyer","buzz","cabbage","cabin","cable","cactus","cage","cake","call","calm","camera","camp","can","canal","cancel","candy","cannon","canvas","canyon","capable","capital","captain","car","carbon","card","cargo","carpet","carry","cart","case","cash","casino","castle","casual","cat","catalog","catch","category","cattle","caught","cause","caution","cave","ceiling","celery","cement","census","century","cereal","certain","chair","chalk","champion","change","chaos","chapter","charge","chase","chat","cheap","check","cheese","chef","cherry","chest","chicken","chief","child","chimney","choice","choose","chronic","chuckle","chunk","cigar","cinnamon","circle","citizen","city","civil","claim","clap","clarify","claw","clay","clean","clerk","clever","click","client","cliff","climb","clinic","clip","clock","clog","close","cloth","cloud","clown","club","clump","cluster","clutch","coach","coast","coconut","code","coffee","coil","coin","collect","color","column","combine","come","comfort","comic","common","company","concert","conduct","confirm","congress","connect","consider","control","convince","cook","cool","copper","copy","coral","core","corn","correct","cost","cotton","couch","country","couple","course","cousin","cover","coyote","crack","cradle","craft","cram","crane","crash","crater","crawl","crazy","cream","credit","creek","crew","cricket","crime","crisp","critic","cross","crouch","crowd","crucial","cruel","cruise","crumble","crunch","crush","cry","crystal","cube","culture","cup","cupboard","curious","current","curtain","curve","cushion","custom","cute","cycle","dad","damage","damp","dance","danger","daring","dash","daughter","dawn","day","deal","debate","debris","decade","december","decide","decline","decorate","decrease","deer","defense","define","defy","degree","delay","deliver","demand","demise","denial","dentist","deny","depart","depend","deposit","depth","deputy","derive","describe","desert","design","desk","despair","destroy","detail","detect","develop","device","devote","diagram","dial","diamond","diary","dice","diesel","diet","differ","digital","dignity","dilemma","dinner","dinosaur","direct","dirt","disagree","discover","disease","dish","dismiss","disorder","display","distance","divert","divide","divorce","dizzy","doctor","document","dog","doll","dolphin","domain","donate","donkey","donor","door","dose","double","dove","draft","dragon","drama","drastic","draw","dream","dress","drift","drill","drink","drip","drive","drop","drum","dry","duck","dumb","dune","during","dust","dutch","duty","dwarf","dynamic","eager","eagle","early","earn","earth","easily","east","easy","echo","ecology","edge","edit","educate","effort","egg","eight","either","elbow","elder","electric","elegant","element","elephant","elevator","elite","else","embark","embody","embrace","emerge","emotion","employ","empower","empty","enable","enact","endless","endorse","enemy","energy","enforce","engage","engine","enhance","enjoy","enlist","enough","enrich","enroll","ensure","enter","entire","entry","envelope","episode","equal","equip","erase","erode","erosion","error","erupt","escape","essay","essence","estate","eternal","ethics","evidence","evil","evoke","evolve","exact","example","excess","exchange","excite","exclude","exercise","exhaust","exhibit","exile","exist","exit","exotic","expand","expire","explain","expose","express","extend","extra","eye","fable","face","faculty","faint","faith","fall","false","fame","family","famous","fan","fancy","fantasy","far","fashion","fat","fatal","father","fatigue","fault","favorite","feature","february","federal","fee","feed","feel","feet","fellow","felt","fence","festival","fetch","fever","few","fiber","fiction","field","figure","file","film","filter","final","find","fine","finger","finish","fire","firm","first","fiscal","fish","fit","fitness","fix","flag","flame","flash","flat","flavor","flee","flight","flip","float","flock","floor","flower","fluid","flush","fly","foam","focus","fog","foil","follow","food","foot","force","forest","forget","fork","fortune","forum","forward","fossil","foster","found","fox","fragile","frame","frequent","fresh","friend","fringe","frog","front","frost","frown","frozen","fruit","fuel","fun","funny","furnace","fury","future","gadget","gain","galaxy","gallery","game","gap","garbage","garden","garlic","garment","gas","gasp","gate","gather","gauge","gaze","general","genius","genre","gentle","genuine","gesture","ghost","giant","gift","giggle","ginger","giraffe","girl","give","glad","glance","glare","glass","glide","glimpse","globe","gloom","glory","glove","glow","glue","goat","goddess","gold","good","goose","gorilla","gospel","gossip","govern","gown","grab","grace","grain","grant","grape","grasp","grass","gravity","great","green","grid","grief","grit","grocery","group","grow","grunt","guard","guide","guilt","guitar","gun","gym","habit","hair","half","hammer","hamster","hand","happy","harsh","harvest","hat","have","hawk","hazard","head","health","heart","heavy","hedgehog","height","hello","helmet","help","hen","hero","hidden","high","hill","hint","hip","hire","history","hobby","hockey","hold","hole","holiday","hollow","home","honey","hood","hope","horn","hospital","host","hour","hover","hub","huge","human","humble","humor","hundred","hungry","hunt","hurdle","hurry","hurt","husband","hybrid","ice","icon","ignore","ill","illegal","image","imitate","immense","immune","impact","impose","improve","impulse","inbox","income","increase","index","indicate","indoor","industry","infant","inflict","inform","inhale","inject","inner","innocent","input","inquiry","insane","insect","inside","inspire","install","intact","interest","into","invest","invite","involve","iron","island","isolate","issue","item","ivory","jacket","jaguar","jar","jazz","jealous","jeans","jelly","jewel","job","join","joke","journey","joy","judge","juice","jump","jungle","junior","junk","just","kangaroo","keen","keep","ketchup","key","kick","kid","kingdom","kiss","kit","kitchen","kite","kitten","kiwi","knee","knife","knock","know","lab","lamp","language","laptop","large","later","laugh","laundry","lava","law","lawn","lawsuit","layer","lazy","leader","learn","leave","lecture","left","leg","legal","legend","lemon","lend","length","lens","leopard","lesson","letter","level","liar","liberty","library","license","life","lift","like","limb","lion","liquid","list","little","live","lizard","load","loan","lobster","local","lock","logic","lonely","long","loop","lottery","loud","lounge","love","loyal","lucky","luggage","lumber","lunar","lunch","luxury","mad","magic","magnet","maid","main","mammal","mango","mansion","manual","maple","marble","march","margin","marine","market","marriage","mask","master","match","material","math","matrix","matter","maximum","maze","meadow","mean","medal","media","melody","melt","member","memory","mention","menu","mercy","merge","merit","merry","mesh","message","metal","method","middle","midnight","milk","million","mimic","mind","minimum","minor","minute","miracle","miss","mitten","model","modify","mom","monitor","monkey","monster","month","moon","moral","more","morning","mosquito","mother","motion","motor","mountain","mouse","move","movie","much","muffin","mule","multiply","muscle","museum","mushroom","music","must","mutual","myself","mystery","naive","name","napkin","narrow","nasty","natural","nature","near","neck","need","negative","neglect","neither","nephew","nerve","nest","network","news","next","nice","night","noble","noise","nominee","noodle","normal","north","notable","note","nothing","notice","novel","now","nuclear","number","nurse","nut","oak","obey","object","oblige","obscure","obtain","ocean","october","odor","off","offer","office","often","oil","okay","old","olive","olympic","omit","once","onion","open","opera","oppose","option","orange","orbit","orchard","order","ordinary","organ","orient","original","orphan","ostrich","other","outdoor","outside","oval","over","own","oyster","ozone","pact","paddle","page","pair","palace","palm","panda","panel","panic","panther","paper","parade","parent","park","parrot","party","pass","patch","path","patrol","pause","pave","payment","peace","peanut","peasant","pelican","pen","penalty","pencil","people","pepper","perfect","permit","person","pet","phone","photo","phrase","physical","piano","picnic","picture","piece","pig","pigeon","pill","pilot","pink","pioneer","pipe","pistol","pitch","pizza","place","planet","plastic","plate","play","please","pledge","pluck","plug","plunge","poem","poet","point","polar","pole","police","pond","pony","pool","popular","portion","position","possible","post","potato","pottery","poverty","powder","power","practice","praise","predict","prefer","prepare","present","pretty","prevent","price","pride","primary","print","priority","prison","private","prize","problem","process","produce","profit","program","project","promote","proof","property","prosper","protect","proud","provide","public","pudding","pull","pulp","pulse","pumpkin","punish","pupil","purchase","purity","purpose","push","put","puzzle","pyramid","quality","quantum","quarter","question","quick","quit","quiz","quote","rabbit","raccoon","race","rack","radar","radio","rage","rail","rain","raise","rally","ramp","ranch","random","range","rapid","rare","rate","rather","raven","reach","ready","real","reason","rebel","rebuild","recall","receive","recipe","record","recycle","reduce","reflect","reform","refuse","region","regret","regular","reject","relax","release","relief","rely","remain","remember","remind","remove","render","renew","rent","reopen","repair","repeat","replace","report","require","rescue","resemble","resist","resource","response","result","retire","retreat","return","reunion","reveal","review","reward","rhythm","ribbon","rid","ride","ridge","rifle","right","rigid","ring","riot","ripple","risk","ritual","rival","river","road","roast","robot","robust","rocket","romance","roof","rookie","rose","rotate","rough","royal","rubber","rude","rug","rule","run","runway","rural","sad","saddle","sadness","safe","sail","salad","salmon","salon","salt","salute","same","sample","sand","satisfy","satoshi","sauce","sausage","save","say","scale","scan","scare","scatter","scene","scheme","science","scissors","scorpion","scout","scrap","screen","script","scrub","sea","search","season","seat","second","secret","section","security","seed","seek","segment","select","sell","seminar","senior","sense","sentence","series","service","session","settle","setup","seven","shadow","shaft","shallow","share","shed","shell","sheriff","shield","shift","shine","ship","shiver","shock","shoe","shoot","shop","short","shoulder","shove","shrimp","shrug","shuffle","shy","sibling","siege","sight","sign","silent","silk","silly","silver","similar","simple","since","sing","siren","sister","situate","six","size","sketch","skill","skin","skirt","skull","slab","slam","sleep","slender","slice","slide","slight","slim","slogan","slot","slow","slush","small","smart","smile","smoke","smooth","snack","snake","snap","sniff","snow","soap","soccer","social","sock","solar","soldier","solid","solution","solve","someone","song","soon","sorry","soul","sound","soup","source","south","space","spare","spatial","spawn","speak","special","speed","sphere","spice","spider","spike","spin","spirit","split","spoil","sponsor","spoon","spray","spread","spring","spy","square","squeeze","squirrel","stable","stadium","staff","stage","stairs","stamp","stand","start","state","stay","steak","steel","stem","step","stereo","stick","still","sting","stock","stomach","stone","stop","store","storm","story","stove","strategy","street","strike","strong","struggle","student","stuff","stumble","style","subject","submit","subway","success","such","sudden","suffer","sugar","suggest","suit","summer","sun","sunny","sunset","super","supply","supreme","sure","surface","surge","surprise","sustain","swallow","swamp","swap","swear","sweet","swift","swim","swing","switch","sword","symbol","symptom","syrup","table","tackle","tag","tail","talent","tank","tape","target","task","tattoo","taxi","teach","team","tell","ten","tenant","tennis","tent","term","test","text","thank","that","theme","then","theory","there","they","thing","this","thought","three","thrive","throw","thumb","thunder","ticket","tilt","timber","time","tiny","tip","tired","title","toast","tobacco","today","together","toilet","token","tomato","tomorrow","tone","tongue","tonight","tool","tooth","top","topic","topple","torch","tornado","tortoise","toss","total","tourist","toward","tower","town","toy","track","trade","traffic","tragic","train","transfer","trap","trash","travel","tray","treat","tree","trend","trial","tribe","trick","trigger","trim","trip","trophy","trouble","truck","truly","trumpet","trust","truth","try","tube","tuition","tumble","tuna","tunnel","turkey","turn","turtle","twelve","twenty","twice","twin","twist","two","type","typical","ugly","umbrella","unable","unaware","uncle","uncover","under","undo","unfair","unfold","unhappy","uniform","unique","universe","unknown","unlock","until","unusual","unveil","update","upgrade","uphold","upon","upper","upset","urban","useful","useless","usual","utility","vacant","vacuum","vague","valid","valley","valve","van","vanish","vapor","various","vast","vault","vehicle","velvet","vendor","venture","venue","verb","verify","version","very","veteran","viable","vibrant","vicious","victory","video","view","village","vintage","violin","virtual","virus","visa","visit","visual","vital","vivid","vocal","voice","void","volcano","volume","vote","voyage","wage","wagon","wait","walk","wall","walnut","want","warfare","warm","warrior","waste","water","wave","way","wealth","weapon","wear","weasel","web","wedding","weekend","weird","welcome","well","west","wet","whale","wheat","wheel","when","where","whip","whisper","wide","width","wife","wild","will","win","window","wine","wing","wink","winner","winter","wire","wisdom","wise","wish","witness","wolf","woman","wonder","wood","wool","word","world","worry","worth","wrap","wreck","wrestle","wrist","write","wrong","yard","year","yellow","you","young","youth","zebra","zero","zone","zoo"];

  function stkGetDigits(num){const n=num-1;return[Math.floor(n/1000),Math.floor(n/100)%10,Math.floor(n/10)%10,n%10];}
  function stkDigitToCells(d){const m=[];let r=d;if(r>=8){m.push(8);r-=8;}if(r>=4){m.push(4);r-=4;}if(r>=2){m.push(2);r-=2;}if(r>=1){m.push(1);r-=1;}return m;}

  window.stkTab=function(id,el){
    document.querySelectorAll('.stk-tab-btn').forEach(t=>t.classList.remove('active'));
    document.querySelectorAll('.stk-tab-pane').forEach(t=>t.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('stk-tab-'+id).classList.add('active');
    if(id==='gabarito')stkBuildGab();
    if(id==='lista')stkBuildTable('');
  };
  window.stkSearchWord=function(val){
    document.getElementById('stk-num').value='';
    document.getElementById('stk-suggestions').innerHTML='';
    if(!val.trim()){document.getElementById('stk-result').classList.remove('show');return;}
    const v=val.trim().toLowerCase();
    const idx=STK_BIP39.findIndex(w=>w===v);
    if(idx!==-1){stkShowResult(idx+1,STK_BIP39[idx]);}
    else{
      const parts=STK_BIP39.filter(w=>w.startsWith(v)).slice(0,6);
      if(parts.length){document.getElementById('stk-suggestions').innerHTML=parts.map(w=>`<button class="stk-sug-btn" onclick="stkPickWord('${w}')">${w}</button>`).join('');}
      document.getElementById('stk-result').classList.remove('show');
    }
  };
  window.stkPickWord=function(w){
    document.getElementById('stk-word').value=w;
    document.getElementById('stk-suggestions').innerHTML='';
    stkShowResult(STK_BIP39.indexOf(w)+1,w);
  };
  window.stkSearchNum=function(val){
    document.getElementById('stk-word').value='';
    document.getElementById('stk-suggestions').innerHTML='';
    const n=parseInt(val);
    if(!n||n<1||n>2048){document.getElementById('stk-result').classList.remove('show');return;}
    stkShowResult(n,STK_BIP39[n-1]);
  };
  function stkShowResult(num,word){
    const digits=stkGetDigits(num);
    document.getElementById('stk-res-num').textContent='#'+num;
    document.getElementById('stk-res-word').textContent=word.toUpperCase();
    document.getElementById('stk-res-digits').innerHTML='DÍGITOS: <span>'+digits.join('</span> · <span>')+'</span>';
    stkRenderPunch(digits,'stk-punch-grid','stk-punch-summary');
    document.getElementById('stk-result').classList.add('show');
  }
  function stkRenderPunch(digits,gridId,summaryId){
    const labels=['×1000','×100','×10','×1'];
    const grid=document.getElementById(gridId);
    grid.innerHTML='';
    const summary=[];
    digits.forEach((d,i)=>{
      const marked=stkDigitToCells(d);
      const group=document.createElement('div');
      group.className='stk-punch-group';
      group.innerHTML=`<div class="stk-punch-lbl">${labels[i]}</div>`;
      const cells=document.createElement('div');
      cells.className='stk-punch-cells';
      [1,2,4,8].forEach(v=>{
        const cell=document.createElement('div');
        cell.className='stk-punch-cell'+(marked.includes(v)?' marked':'');
        cell.textContent=v;
        cell.onclick=()=>cell.classList.toggle('marked');
        cells.appendChild(cell);
      });
      group.appendChild(cells);
      const dnum=document.createElement('div');
      dnum.className='stk-punch-digit';
      dnum.textContent=d;
      group.appendChild(dnum);
      grid.appendChild(group);
      summary.push(`D${i+1}=${d}(${marked.length?marked.join('+'):'vazio'})`);
    });
    if(summaryId)document.getElementById(summaryId).textContent='Punção: '+summary.join('  |  ');
  }
  window.stkBuildGab=function(){
    const count=parseInt(document.getElementById('stk-gab-count').value);
    const table=document.getElementById('stk-gab-table');
    table.innerHTML='';
    let header='<thead><tr><th style="min-width:50px;text-align:right;padding-right:6px;">DIG.</th>';
    for(let w=1;w<=count;w++)header+=`<th>W${w}</th>`;
    header+='</tr></thead>';
    table.innerHTML=header;
    const rowLabels=['×1000','×100','×10','×1'];
    const tbody=document.createElement('tbody');
    rowLabels.forEach((label,di)=>{
      const tr=document.createElement('tr');
      const tdLabel=document.createElement('td');
      tdLabel.className='stk-row-lbl';
      tdLabel.textContent=label;
      tr.appendChild(tdLabel);
      for(let w=1;w<=count;w++){
        const td=document.createElement('td');
        td.style.padding='2px';
        const miniGrid=document.createElement('div');
        miniGrid.className='stk-mini-cells';
        [1,2,4,8].forEach(v=>{
          const cell=document.createElement('div');
          cell.className='stk-gab-cell';
          cell.textContent=v;
          cell.onclick=()=>cell.classList.toggle('marked');
          miniGrid.appendChild(cell);
        });
        td.appendChild(miniGrid);
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
  };
  window.stkClearGab=function(){document.querySelectorAll('.stk-gab-cell.marked').forEach(c=>c.classList.remove('marked'));};
  window.stkBuildTable=function(filter){
    const tbody=document.getElementById('stk-table-body');
    const f=filter.toLowerCase();
    let html='';
    STK_BIP39.forEach((w,i)=>{
      const num=i+1;
      if(f&&!w.includes(f)&&!String(num).includes(f))return;
      const digits=stkGetDigits(num);
      html+=`<tr><td>${num}</td><td onclick="stkPickFromTable('${w}')">${w}</td><td>${digits.join('')}</td><td>${digits.join(' · ')}</td></tr>`;
    });
    tbody.innerHTML=html;
  };
  window.stkPickFromTable=function(w){
    document.getElementById('stk-word').value=w;
    stkShowResult(STK_BIP39.indexOf(w)+1,w);
    document.querySelectorAll('.stk-tab-btn').forEach(t=>t.classList.remove('active'));
    document.querySelectorAll('.stk-tab-pane').forEach(t=>t.classList.remove('active'));
    document.querySelectorAll('.stk-tab-btn')[0].classList.add('active');
    document.getElementById('stk-tab-busca').classList.add('active');
  };
  window.stkFilterTable=function(val){stkBuildTable(val);};

  // Init
  stkBuildTable('');
  stkBuildGab();
})();
;
/* ═══ bloco ═══ */
// ===== QUANTUM PULSE HUD v2 — controlador (reusa #liveAudio/#econAudio) =====
(function(){
  var hero=document.getElementById('qpHero'); if(!hero) return;
  var liveAudio=document.getElementById('liveAudio'), econAudio=document.getElementById('econAudio');
  if(!liveAudio||!econAudio) return;
  try{ liveAudio.crossOrigin='anonymous'; }catch(_){}
  var LIVE_URL='https://stream.radiobitcoin.org/radio', BASE='https://radiobitcoin.org/';
  var PLAY='<path d="M8 5v14l11-7z"/>', PAUSE='<path d="M6 5h4v14H6zM14 5h4v14h-4z"/>';
  var CATS={econ:['mercado','fluxo','boletim','economia','austriaca','austríaca','alerta','noticia','notícia'],surv:['sobreviv','clima','prepper','surviv','tempo']};
  var mode=null, connecting=false, tracks=null, queues={econ:null,surv:null}, qidx={econ:0,surv:0};
  var $=function(id){return document.getElementById(id);};
  // grade real p/ AGORA / A SEGUIR / card PROGRAMA
  var GRADE=[['08:30','Radar Coin Bureau'],['09:30','Radar de Ações'],['12:00','As Mais Negociadas'],['16:30','Melhores Oportunidades'],['17:00','Fechamento de Mercado'],['19:00','Radar Coin Bureau'],['21:00','Programa de Lutas']];

  var DIAS=['DOM','SEG','TER','QUA','QUI','SEX','SÁB'], MES=['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'];
  function tick(){ var d=new Date();
    $('qpClock').textContent=[d.getHours(),d.getMinutes(),d.getSeconds()].map(function(n){return String(n).padStart(2,'0');}).join(':');
    var ds=DIAS[d.getDay()]+', '+String(d.getDate()).padStart(2,'0')+' '+MES[d.getMonth()];
    $('qpDate').textContent=ds; $('qpDate2').textContent=ds+' · 24H';
    // AGORA / A SEGUIR
    var mins=d.getHours()*60+d.getMinutes(), cur=null, nxt=null;
    for(var i=0;i<GRADE.length;i++){ var p=GRADE[i].split?null:null; var hm=GRADE[i][0].split(':'); var m=(+hm[0])*60+(+hm[1]);
      if(m<=mins)cur=GRADE[i]; if(m>mins&&!nxt)nxt=GRADE[i]; }
    if(!cur)cur=GRADE[GRADE.length-1]; if(!nxt)nxt=GRADE[0];
    $('qpNow').textContent=(cur?cur[1]+' — '+cur[0].replace(':','h'):'Rádio Bitcoin 24h');
    $('qpNext').textContent=(nxt?nxt[1]+' — '+nxt[0].replace(':','h'):'—');
    if(mode!=='live'&&mode!=='econ'&&mode!=='surv'){ $('qpProg').textContent=(cur?cur[1].split(' ')[0]+' '+cur[0].replace(':','h'):'—'); }
  }
  tick(); setInterval(tick,1000);

  // volume + mute + fade
  var vol=0.85, muted=false, fadeIv=null;
  function applyVol(){ var v=muted?0:vol; try{liveAudio.volume=v;econAudio.volume=v;}catch(_){}}
  function setVolUI(){ var p=(muted?0:vol*100);
    $('qpVolFill').style.width=p+'%'; $('qpVolThumb').style.left=p+'%'; $('qpVolTip').style.left=p+'%'; $('qpVolTip').textContent=Math.round(p)+'%';
    $('qpPct').textContent=Math.round(p)+'%';
    $('qpMuteIco').innerHTML=muted?'<path d="M11 5 6 9H2v6h4l5 4z"/><line x1="22" y1="9" x2="16" y2="15"/><line x1="16" y1="9" x2="22" y2="15"/>':'<path d="M11 5 6 9H2v6h4l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/><path d="M19 5a10 10 0 0 1 0 14"/>'; }
  var slider=$('qpVol'); var sv=parseFloat(localStorage.getItem('qpxVol')); if(!isNaN(sv)){vol=sv;slider.value=Math.round(sv*100);}
  applyVol(); setVolUI();
  slider.addEventListener('input',function(){ vol=slider.value/100; if(muted&&vol>0)muted=false; applyVol(); setVolUI(); $('qpVolWrap').classList.add('act'); try{localStorage.setItem('qpxVol',vol);}catch(_){} });
  slider.addEventListener('change',function(){ setTimeout(function(){$('qpVolWrap').classList.remove('act');},900); });
  $('qpMute').addEventListener('click',function(){ muted=!muted; applyVol(); setVolUI(); });
  function fadeIn(a){ if(fadeIv){clearInterval(fadeIv);fadeIv=null;} var t=muted?0:vol; if(!(t>0))return; try{a.volume=0;}catch(_){return;} var k=0,st=40;
    fadeIv=setInterval(function(){ k++; var v=t*(k/st); try{a.volume=v>=t?t:v;}catch(_){clearInterval(fadeIv);return;} if(k>=st)clearInterval(fadeIv); },60); }

  function setBtn(id,p){ var s=document.querySelector('#'+id+' svg'); if(s)s.innerHTML=p?PAUSE:PLAY; }
  function cap(m){return 'row'+m.charAt(0).toUpperCase()+m.slice(1);}
  function render(){
    ['live','econ','surv'].forEach(function(m){ var r=$(cap(m)); r.classList.toggle('on',mode===m&&!connecting); r.classList.toggle('connecting',mode===m&&connecting); setBtn('btn'+m.charAt(0).toUpperCase()+m.slice(1),mode===m&&!connecting); });
    hero.classList.toggle('playing',!!mode&&!connecting); hero.classList.toggle('connecting',connecting);
    hero.classList.toggle('live-on',mode==='live'&&!connecting); hero.classList.toggle('econ-on',mode==='econ'&&!connecting); hero.classList.toggle('surv-on',mode==='surv'&&!connecting);
    $('qpLiveLbl').textContent=connecting?'CONECTANDO':(mode==='live'?'AO VIVO':'24H NO AR');
    $('liveStatus').innerHTML=(connecting&&mode==='live')?'CONECTANDO…':(mode==='live'?'❚❚ TOCANDO — toque para pausar':'▶ OUVIR AO VIVO');
    $('liveTi').textContent=mode==='live'?'Transmissão ao vivo':'Rádio Bitcoin 24h';
    $('liveSu').textContent=mode==='live'?'stream.radiobitcoin.org · 128kbps':'Toque para iniciar o stream';
    $('econStatus').innerHTML=(connecting&&mode==='econ')?'CONECTANDO…':(mode==='econ'?'❚❚ TOCANDO — toque para pausar':'BOLETINS DE ECONOMIA');
    $('survStatus').innerHTML=(connecting&&mode==='surv')?'CONECTANDO…':(mode==='surv'?'❚❚ TOCANDO — toque para pausar':'BOLETINS DE SOBREVIVÊNCIA');
    var st=$('qpStatus'),sts=$('qpStatusSub'),stc=$('qpStatusCard'),md=$('qpMode'),mds=$('qpModeSub');
    var cst=$('qpChipStatus'),cstx=$('qpChipStatusTxt');
    if(mode==='live'&&!connecting){st.textContent='ON AIR';st.style.color='var(--red)';sts.textContent='Transmissão ativa';stc.style.setProperty('--rc','var(--red)');stc.classList.add('on');md.textContent='LIVE';md.style.color='var(--cyan)';mds.textContent='Stream 24h';cstx.textContent='ON AIR';cst.querySelector('.cd').style.background='var(--red)';}
    else if(mode==='econ'&&!connecting){st.textContent='ECON';st.style.color='var(--amber)';sts.textContent='Boletins IA';stc.classList.add('on');stc.style.setProperty('--rc','var(--amber)');md.textContent='ECON';md.style.color='var(--amber)';mds.textContent='Boletins IA';cstx.textContent='ECON';cst.querySelector('.cd').style.background='var(--amber)';}
    else if(mode==='surv'&&!connecting){st.textContent='SURV';st.style.color='var(--green)';sts.textContent='Preparo & clima';stc.classList.add('on');stc.style.setProperty('--rc','var(--green)');md.textContent='SURV';md.style.color='var(--green)';mds.textContent='Preparo & clima';cstx.textContent='SURV';cst.querySelector('.cd').style.background='var(--green)';}
    else if(connecting){st.textContent='...';st.style.color='var(--amber)';sts.textContent='Conectando';md.textContent=(mode||'').toUpperCase()||'…';md.style.color='var(--amber)';cstx.textContent='CONECTANDO';cst.querySelector('.cd').style.background='var(--amber)';}
    else{st.textContent='NO AR';st.style.color='var(--green)';sts.textContent='Toque para ouvir';stc.classList.remove('on');md.textContent='IDLE';md.style.color='var(--qdim)';mds.textContent='—';cstx.textContent='STANDBY';cst.querySelector('.cd').style.background='var(--qdim)';}
  }

  var connTimer=null;
  function startConn(m){ connecting=true; render(); if(connTimer)clearTimeout(connTimer); connTimer=setTimeout(function(){ if(connecting){connecting=false; if(mode===m){mode=null;} render();} },12000); }
  function onPlaying(){ if(connecting){connecting=false; if(connTimer)clearTimeout(connTimer); render();} }
  liveAudio.addEventListener('playing',onPlaying); econAudio.addEventListener('playing',onPlaying);

  function playLive(){ if(mode==='live'&&!connecting){ liveAudio.pause(); mode=null; render(); return; }
    mode='live'; startConn('live'); if(liveAudio.src!==LIVE_URL)liveAudio.src=LIVE_URL; liveAudio.load(); liveAudio.play().then(function(){fadeIn(liveAudio);}).catch(function(){ connecting=false; mode=null; render(); }); }
  function loadTracks(){ if(tracks)return Promise.resolve(tracks); return fetch(BASE+'tracks.json',{cache:'no-store'}).then(function(r){return r.json();}).then(function(t){tracks=t||[];return tracks;}); }
  function matches(cat,list){cat=(cat||'').toLowerCase();return list.some(function(c){return cat.indexOf(c)>=0;});}
  function playThemed(m){ if(mode===m&&!connecting){ econAudio.pause(); mode=null; render(); return; }
    mode=m; startConn(m); $(m+'Su').textContent='Carregando boletins…';
    loadTracks().then(function(){ if(!queues[m])queues[m]=tracks.filter(function(t){return t&&t.file&&matches(t.category,CATS[m]);});
      if(!queues[m].length){ $(m+'Su').textContent='Nenhum boletim disponível agora.'; connecting=false; mode=null; render(); return; } playBoletim(m);
    }).catch(function(){ $(m+'Su').textContent='Erro ao carregar.'; connecting=false; mode=null; render(); }); }
  function playBoletim(m){ var q=queues[m]; if(!q||!q.length)return; var t=q[qidx[m]%q.length];
    econAudio.src=(t.file.indexOf('http')===0?t.file:BASE+t.file); econAudio.play().then(function(){fadeIn(econAudio);
      $(m+'Ti').textContent=t.title||'Boletim'; $(m+'Su').textContent=t.title||t.file; $(m+'Li').textContent='Boletim '+((qidx[m]%q.length)+1)+' de '+q.length;
    }).catch(function(){ $(m+'Su').textContent='Erro ao reproduzir.'; connecting=false; render(); }); }
  econAudio.addEventListener('ended',function(){ if(mode==='econ'||mode==='surv'){ qidx[mode]=(qidx[mode]+1)%((queues[mode]||[]).length||1); playBoletim(mode);} });

  $('btnLive').addEventListener('click',playLive);
  $('btnEcon').addEventListener('click',function(){playThemed('econ');});
  $('btnSurv').addEventListener('click',function(){playThemed('surv');});
  $('econSkip').addEventListener('click',function(){ if(mode==='econ'){qidx.econ=(qidx.econ+1)%((queues.econ||[]).length||1);playBoletim('econ');} });
  $('survSkip').addEventListener('click',function(){ if(mode==='surv'){qidx.surv=(qidx.surv+1)%((queues.surv||[]).length||1);playBoletim('surv');} });

  // share -> copia link + toast + checkmark
  var CHK='<polyline points="20 6 9 17 4 12"/>', SH='<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.6" y1="13.5" x2="15.4" y2="17.5"/><line x1="15.4" y1="6.5" x2="8.6" y2="10.5"/>';
  $('qpShareBtn').addEventListener('click',function(){ var url='https://radiobitcoin.org', txt='📻 Rádio Bitcoin — 24h ao vivo, soberana e sem censura. Ouça: ';
    function toast(){ var b=$('qpShareBtn'); b.classList.add('done'); $('qpShareIco').innerHTML=CHK; var t=$('qpToast'); t.classList.add('show');
      setTimeout(function(){ t.classList.remove('show'); b.classList.remove('done'); $('qpShareIco').innerHTML=SH; },2200); }
    try{ if(navigator.clipboard&&navigator.clipboard.writeText){ navigator.clipboard.writeText(txt+url).catch(function(){}); } else if(navigator.share){ navigator.share({title:'Rádio Bitcoin',text:txt,url:url}).catch(function(){}); } }catch(_){}
    toast(); /* DeLorean menu segue disponível abaixo */
  });

  // EQ
  var eqEl=$('qpEq'), BARS=48, bars=[], vals=new Array(BARS).fill(0);
  for(var i=0;i<BARS;i++){var b=document.createElement('i');eqEl.appendChild(b);bars.push(b);}
  function frame(){ var playing=(!!mode&&!connecting); var amberCol=mode==='surv'?'#22c55e':'#f59e0b';
    for(var i=0;i<BARS;i++){ var t; if(!playing)t=0.05; else{ var base=Math.sin(Date.now()/300+i*0.5)*0.5+0.5; t=Math.min(1,(base*0.5+Math.random()*0.6)); }
      vals[i]+=(t-vals[i])*0.35; bars[i].style.height=(6+vals[i]*40)+'px'; bars[i].style.opacity=0.35+vals[i]*0.65; bars[i].style.background=(i/BARS>0.62)?amberCol:'#00d4ff'; }
    requestAnimationFrame(frame); }
  requestAnimationFrame(frame);

  // telemetria (+ chips)
  function fmt(n){return Number(n).toLocaleString('en-US');}
  function telem(){
    fetch('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT').then(function(r){return r.json();}).then(function(d){ if(d&&d.price){var s='$'+fmt(Math.round(d.price)); $('qpBtc').textContent=s; $('qpChipBtc').textContent=s;} }).catch(function(){});
    fetch('https://mempool.space/api/blocks/tip/height').then(function(r){return r.text();}).then(function(t){ if(t){var s=fmt(parseInt(t,10)); $('qpBlock').textContent=s; $('qpChipBlk').textContent='Bloco '+s;} }).catch(function(){});
  }
  telem(); setInterval(telem,45000);
  var lis=0; setInterval(function(){ var el=$('qpListeners'), ch=$('qpChipLis');
    if(mode==='live'&&!connecting){ if(!lis)lis=10+Math.floor(Math.random()*30); else lis=Math.max(1,lis+(Math.floor(Math.random()*5)-2)); el.textContent=String(lis); el.style.color='var(--cyan)'; ch.textContent=lis+' ouvintes'; $('liveLi').textContent='● '+lis+' ouvintes conectados'; }
    else{ lis=0; el.textContent='—'; el.style.color='var(--qdim)'; ch.textContent='— ouvintes'; $('liveLi').textContent=''; } },4000);

  document.addEventListener('keydown',function(e){ var tag=(e.target&&e.target.tagName||'').toLowerCase(); if(tag==='input'||tag==='textarea')return;
    if(e.code==='Space'){e.preventDefault(); mode&&!connecting?(mode==='live'?playLive():playThemed(mode)):playLive();} else if(e.key==='1')playLive(); else if(e.key==='2')playThemed('econ'); else if(e.key==='3')playThemed('surv'); });

  render();
})();