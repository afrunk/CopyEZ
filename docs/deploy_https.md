# 生产环境部署说明（HTTPS + iOS 推送）

> 最后更新：2026-11-11

## 1. 架构

```
浏览器 / iPhone PWA
        |  https://39.106.147.188[:5000]
        v
     nginx  (443 / 5000 -> TLS 终止, 80 -> ACME 校验)
        |  http://127.0.0.1:5001
        v
   Flask (systemd: copyez.service, 只监听 127.0.0.1:5001)
```

- nginx 配置：`/etc/nginx/conf.d/copyez.conf`
- 证书：`/etc/letsencrypt/live/39.106.147.188/`
- Flask 服务：`/etc/systemd/system/copyez.service`

## 2. 为什么必须要 HTTPS

iOS 的 Web Push 依赖 Service Worker，而 **Service Worker 与 Push API 只在安全上下文
(HTTPS) 下可用**。在 `http://` 下 `navigator.serviceWorker` 根本不存在，
订阅流程会直接静默失败 —— 这就是"iPhone 收不到提醒"的根因。

本项目用 **Let's Encrypt 的 IP 证书**（`shortlived` profile，6 天有效期），
不需要域名、不需要备案、不需要注册任何账号，证书签发给 IP `39.106.147.188`。

## 3. 常用运维命令

```bash
# 服务状态
systemctl status copyez
systemctl restart copyez
journalctl -u copyez -f

# nginx
nginx -t && systemctl reload nginx
tail -f /var/log/nginx/access.log

# 证书续期（shortlived 证书每 6 天过期）
/opt/certbot-venv/bin/certbot renew
systemctl list-timers | grep certbot        # 定时续期已配置，每 6 小时检查一次
openssl x509 -enddate -noout -in /etc/letsencrypt/live/39.106.147.188/fullchain.pem
```

续期使用 webroot 方式（`/var/www/certbot`），nginx 运行时也能续，不需要停服务。

## 4. 安全组

阿里云安全组需要放行：

| 端口 | 用途 | 说明 |
|---|---|---|
| 22 | SSH | 已有 |
| 80 | ACME 校验 + 明文兜底 | 已有 |
| 443 | HTTPS（推荐入口） | **需要新增** |
| 5000 | HTTPS（备用入口，端口已开放时立即可用） | 已有 |

> 443 未放行时，直接使用 `https://39.106.147.188:5000/` 即可，
> 证书、Service Worker、推送全部正常工作。

## 5. iPhone 端开启提醒的步骤

1. 用 **Safari 打开 `https://39.106.147.188:5000/wechat/`**（必须是 https）
2. 分享 -> "添加到主屏幕"
3. 从主屏幕图标进入（必须从主屏启动，浏览器标签页里收不到推送）
4. 点右上角铃铛 -> 授权通知 -> 显示"已开启手机提醒"
5. 之后对方发消息，iPhone 就会收到通知

长按铃铛可以查看推送诊断信息（安全上下文、权限、订阅数、订阅来源）。

## 6. 推送链路要点

- 浏览器订阅 -> `POST /wechat/push/api/subscribe` 存入 `wechat_push_subscriptions`
- 对方发消息 -> `notify_user()` -> pywebpush 发送
- **iOS 必须补 APNs 扩展头**，否则苹果服务会接受连接但静默丢弃通知：

  ```
  apns-push-type: alert
  apns-priority: 10
  apns-topic: com.apple.webpush.<VAPID_CLAIMS_SUB>
  ```

- **VAPID 私钥是 PEM 格式**，而 `py_vapid.Vapid.from_string()` 只支持 raw/DER，
  必须先转成 `Vapid.from_pem()`（见 `app/modules/wechat/push.py` 的 `_vapid_private_key`）。
