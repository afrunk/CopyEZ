/* WeChat Service Worker
 * Scope: /wechat/
 * iOS Safari 16.4+ 必须把网页「添加到主屏幕」后才能接收 push
 * 同时必须存在 fetch handler 才会被 iOS 当作有效的 PWA SW
 */
self.addEventListener("install", (event) => {
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(self.clients.claim());
});

// 占位 fetch handler —— iOS PWA 要求 SW 文件里出现 fetch 监听器
self.addEventListener("fetch", (event) => {
    // 不做缓存,网络优先
    event.respondWith(fetch(event.request).catch(() => fetch(event.request)));
});

self.addEventListener("push", (event) => {
    let data = { title: "CopyEZ", body: "你有一条新消息", url: "/wechat/" };
    try {
        if (event.data) data = event.data.json();
    } catch (e) {
        try { data.body = event.data.text(); } catch (e2) {}
    }
    const title = data.title || "CopyEZ";
    const options = {
        body: data.body || "",
        icon: data.icon || "/static/wechat/icon-192.png",
        badge: data.badge || "/static/wechat/icon-192.png",
        tag: "copyez-wechat",
        renotify: true,
        requireInteraction: false,
        data: { url: data.url || "/wechat/" },
        vibrate: [200, 100, 200],
    };
    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
    event.notification.close();
    const url = (event.notification.data && event.notification.data.url) || "/wechat/";
    event.waitUntil(
        self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
            for (const client of clientList) {
                if ("focus" in client) {
                    client.navigate(url);
                    return client.focus();
                }
            }
            if (self.clients.openWindow) return self.clients.openWindow(url);
        })
    );
});
