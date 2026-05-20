/*
 * widgets/include.js — helper pra carregar widgets HTML dinamicamente
 *
 * USO em qualquer pagina:
 *   <div data-widget="nav"></div>
 *   <div data-widget="social"></div>
 *   <div data-widget="mini-carteira"></div>
 *   <div data-widget="cta-sticky-mobile"></div>
 *   <script src="/widgets/include.js" defer></script>
 *
 * O script:
 *   - encontra todo <div data-widget="X">
 *   - faz fetch('/widgets/X.html')
 *   - substitui o div pelo HTML do widget (executa <script> inline)
 *
 * Cache: cada widget eh fetchado uma vez por sessao do browser.
 */
(function() {
  const cache = {};

  async function loadOne(name) {
    if (cache[name]) return cache[name];
    const r = await fetch(`/widgets/${name}.html`, { cache: 'default' });
    if (!r.ok) throw new Error(`widget ${name}: HTTP ${r.status}`);
    cache[name] = await r.text();
    return cache[name];
  }

  function executeInlineScripts(host) {
    // <script> inseridos via innerHTML nao executam — precisa recriar
    host.querySelectorAll('script').forEach(old => {
      const s = document.createElement('script');
      [...old.attributes].forEach(a => s.setAttribute(a.name, a.value));
      s.textContent = old.textContent;
      old.parentNode.replaceChild(s, old);
    });
  }

  async function loadAll() {
    const holders = document.querySelectorAll('[data-widget]');
    for (const el of holders) {
      const name = el.getAttribute('data-widget');
      try {
        const html = await loadOne(name);
        const wrapper = document.createElement('div');
        wrapper.innerHTML = html;
        // move children pra parent do placeholder (sem div extra)
        const frag = document.createDocumentFragment();
        while (wrapper.firstChild) frag.appendChild(wrapper.firstChild);
        el.parentNode.replaceChild(frag, el);
      } catch (e) {
        console.warn(`widget load fail '${name}':`, e);
        el.innerHTML = `<!-- widget ${name} unavailable -->`;
      }
    }
    // re-executa scripts inline do documento todo
    executeInlineScripts(document.body);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadAll);
  } else {
    loadAll();
  }
})();
