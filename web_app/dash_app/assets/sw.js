/*
 * ECGiga Service Worker
 * Provides offline support with network-first (dynamic) and cache-first (static) strategies.
 */

const CACHE_NAME = 'ecgiga-v1';
const STATIC_CACHE = 'ecgiga-static-v1';
const API_CACHE = 'ecgiga-api-v1';

const STATIC_ASSETS = [
  '/',
  '/assets/style.css',
  '/assets/manifest.json',
  '/assets/pwa_register.js',
  '/assets/icon-192.png',
  '/assets/icon-512.png',
];

const OFFLINE_PAGE = '/offline.html';

/* ------------------------------------------------------------------ */
/*  Install – pre-cache static shell                                  */
/* ------------------------------------------------------------------ */
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        // Some assets may not exist yet; continue gracefully
        console.warn('[SW] Pre-cache partial failure:', err);
      });
    })
  );
  // Activate immediately without waiting for old SW to stop
  self.skipWaiting();
});

/* ------------------------------------------------------------------ */
/*  Activate – clean old caches                                       */
/* ------------------------------------------------------------------ */
self.addEventListener('activate', (event) => {
  const allowedCaches = [STATIC_CACHE, API_CACHE];
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => !allowedCaches.includes(key))
          .map((key) => caches.delete(key))
      )
    )
  );
  // Claim all open clients so the new SW takes effect immediately
  self.clients.claim();
});

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

function isStaticAsset(url) {
  const path = new URL(url).pathname;
  return (
    path.startsWith('/assets/') ||
    path.endsWith('.css') ||
    path.endsWith('.js') ||
    path.endsWith('.png') ||
    path.endsWith('.jpg') ||
    path.endsWith('.jpeg') ||
    path.endsWith('.gif') ||
    path.endsWith('.svg') ||
    path.endsWith('.woff') ||
    path.endsWith('.woff2') ||
    path.endsWith('.ico')
  );
}

function isAPIRequest(url) {
  const path = new URL(url).pathname;
  return (
    path.startsWith('/api/') ||
    path.startsWith('/_dash-') ||
    path.startsWith('/_callback')
  );
}

/* ------------------------------------------------------------------ */
/*  Cache-first strategy (static assets)                              */
/* ------------------------------------------------------------------ */
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (err) {
    // For navigation requests, return offline page if available
    if (request.mode === 'navigate') {
      const offlinePage = await caches.match(OFFLINE_PAGE);
      if (offlinePage) return offlinePage;
    }
    return new Response('Offline — recurso indisponivel', {
      status: 503,
      statusText: 'Service Unavailable',
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });
  }
}

/* ------------------------------------------------------------------ */
/*  Network-first strategy (dynamic / API)                            */
/* ------------------------------------------------------------------ */
async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(API_CACHE);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (err) {
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    return new Response(
      JSON.stringify({ error: 'offline', message: 'Sem conexao' }),
      {
        status: 503,
        statusText: 'Service Unavailable',
        headers: { 'Content-Type': 'application/json; charset=utf-8' },
      }
    );
  }
}

/* ------------------------------------------------------------------ */
/*  Fetch handler – route to correct strategy                         */
/* ------------------------------------------------------------------ */
self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Only handle GET requests
  if (request.method !== 'GET') return;

  // Skip cross-origin requests
  if (!request.url.startsWith(self.location.origin)) return;

  if (isStaticAsset(request.url)) {
    event.respondWith(cacheFirst(request));
  } else if (isAPIRequest(request.url)) {
    event.respondWith(networkFirst(request));
  } else {
    // Navigation and other requests — network first with offline fallback
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cache successful navigation responses
          if (response.ok && request.mode === 'navigate') {
            const cache = caches.open(STATIC_CACHE);
            cache.then((c) => c.put(request, response.clone()));
          }
          return response;
        })
        .catch(async () => {
          const cached = await caches.match(request);
          if (cached) return cached;
          // Fallback offline page for navigation
          if (request.mode === 'navigate') {
            const offlinePage = await caches.match(OFFLINE_PAGE);
            if (offlinePage) return offlinePage;
            return new Response(
              '<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">' +
              '<meta name="viewport" content="width=device-width,initial-scale=1">' +
              '<title>ECGiga — Offline</title>' +
              '<style>body{font-family:system-ui,sans-serif;display:flex;' +
              'justify-content:center;align-items:center;min-height:100vh;' +
              'margin:0;background:#f5f5f5;color:#333;text-align:center}' +
              '.box{padding:2rem;max-width:480px}h1{color:#1a73e8}' +
              '</style></head><body><div class="box">' +
              '<h1>ECGiga</h1>' +
              '<p>Voce esta sem conexao. Verifique sua rede e tente novamente.</p>' +
              '</div></body></html>',
              {
                status: 200,
                headers: { 'Content-Type': 'text/html; charset=utf-8' },
              }
            );
          }
          return new Response('Offline', { status: 503 });
        })
    );
  }
});
