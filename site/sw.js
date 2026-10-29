/* App-shell cache. Audio is never cached here: it is huge and uses Range requests. (deployed from git) */
const V = 'radioport-v17';
const SHELL = ['./', 'index.html', 'stats.html', 'style.css?v=12', 'app.js?v=20', 'fx.js?v=7', 'data/tracks.js?v=9', 'data/dj.js?v=7', 'manifest.webmanifest',
  'fonts/blenderpro-book.ttf', 'fonts/blenderpro-bold.ttf', 'fonts/raj-medium.ttf', 'fonts/raj-bold.ttf'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(V).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== V).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin || u.pathname.includes('/audio/') || e.request.headers.has('range')) return;
  // network first so updates land immediately; cache is the offline fallback
  e.respondWith(fetch(e.request).then((r) => {
    if (r.ok) { const copy = r.clone(); caches.open(V).then((c) => c.put(e.request, copy)); }
    return r;
  }).catch(() => caches.match(e.request, { ignoreSearch: true })));
});
