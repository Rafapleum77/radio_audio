/*!
 * BIT ADICT · currency switcher · 3 moedas (EUR, USD, BRL)
 * Detecta país via Cloudflare CDN headers, define moeda preferida.
 * Override manual: rbSetCurrency('EUR'|'USD'|'BRL'|'ALL')
 */
(function(){
  'use strict';

  const BRL_COUNTRIES = new Set(['BR']);
  const USD_COUNTRIES = new Set([
    'US','CA','MX','AR','CL','CO','PE','UY','VE','EC','BO','PY',
    'AU','NZ','SG','HK','TW','PH','MY','TH','VN','ID',
    'AE','SA','QA','KW','BH','OM','IL','TR',
    'ZA','NG','EG','KE','IN','JP','KR'
  ]);
  const EUR_COUNTRIES = new Set([
    'PT','ES','FR','DE','IT','NL','BE','LU','IE','AT','GR','FI','EE','LV','LT',
    'SK','SI','MT','CY','HR','CH','GB','NO','SE','DK','PL','CZ','HU','RO','BG'
  ]);

  function fmtBRL(n) { return 'R$' + n.toLocaleString('pt-BR'); }

  function applyCurrency(curr) {
    document.documentElement.setAttribute('data-currency', curr);
    document.querySelectorAll('[data-price-eur], [data-price-usd], [data-price-brl]').forEach(el => {
      const eur = el.getAttribute('data-price-eur');
      const usd = el.getAttribute('data-price-usd');
      const brl = el.getAttribute('data-price-brl');
      const suffix = el.getAttribute('data-price-suffix') || '';
      let html = '';
      if (curr === 'EUR' && eur)      html = '€' + eur;
      else if (curr === 'USD' && usd) html = '$' + usd;
      else if (curr === 'BRL' && brl) html = fmtBRL(parseInt(brl));
      else {
        const parts = [];
        if (eur) parts.push('€' + eur);
        if (usd) parts.push('$' + usd);
        if (brl) parts.push(fmtBRL(parseInt(brl)));
        html = parts.join(' / ');
      }
      el.innerHTML = html + suffix;
    });
    document.querySelectorAll('[data-curr-badge]').forEach(b => {
      b.classList.toggle('active', b.getAttribute('data-curr-badge') === curr);
    });
  }

  function detectFromCloudflare(callback) {
    fetch('https://www.cloudflare.com/cdn-cgi/trace', {cache:'no-store'})
      .then(r => r.text())
      .then(t => {
        const m = t.match(/loc=([A-Z]{2})/);
        callback(m ? m[1] : null);
      })
      .catch(() => callback(null));
  }

  function pickCurrency(country) {
    if (!country) return 'ALL';
    if (BRL_COUNTRIES.has(country)) return 'BRL';
    if (USD_COUNTRIES.has(country)) return 'USD';
    if (EUR_COUNTRIES.has(country)) return 'EUR';
    return 'ALL';
  }

  const saved = localStorage.getItem('rb_currency');
  if (saved && ['EUR','USD','BRL','ALL','BOTH'].includes(saved)) {
    applyCurrency(saved === 'BOTH' ? 'ALL' : saved);
  } else {
    applyCurrency('ALL');
    detectFromCloudflare(country => {
      const curr = pickCurrency(country);
      applyCurrency(curr);
    });
  }

  window.rbSetCurrency = function(curr) {
    localStorage.setItem('rb_currency', curr);
    applyCurrency(curr);
  };
})();
