// =====================================================================
// sw.js — service worker da PWA SmartTracking
// =====================================================================
// Guarda em cache APENAS a "casca" da aplicação (HTML, ícones, manifest).
// Os dados de saúde que vêm do Supabase NUNCA são guardados em cache:
// assim, nada de pessoal fica no dispositivo depois de terminar a sessão
// (minimização de dados, RGPD art. 5.º).

const CACHE = 'smarttracking-v1';
const SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  // Apaga caches de versões antigas
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Só tratamos pedidos GET do próprio site. Tudo o resto (Supabase,
  // fontes, CDN) segue direto para a rede, sem passar pela cache.
  if (event.request.method !== 'GET' || url.origin !== self.location.origin) return;

  // Rede primeiro; se não houver rede, usa a cópia guardada.
  event.respondWith(
    fetch(event.request)
      .then(resp => {
        const copy = resp.clone();
        caches.open(CACHE).then(c => c.put(event.request, copy));
        return resp;
      })
      .catch(() => caches.match(event.request))
  );
});
