/*!
 * BIT ADICT · currency switcher
 * Detecta país via Cloudflare CDN headers (geo-IP grátis), define moeda preferida.
 * Não bloqueia render — roda async e atualiza UI quando chega.
 * Fallback: mostra ambos (€/$). Manual override via localStorage('rb_currency').
 */
(function(){
  'use strict';

  // Países que pagam em USD
  const USD_COUNTRIES = new Set([
    'US','CA','MX','BR','AR','CL','CO','PE','UY','VE','EC','BO','PY',  // Américas
    'AU','NZ','SG','HK','TW','PH','MY','TH','VN','ID',  // Ásia-Pacífico
    'AE','SA','QA','KW','BH','OM','IL','TR',  // Oriente Médio
    'ZA','NG','EG','KE',  // África
    'IN','JP','KR'  // Ásia
  ]);

  // Países da zona EUR (preferem €)
  const EUR_COUNTRIES = new Set([
    'PT','ES','FR','DE','IT','NL','BE','LU','IE','AT','GR','FI','EE','LV','LT',
    'SK','SI','MT','CY','HR','CH','GB','NO','SE','DK','PL','CZ','HU','RO','BG'
  ]);

  function applyCurrency(curr) {
    document.documentElement.setAttribute('data-currency', curr);
    document.querySelectorAll('[data-price-eur][data-price-usd]').forEach(el => {
      const eur = el.getAttribute('data-price-eur');
      const usd = el.getAttribute('data-price-usd');
      const suffix = el.getAttribute('data-price-suffix') || '';
      if (curr === 'EUR')      el.innerHTML = '€' + eur + suffix;
      else if (curr === 'USD') el.innerHTML = '$' + usd + suffix;
      else                     el.innerHTML = '€' + eur + ' / $' + usd + suffix;
    });

    // Atualiza badges de moeda (quem clicou)
    document.querySelectorAll('[data-curr-badge]').forEach(b => {
      b.classList.toggle('active', b.getAttribute('data-curr-badge') === curr);
    });
  }

  function detectFromCloudflare(callback) {
    // Cloudflare expõe CF-IPCountry no header de resposta — pegamos via tiny endpoint
    fetch('https://www.cloudflare.com/cdn-cgi/trace', {cache:'no-store'})
      .then(r => r.text())
      .then(t => {
        const m = t.match(/loc=([A-Z]{2})/);
        callback(m ? m[1] : null);
      })
      .catch(() => callback(null));
  }

  function pickCurrency(country) {
    if (!country) return 'BOTH';
    if (USD_COUNTRIES.has(country)) return 'USD';
    if (EUR_COUNTRIES.has(country)) return 'EUR';
    return 'BOTH';
  }

  // 1) Override manual via localStorage (usuário clicou no badge)
  const saved = localStorage.getItem('rb_currency');
  if (saved && ['EUR','USD','BOTH'].includes(saved)) {
    applyCurrency(saved);
  } else {
    // 2) Auto-detecta via Cloudflare
    applyCurrency('BOTH');  // render rápido com ambos
    detectFromCloudflare(country => {
      const curr = pickCurrency(country);
      applyCurrency(curr);
    });
  }

  // 3) Botões manuais (badge no header)
  window.rbSetCurrency = function(curr) {
    localStorage.setItem('rb_currency', curr);
    applyCurrency(curr);
  };
})();
