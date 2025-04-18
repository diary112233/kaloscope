/// <reference types="vite/client" />
/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />
import { cleanupOutdatedCaches, createHandlerBoundToURL, precacheAndRoute } from 'workbox-precaching';
import { NavigationRoute, registerRoute } from 'workbox-routing';

declare let self: ServiceWorkerGlobalScope;

// activate new service worker immediately when skip waiting message is received
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// self.__WB_MANIFEST is default injection point
precacheAndRoute(self.__WB_MANIFEST);

// clean up incompatible caches
cleanupOutdatedCaches();

let denylist: RegExp[] | undefined;
if (import.meta.env.DEV) {
  // disable precaching to avoid caching issues in dev mode
  denylist = [/.*/];
  // clear all caches when service worker is activated
  self.addEventListener('activate', (event) => {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(cacheNames.map((cacheName) => caches.delete(cacheName)));
      })
    );
  });
}
// register a navigation route to allow work offline
registerRoute(new NavigationRoute(createHandlerBoundToURL('/'), { denylist }));
