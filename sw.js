const CACHE = 'bitadict-v1';
const SHELL = [
  '/',
  '/index.html',
  '/logo-radio.png',
  '/logo_btc.png',
  '/manifest.json'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // Nunca interceptar áudio, streams externos, APIs de preço ou dados dinâmicos
  if (
    e.request.url.includes('192.168.1.64') ||
    e.request.url.includes('binance') ||
    e.request.url.includes('allorigins') ||
    e.request.url.includes('youtube') ||
    e.request.url.includes('googleapis') ||
    e.request.url.includes('polymarket') ||
    /\.(mp3|mp4|m4a|ogg|wav)$/.test(url.pathname) ||
    /\.(json)(\?.*)?$/.test(url.pathname + url.search)
  ) {
    return; // deixa o browser lidar diretamente (sem cache)
  }

  // Cache-first para assets locais (imagens, html, js)
  e.respondWith(
    caches.match(e.request).then(cached => {
      if (cached) return cached;
      return fetch(e.request).then(res => {
        if (res && res.status === 200 && res.type === 'basic') {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
        }
        return res;
      }).catch(() => caches.match('/index.html'));
    })
  );
});
