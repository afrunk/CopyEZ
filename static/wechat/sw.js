/* WeChat Service Worker - 处理 Web Push 推送
 * 作用域:/static/wechat/sw.js
 * iOS Safari 16.4+ 仅当网页「添加到主屏幕」后才能接收 push 事件
 */
self.addEventListener("install", (event) => {
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(self.clients.claim());
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
