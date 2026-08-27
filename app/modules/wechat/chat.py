"""
WeChat chat routes.

URL prefix: /wechat
"""
from functools import wraps
from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    request,
    jsonify,
    current_app,
)

from app.extensions import db
from app.models.wechat import WeChatUser, WeChatMessage
from app.modules.wechat.auth import login_required, get_current_user

wechat_chat_bp = Blueprint("wechat_chat", __name__, url_prefix="/wechat")


# ── 页面 ────────────────────────────────────────────────────────────────────
@wechat_chat_bp.route("/", methods=["GET"])
@login_required
def chat_page():
    """聊天主页"""
    user = get_current_user()
    return render_template("wechat/chat.html", user=user.to_dict())


# ── API ─────────────────────────────────────────────────────────────────────
@wechat_chat_bp.route("/api/messages", methods=["GET"])
@login_required
def api_messages():
    """获取与对方的所有消息（双向）"""
    user = get_current_user()

    partner = WeChatUser.query.filter(WeChatUser.id != user.id).first()
    if not partner:
        return jsonify({"messages": [], "partner": None})

    messages = WeChatMessage.query.filter(
        db.or_(
            db.and_(WeChatMessage.sender_id == user.id, WeChatMessage.receiver_id == partner.id),
            db.and_(WeChatMessage.sender_id == partner.id, WeChatMessage.receiver_id == user.id),
        )
    ).order_by(WeChatMessage.created_at.asc()).all()

    result = []
    for m in messages:
        d = m.to_dict()
        d["is_mine"] = (m.sender_id == user.id)
        result.append(d)

    return jsonify({
        "messages": result,
        "partner": partner.to_dict(),
    })


@wechat_chat_bp.route("/api/messages/send", methods=["POST"])
@login_required
def api_send_message():
    """发送消息"""
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

    d = msg.to_dict()
    d["is_mine"] = True
    return jsonify({"message": d}), 201


@wechat_chat_bp.route("/api/messages/mark_read", methods=["POST"])
@login_required
def api_mark_read():
    """标记对方发来的消息为已读"""
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


@wechat_chat_bp.route("/api/unread_count", methods=["GET"])
@login_required
def api_unread_count():
    """获取未读消息数"""
    user = get_current_user()
    count = WeChatMessage.query.filter_by(
        receiver_id=user.id,
        is_read=False,
        recalled=False,
    ).count()
    return jsonify({"unread": count})


# 撤回时间限制（秒）
RECALL_WINDOW = 120


@wechat_chat_bp.route("/api/messages/search", methods=["GET"])
@login_required
def api_search_messages():
    """按关键词搜索消息"""
    user = get_current_user()
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"results": [], "q": ""})

    partner = WeChatUser.query.filter(WeChatUser.id != user.id).first()
    if not partner:
        return jsonify({"results": [], "q": q})

    like_q = f"%{q}%"
    hits = WeChatMessage.query.filter(
        WeChatMessage.recalled == False,  # noqa: E712
        db.or_(
            db.and_(WeChatMessage.sender_id == user.id, WeChatMessage.receiver_id == partner.id),
            db.and_(WeChatMessage.sender_id == partner.id, WeChatMessage.receiver_id == user.id),
        ),
        WeChatMessage.content.ilike(like_q),
    ).order_by(WeChatMessage.created_at.asc()).limit(50).all()

    results = []
    for m in hits:
        d = m.to_dict()
        d["is_mine"] = (m.sender_id == user.id)
        results.append(d)
    return jsonify({"results": results, "q": q})


@wechat_chat_bp.route("/api/partner/last_seen", methods=["GET"])
@login_required
def api_partner_last_seen():
    """单向：只有 dandan 可查看 benben 的最后上线时间"""
    user = get_current_user()
    if user.username != "dandan":
        return jsonify({"visible": False, "last_seen": None, "display_name": None})
    partner = WeChatUser.query.filter(WeChatUser.id != user.id).first()
    if not partner:
        return jsonify({"visible": False, "last_seen": None, "display_name": None})
    return jsonify({
        "visible": True,
        "last_seen": partner.last_seen.isoformat() if partner.last_seen else None,
        "display_name": partner.display_name,
    })


@wechat_chat_bp.route("/api/messages/<int:msg_id>/recall", methods=["POST"])
@login_required
def api_recall_message(msg_id):
    """撤回消息（仅自己发的，2 分钟内）"""
    try:
        return _do_recall(msg_id)
    except Exception as e:
        import traceback
        current_app.logger.error("recall error: %s", traceback.format_exc())
        return jsonify({"error": f"撤回失败: {type(e).__name__}: {e}"}), 500


def _do_recall(msg_id):
    user = get_current_user()
    msg = WeChatMessage.query.get(msg_id)
    if not msg:
        return jsonify({"error": "消息不存在"}), 404

    if msg.sender_id != user.id:
        return jsonify({"error": "只能撤回自己的消息"}), 403

    if msg.recalled:
        return jsonify({"error": "消息已撤回"}), 400

    from app.utils.datetime_utils import now_bj
    # 容错：即便 created_at 是 aware datetime（DB 列在不同路径下被解析可能不同），统一转 naive
    created = msg.created_at
    if created is not None and created.tzinfo is not None:
        created = created.replace(tzinfo=None)
    age = (now_bj() - created).total_seconds()
    if age > RECALL_WINDOW:
        return jsonify({"error": f"只能撤回 {RECALL_WINDOW // 60} 分钟内的消息"}), 400

    msg.recalled = True
    db.session.commit()
    return jsonify({"ok": True, "message": msg.to_dict()})
