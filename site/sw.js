// Network first, so online visitors always get the latest data. The cache is the
// fallback that lets the site open offline with the last data it loaded.
"use strict";

const CACHE = "job-watcher-v1";
const FILES = [
  "./", "index.html", "browse.html", "market.html", "style.css", "common.js", "today.js",
  "areas.js", "browse.js", "charts.js", "market.js", "manifest.webmanifest",
  "icons/icon-192.png", "icons/icon-512.png", "data/status.json", "data/history.csv",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.addAll(FILES.map((file) => new Request(file, { cache: "reload" }))))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((names) => Promise.all(
        names.filter((n) => n.startsWith("job-watcher-") && n !== CACHE).map((n) => caches.delete(n)),
      ))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET" || new URL(request.url).origin !== self.location.origin) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    try {
      // "no-cache" makes the browser check with the server instead of trusting an old copy.
      const response = await fetch(request, { cache: "no-cache" });
      if (response.ok) {
        event.waitUntil(cache.put(request, response.clone()));
        return response;
      }
      return (await cache.match(request, { ignoreSearch: true })) ?? response;
    } catch (error) {
      const saved = await cache.match(request, { ignoreSearch: true });
      if (saved) return saved;
      if (request.mode === "navigate") return cache.match("index.html");
      throw error;
    }
  })());
});
