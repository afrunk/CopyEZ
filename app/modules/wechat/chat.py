"""WeChat chat routes."""
import os

from flask import Blueprint, render_template, request, jsonify, current_app, send_from_directory

from app.extensions import db
from app.models.wechat import WeChatUser, WeChatMessage, WeChatLoginHistory
from app.modules.wechat.auth import login_required, get_current_user

wechat_chat_bp = Blueprint("wechat_chat", __name__, url_prefix="/wechat")


@wechat_chat_bp.route("/", methods=["GET"])
@login_required
def chat_page():
    user = get_current_user()
    return render_template("wechat/chat.html", user=user.to_dict())


@wechat_chat_bp.route("/api/messages", methods=["GET"])
@login_required
def api_messages():
    """获取聊天消息，默认返回最近消息，支持向前翻页和增量更新。"""
    user = get_current_user()
    partner = WeChatUser.query.filter(WeChatUser.id != user.id).first()
    if not partner:
        return jsonify({"messages": [], "partner": None, "has_more": False})

    conversation = db.or_(
        db.and_(WeChatMessage.sender_id == user.id, WeChatMessage.receiver_id == partner.id),
        db.and_(WeChatMessage.sender_id == partner.id, WeChatMessage.receiver_id == user.id),
    )
    try:
        limit = min(max(int(request.args.get("limit", 50)), 1), 100)
    except (TypeError, ValueError):
        limit = 50

    before_id = request.args.get("before_id", type=int)
    after_id = request.args.get("after_id", type=int)
    query = WeChatMessage.query.filter(conversation)
    if before_id:
        messages = query.filter(WeChatMessage.id < before_id).order_by(
            WeChatMessage.id.desc()
        ).limit(limit + 1).all()
        has_more = len(messages) > limit
        messages = list(reversed(messages[:limit]))
    elif after_id:
        messages = query.filter(WeChatMessage.id > after_id).order_by(
            WeChatMessage.id.asc()
        ).limit(limit).all()
        has_more = False
    else:
        messages = query.order_by(WeChatMessage.id.desc()).limit(limit + 1).all()
        has_more = len(messages) > limit
        messages = list(reversed(messages[:limit]))

    result = []
    for message in messages:
        item = message.to_dict()
        item["is_mine"] = message.sender_id == user.id
        result.append(item)

    return jsonify({
        "messages": result,
        "partner": partner.to_dict(),
        "has_more": has_more,
    })


@wechat_chat_bp.route("/api/messages/send", methods=["POST"])
@login_required
def api_send_message():
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    msg_type = (data.get("msg_type") or "text").strip()
    image_urls = data.get("image_urls") or []

    if msg_type == "text" and not content:
        return jsonify({"error": "消息不能为空"}), 400
    if msg_type == "image" and not image_urls:
        return jsonify({"error": "图片不能为空"}), 400

    partner = WeChatUser.query.filter(WeChatUser.id != user.id).first()
    if not partner:
        return jsonify({"error": "对方不存在"}), 404

    msg = WeChatMessage(
        sender_id=user.id,
        receiver_id=partner.id,
        content=content or "[图片]",
        msg_type=msg_type,
        image_urls=image_urls,
    )
    db.session.add(msg)
    db.session.commit()
    result = msg.to_dict()
    result["is_mine"] = True

    # ── 触发 Web Push 提醒对方 ────────────────────────────────────────
    # 只推「未读的新消息」：发件人自己肯定在线，不推自己
    # 已经在 chat.html 里看了的不算"未读"——这里以消息刚 commit 为准
    try:
        from app.modules.wechat.push import notify_user
        preview = "[图片]" if msg_type == "image" else (content or "[图片]")
        notify_user(
            user_id=partner.id,
            title=f"{user.display_name}",
            body=preview[:80],
            url="/wechat/",
        )
    except Exception as _push_exc:
        # 推送失败不应该影响消息发送
        try:
            current_app.logger.warning("web push trigger failed: %s", _push_exc)
        except Exception:
            pass

    return jsonify({"message": result}), 201


@wechat_chat_bp.route("/api/messages/mark_read", methods=["POST"])
@login_required
def api_mark_read():
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    message_ids = data.get("message_ids", [])
    if message_ids:
        WeChatMessage.query.filter(
            WeChatMessage.id.in_(message_ids),
            WeChatMessage.receiver_id == user.id,
        ).update({WeChatMessage.is_read: True}, synchronize_session=False)
        db.session.commit()
    return jsonify({"ok": True})


@wechat_chat_bp.route("/api/messages/mark_all_read", methods=["POST"])
@login_required
def api_mark_all_read():
    """将当前用户收到的全部未读消息标记为已读。"""
    user = get_current_user()
    updated = WeChatMessage.query.filter_by(
        receiver_id=user.id, is_read=False, recalled=False
    ).update({WeChatMessage.is_read: True}, synchronize_session=False)
    db.session.commit()
    return jsonify({"ok": True, "updated": updated})


@wechat_chat_bp.route("/api/unread_count", methods=["GET"])
@login_required
def api_unread_count():
    user = get_current_user()
    count = WeChatMessage.query.filter_by(
        receiver_id=user.id, is_read=False, recalled=False
    ).count()
    return jsonify({"unread": count})


@wechat_chat_bp.route("/api/messages/search", methods=["GET"])
@login_required
def api_search_messages():
    user = get_current_user()
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"results": [], "q": ""})

    partner = WeChatUser.query.filter(WeChatUser.id != user.id).first()
    if not partner:
        return jsonify({"results": [], "q": q})

    conversation = db.or_(
        db.and_(WeChatMessage.sender_id == user.id, WeChatMessage.receiver_id == partner.id),
        db.and_(WeChatMessage.sender_id == partner.id, WeChatMessage.receiver_id == user.id),
    )
    hits = WeChatMessage.query.filter(
        WeChatMessage.recalled.is_(False), conversation,
        WeChatMessage.content.ilike(f"%{q}%"),
    ).order_by(WeChatMessage.created_at.asc()).limit(50).all()

    results = []
    for message in hits:
        item = message.to_dict()
        item["is_mine"] = message.sender_id == user.id
        results.append(item)
    return jsonify({"results": results, "q": q})


@wechat_chat_bp.route("/api/partner/last_seen", methods=["GET"])
@login_required
def api_partner_last_seen():
    """返回对方最后上线时间。"""
    user = get_current_user()
    partner = WeChatUser.query.filter(WeChatUser.id != user.id).first()
    if not partner:
        return jsonify({"visible": False, "last_seen": None, "display_name": None})
    return jsonify({
        "visible": True,
        "last_seen": partner.last_seen.isoformat() if partner.last_seen else None,
        "display_name": partner.display_name,
    })


@wechat_chat_bp.route("/api/login-history", methods=["GET"])
@login_required
def api_login_history():
    """仅允许蛋蛋查看笨笨的成功登录记录。"""
    user = get_current_user()
    if user.username != "蛋蛋":
        return jsonify({"error": "无权查看登录历史"}), 403

    benben = WeChatUser.query.filter_by(username="笨笨").first()
    if not benben:
        return jsonify({"entries": [], "user": None})

    try:
        limit = min(max(int(request.args.get("limit", 50)), 1), 100)
    except (TypeError, ValueError):
        limit = 50

    entries = WeChatLoginHistory.query.filter_by(user_id=benben.id).order_by(
        WeChatLoginHistory.logged_in_at.desc()
    ).limit(limit).all()
    return jsonify({
        "entries": [entry.to_dict() for entry in entries],
        "user": benben.to_dict(),
    })


RECALL_WINDOW = 120


@wechat_chat_bp.route("/api/messages/<int:msg_id>/recall", methods=["POST"])
@login_required
def api_recall_message(msg_id):
    try:
        return _do_recall(msg_id)
    except Exception as exc:
        current_app.logger.exception("recall error")
        return jsonify({"error": f"撤回失败: {type(exc).__name__}: {exc}"}), 500


def _do_recall(msg_id):
    user = get_current_user()
    msg = db.session.get(WeChatMessage, msg_id)
    if not msg:
        return jsonify({"error": "消息不存在"}), 404
    if msg.sender_id != user.id:
        return jsonify({"error": "只能撤回自己的消息"}), 403
    if msg.recalled:
        return jsonify({"error": "消息已撤回"}), 400

    from app.utils.datetime_utils import now_bj
    created = msg.created_at
    if created is None:
        return jsonify({"error": "消息时间无效，无法撤回"}), 400
    if created.tzinfo is not None:
        created = created.replace(tzinfo=None)
    age = (now_bj() - created).total_seconds()
    if age > RECALL_WINDOW:
        return jsonify({"error": f"只能撤回 {RECALL_WINDOW // 60} 分钟内的消息"}), 400

    msg.recalled = True
    db.session.commit()
    return jsonify({"ok": True, "message": msg.to_dict()})


# ── PWA 资源（iOS 16.4+ 需要 SW 与 manifest 与 PWA 同 scope） ─────────
# 服务端动态路由 /wechat/sw.js 与 /wechat/manifest.json
# 这样 SW 路径落在 manifest 的 scope=/wechat/ 内，iOS PWA 才能 push
_PWA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "static", "wechat")


@wechat_chat_bp.route("/sw.js")
def pwa_service_worker():
    """Service Worker — 必须与 manifest scope 同级，iOS PWA 必需"""
    response = send_from_directory(_PWA_DIR, "sw.js", mimetype="application/javascript")
    # 不允许缓存，调试期间能看到最新
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@wechat_chat_bp.route("/manifest.json")
def pwa_manifest():
    """PWA Manifest — start_url 必须与 scope 同级"""
    return send_from_directory(_PWA_DIR, "manifest.json", mimetype="application/manifest+json")
