"""
WeChat Web Push 蓝图

URL prefix: /wechat/push

提供 4 个接口：
  GET  /api/vapid_public_key     返回服务端公钥，前端订阅时用
  POST /api/subscribe            保存前端 Service Worker 的 subscription
  POST /api/unsubscribe          取消某个 endpoint 的订阅
  POST /api/test                 当前登录用户触发一条测试推送（联调用）

业务层:
  - notify_user(user_id, title, body)  给指定用户的所有订阅广播
  - 在 chat.py 的 api_send_message 之后调用
"""
import json
import logging
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app

from app.extensions import db
from app.models.wechat import WeChatUser, WeChatPushSubscription
from app.modules.wechat.auth import login_required, get_current_user

wechat_push_bp = Blueprint("wechat_push", __name__, url_prefix="/wechat/push")

# iOS(WebKit) 的推送走苹果自己的 Web Push 服务，除了 VAPID 之外还必须带
# APNs 的扩展头，缺失时苹果服务会接受连接但**静默丢弃**通知（表现为"没提醒"）。
APPLE_PUSH_HOSTS = ("api.push.apple.com", "web.push.apple.com")


def _vapid_private_key(raw):
    """把配置里的 VAPID 私钥转成 py_vapid 能识别的形式。

    py_vapid.Vapid.from_string() 只支持 raw(32 字节) / DER，
    而 config.py 里存的是标准 PEM —— 直接传进去会在签名前就抛
    "Could not deserialize key data"，推送永远发不出去。
    这里统一转成 Vapid 对象。
    """
    if isinstance(raw, str) and "-----BEGIN" in raw:
        from py_vapid import Vapid
        return Vapid.from_pem(raw.encode())
    return raw


def _apple_push_headers(vapid_sub: str) -> dict:
    """构造 iOS 推送必需的 APNs 扩展头。"""
    return {
        "apns-push-type": "alert",
        "apns-priority": "10",
        "apns-expiration": "0",
        "apns-topic": f"com.apple.webpush.{vapid_sub}",
    }


# ── 业务层：发送 Web Push ──────────────────────────────────────────────────────
def _send_one(sub: WeChatPushSubscription, title: str, body: str, url: str = "/wechat/") -> bool:
    """对一条订阅发送推送。返回 True=成功 False=失败（订阅应被清理）。"""
    from pywebpush import webpush, WebPushException

    cfg = current_app.config
    vapid_sub = cfg.get("VAPID_CLAIMS_SUB", "mailto:admin@copyez.local")
    payload = json.dumps({
        "title": title,
        "body": body,
        "url": url,
        "icon": "/static/wechat/icon-192.png",
        "badge": "/static/wechat/icon-192.png",
    }, ensure_ascii=False)

    # 只有苹果的推送服务才需要 APNs 头，其它厂商（FCM/Mozilla）带上会被忽略
    extra_headers = {}
    if any(host in (sub.endpoint or "") for host in APPLE_PUSH_HOSTS):
        extra_headers = _apple_push_headers(vapid_sub)

    try:
        webpush(
            subscription_info={
                "endpoint": sub.endpoint,
                "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
            },
            data=payload,
            vapid_private_key=_vapid_private_key(cfg["VAPID_PRIVATE_KEY"]),
            vapid_claims={"sub": vapid_sub},
            headers=extra_headers or None,
            timeout=10,
        )
        sub.last_used_at = datetime.utcnow()
        db.session.commit()
        return True
    except WebPushException as exc:
        # 410 Gone / 404 Not Found → 浏览器/系统已废弃此 endpoint，删除
        resp = getattr(exc, "response", None)
        status = getattr(resp, "status_code", None) if resp else None
        logging.getLogger("wechat_push").warning(
            "push failed sub=%s status=%s err=%s", sub.id, status, exc
        )
        if status in (404, 410):
            db.session.delete(sub)
            db.session.commit()
        return False
    except Exception as exc:
        logging.getLogger("wechat_push").exception("push unexpected error: %s", exc)
        return False


def notify_user(user_id: int, title: str, body: str, url: str = "/wechat/") -> int:
    """给 user_id 的所有订阅广播推送。返回成功条数。"""
    return notify_user_detail(user_id, title, body, url)["sent"]


def notify_user_detail(user_id: int, title: str, body: str, url: str = "/wechat/") -> dict:
    """广播推送并返回明细，便于前端/接口直接看到失败原因。"""
    subs = WeChatPushSubscription.query.filter_by(user_id=user_id).all()
    if not subs:
        return {"sent": 0, "total": 0, "details": []}
    ok = 0
    details = []
    for s in subs:
        sent = _send_one(s, title, body, url)
        ok += 1 if sent else 0
        details.append({
            "endpoint": (s.endpoint or "")[:120],
            "sent": sent,
        })
    return {"sent": ok, "total": len(subs), "details": details}


# ── 接口 ──────────────────────────────────────────────────────────────────────
@wechat_push_bp.route("/api/vapid_public_key", methods=["GET"])
def api_vapid_public_key():
    """返回 VAPID 公钥给前端 Service Worker subscribe() 用。"""
    return jsonify({"key": current_app.config["VAPID_PUBLIC_KEY"]})


@wechat_push_bp.route("/api/subscribe", methods=["POST"])
@login_required
def api_subscribe():
    """保存一条订阅。重复 endpoint 会被 upsert（覆盖 user_id / keys）。"""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    endpoint = (data.get("endpoint") or "").strip()
    keys = data.get("keys") or {}
    p256dh = (keys.get("p256dh") or "").strip()
    auth = (keys.get("auth") or "").strip()

    if not endpoint or not p256dh or not auth:
        return jsonify({"error": "订阅数据不完整"}), 400
    if not endpoint.startswith("https://"):
        return jsonify({"error": "endpoint 必须是 https"}), 400

    existing = WeChatPushSubscription.query.filter_by(endpoint=endpoint[:500]).first()
    ua = (request.headers.get("User-Agent") or "")[:300]

    if existing:
        existing.user_id = user.id
        existing.p256dh = p256dh
        existing.auth = auth
        existing.user_agent = ua
        existing.last_used_at = datetime.utcnow()
    else:
        db.session.add(WeChatPushSubscription(
            user_id=user.id,
            endpoint=endpoint[:500],
            p256dh=p256dh,
            auth=auth,
            user_agent=ua,
        ))
    db.session.commit()
    return jsonify({"ok": True, "user_id": user.id})


@wechat_push_bp.route("/api/unsubscribe", methods=["POST"])
@login_required
def api_unsubscribe():
    """删除当前用户的某条订阅。"""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    endpoint = (data.get("endpoint") or "").strip()
    if not endpoint:
        return jsonify({"error": "缺少 endpoint"}), 400

    deleted = WeChatPushSubscription.query.filter_by(
        user_id=user.id, endpoint=endpoint[:500]
    ).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({"ok": True, "deleted": deleted})


@wechat_push_bp.route("/api/test", methods=["POST"])
@login_required
def api_test_push():
    """触发一条测试推送给自己。联调用。"""
    user = get_current_user()
    result = notify_user_detail(
        user.id,
        title="CopyEZ 测试推送",
        body="如果你看到这条，说明你的 iPhone 已经能收到消息提醒啦 🎉",
        url="/wechat/",
    )
    return jsonify({
        "ok": result["sent"] > 0,
        "sent": result["sent"],
        "total": result["total"],
        "details": result["details"],
    })


def _endpoint_host(endpoint: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(endpoint or "").netloc
    except Exception:
        return ""


@wechat_push_bp.route("/api/status", methods=["GET"])
@login_required
def api_push_status():
    """返回当前用户的订阅情况。用于前端按钮文案与排查。"""
    user = get_current_user()
    subs = WeChatPushSubscription.query.filter_by(user_id=user.id).all()
    # 只统计"看起来是真实浏览器订阅"的记录：
    # endpoint 必须是 https，且 host 不能是示例域名 / 本机
    real = []
    for s in subs:
        endpoint = s.endpoint or ""
        host = _endpoint_host(endpoint)
        if not endpoint.startswith("https://"):
            continue
        if host in ("fake.example.com", "example.com", "localhost", "127.0.0.1"):
            continue
        real.append(s)

    return jsonify({
        "subscribed": len(real) > 0,
        "count": len(real),
        "raw_count": len(subs),
        # 请求本身是否来自 HTTPS —— iOS 只有安全上下文才能注册 SW / 订阅推送
        "secure": bool(request.is_secure),
        "host": request.host,
        "subscriptions": [{
            "endpoint_host": _endpoint_host(s.endpoint),
            "is_apple": any(h in (s.endpoint or "") for h in APPLE_PUSH_HOSTS),
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "last_used_at": s.last_used_at.isoformat() if s.last_used_at else None,
        } for s in subs],
        "vapid_public_key": current_app.config["VAPID_PUBLIC_KEY"],
    })


@wechat_push_bp.route("/api/cleanup", methods=["POST"])
@login_required
def api_push_cleanup():
    """清理无效订阅（示例域名 / 非 https / 本机地址）。"""
    user = get_current_user()
    subs = WeChatPushSubscription.query.filter_by(user_id=user.id).all()
    removed = 0
    for s in subs:
        endpoint = s.endpoint or ""
        host = _endpoint_host(endpoint)
        if (not endpoint.startswith("https://")
                or host in ("fake.example.com", "example.com", "localhost", "127.0.0.1")):
            db.session.delete(s)
            removed += 1
    db.session.commit()
    return jsonify({"ok": True, "removed": removed})
