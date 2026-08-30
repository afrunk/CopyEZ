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


# ── 业务层：发送 Web Push ──────────────────────────────────────────────────────
def _send_one(sub: WeChatPushSubscription, title: str, body: str, url: str = "/wechat/") -> bool:
    """对一条订阅发送推送。返回 True=成功 False=失败（订阅应被清理）。"""
    from pywebpush import webpush, WebPushException

    cfg = current_app.config
    payload = json.dumps({
        "title": title,
        "body": body,
        "url": url,
        "icon": "/static/wechat/icon-192.png",
        "badge": "/static/wechat/icon-192.png",
    }, ensure_ascii=False)

    try:
        webpush(
            subscription_info={
                "endpoint": sub.endpoint,
                "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
            },
            data=payload,
            vapid_private_key=cfg["VAPID_PRIVATE_KEY"],
            vapid_claims={"sub": cfg.get("VAPID_CLAIMS_SUB", "mailto:admin@copyez.local")},
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
    subs = WeChatPushSubscription.query.filter_by(user_id=user_id).all()
    if not subs:
        return 0
    ok = 0
    for s in subs:
        if _send_one(s, title, body, url):
            ok += 1
    return ok


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
    count = notify_user(
        user.id,
        title="CopyEZ 测试推送",
        body="如果你看到这条，说明你的 iPhone 已经能收到消息提醒啦 🎉",
        url="/wechat/",
    )
    return jsonify({"ok": True, "sent": count})


@wechat_push_bp.route("/api/status", methods=["GET"])
@login_required
def api_push_status():
    """返回当前用户的订阅数。用于前端按钮文案。"""
    user = get_current_user()
    count = WeChatPushSubscription.query.filter_by(user_id=user.id).count()
    return jsonify({
        "subscribed": count > 0,
        "count": count,
        "vapid_public_key": current_app.config["VAPID_PUBLIC_KEY"],
    })
