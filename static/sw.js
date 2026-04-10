// BOXcric Service Worker v21 — no caching, network-only
self.addEventListener('install', function() {
  self.skipWaiting();
  caches.keys().then(function(keys) {
    keys.forEach(function(k) { caches.delete(k); });
  });
});
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(keys.map(function(k) { return caches.delete(k); }));
    })
  );
  self.clients.claim();
});
self.addEventListener('fetch', function(event) {
  event.respondWith(fetch(event.request));
});
