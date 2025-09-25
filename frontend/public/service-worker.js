const CACHE_NAME = 'smart-ocean-navigation-v1';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json'
];

// Install Service Worker
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch event
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version or fetch from network
        if (response) {
          return response;
        }
        
        // For API calls, use cache-first strategy for weather data
        if (event.request.url.includes('/api/weather/')) {
          return caches.open(CACHE_NAME).then((cache) => {
            return fetch(event.request).then((response) => {
              // Only cache successful responses
              if (response.status === 200) {
                cache.put(event.request, response.clone());
              }
              return response;
            }).catch(() => {
              // Return cached version if network fails
              return caches.match(event.request);
            });
          });
        }
        
        return fetch(event.request);
      })
  );
});

// Activate event
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});