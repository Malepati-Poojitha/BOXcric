const CACHE_NAME = 'boxcric-v20';
const STATIC_ASSETS = [
  '/static/css/style.css',
  '/static/js/app.js',
  '/static/manifest.json'
];

// Install: cache static shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// Fetch: network-first, only cache static assets (never cache HTML/API)
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Skip WebSocket and non-GET requests
  if (url.protocol === 'ws:' || url.protocol === 'wss:') return;
  if (event.request.method !== 'GET') return;

  // Never cache HTML pages or API responses (they contain user-specific data)
  const isStaticAsset = url.pathname.startsWith('/static/');
  const isApiOrPage = url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/app') ||
    url.pathname.startsWith('/admin') ||
    url.pathname === '/' ||
    url.pathname.startsWith('/scoring') ||
    url.pathname.startsWith('/matches') ||
    url.pathname.startsWith('/players') ||
    url.pathname.startsWith('/teams');

  if (isApiOrPage && !isStaticAsset) {
    // Always go to network for pages/API, no caching
    event.respondWith(fetch(event.request));
    return;
  }

  // Static assets: network-first with cache fallback
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
