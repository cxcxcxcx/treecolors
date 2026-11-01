const CACHE_NAME = 'tree-map-v20261101-084343';
const ASSETS_TO_CACHE = [
    './',
    './index.html',
    './favicon.ico',
    './icon-botanisense-red-side-192.png?v=20261031a',
    './icon-botanisense-red-side-512.png?v=20261031a',
    './apple-touch-botanisense-red-side.png?v=20261031a',
    './app.webmanifest',
    './manifest.json',
    './species_stats.json',
    './sources.json',
    'https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js',
    'https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css',
    'https://unpkg.com/pmtiles@3.1.0/dist/pmtiles.js'
];

self.addEventListener('install', (event) => {
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil((async () => {
        await self.clients.claim();
        const cacheNames = await caches.keys();
        await Promise.all(
            cacheNames.map((cacheName) => {
                if (cacheName !== CACHE_NAME) {
                    return caches.delete(cacheName);
                }
            })
        );
    })());
});

self.addEventListener('fetch', (event) => {
    // Navigations are network-first so a deploy can never leave users on a
    // stale index.html (the old cache-first handler caused exactly that).
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request)
                .then((response) => {
                    const copy = response.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
                    return response;
                })
                .catch(() => caches.match(event.request))
        );
        return;
    }
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        })
    );
});
