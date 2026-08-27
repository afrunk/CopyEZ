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

    if not content:
        return jsonify({"error": "消息不能为空"}), 400

    partner = WeChatUser.query.filter(WeChatUser.id != user.id).first()
    if not partner:
        return jsonify({"error": "对方不存在"}), 404

    msg = WeChatMessage(
        sender_id=user.id,
        receiver_id=partner.id,
        content=content,
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
    ).count()
    return jsonify({"unread": count})
