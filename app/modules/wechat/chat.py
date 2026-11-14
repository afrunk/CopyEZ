"""WeChat chat routes."""
import os

from flask import Blueprint, render_template, request, jsonify, current_app, send_from_directory

from app.extensions import db
from app.models.wechat import WeChatUser, WeChatMessage, WeChatLoginHistory
from app.modules.wechat.auth import login_required, get_current_user
from app.modules.wechat.identity import resolve_context, person_label

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
    my_ids, their_ids, partner = resolve_context(user)
    if not partner:
        return jsonify({"messages": [], "partner": None, "has_more": False})

    conversation = _conversation_filter(my_ids, their_ids)
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
        item["is_mine"] = message.sender_id in my_ids
        result.append(item)

    return jsonify({
        "messages": result,
        "partner": partner.to_dict(),
        "has_more": has_more,
    })


def _conversation_filter(my_ids: set, their_ids: set):
    """当前登录者与对方之间的消息过滤条件。

    my_ids / their_ids 是「人」级别的账号 id 集合（同一个人的多个账号行都在里面），
    这样无论用哪个账号登录，看到的历史都是同一份。
    """
    return db.or_(
        db.and_(
            WeChatMessage.sender_id.in_(my_ids),
            WeChatMessage.receiver_id.in_(their_ids),
        ),
        db.and_(
            WeChatMessage.sender_id.in_(their_ids),
            WeChatMessage.receiver_id.in_(my_ids),
        ),
    )


def _normalize_image_items(raw):
    """把 image_urls 字段统一成 [{url, thumb_url, width, height}, ...]。

    历史上 image_urls 有三种形态：
      1. None（老数据只有 "[图片]" 文本）
      2. ["<url>", ...]            纯字符串数组
      3. [{"url":..., "thumb_url":...}]  上传接口写入的对象数组
    另外 JSON 列里偶尔会被写成"被再次序列化的字符串"，这里一并兜底。
    """
    import json as _json

    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            raw = _json.loads(raw)
        except (ValueError, TypeError):
            raw = [raw]
    if not isinstance(raw, list):
        return []

    items = []
    for entry in raw:
        if isinstance(entry, str):
            url = entry
            thumb = entry
        elif isinstance(entry, dict):
            url = entry.get("url") or ""
            thumb = entry.get("thumb_url") or url
        else:
            continue
        # 历史上有一批消息把正文误写进了 image_urls（如 "安排"），这里过滤掉，
        # 否则浏览器会去加载 /wechat/安排 这种不存在的地址。
        if not (url.startswith("/") or url.startswith("http")):
            continue
        items.append({
            "url": url,
            "thumb_url": thumb if (thumb.startswith("/") or thumb.startswith("http")) else url,
            "width": entry.get("width") if isinstance(entry, dict) else None,
            "height": entry.get("height") if isinstance(entry, dict) else None,
        })
    return items


@wechat_chat_bp.route("/api/images", methods=["GET"])
@login_required
def api_images():
    """返回会话内的全部图片（按时间正序），供图片查看器左右翻页。

    之前查看器只能翻到"已经加载进页面的消息"里的图片，历史图片永远翻不到；
    这里一次性返回全部图片，保证能翻到任意一张。
    """
    user = get_current_user()
    my_ids, their_ids, partner = resolve_context(user)
    if not partner:
        return jsonify({"images": [], "total": 0})

    rows = WeChatMessage.query.filter(
        _conversation_filter(my_ids, their_ids),
        WeChatMessage.msg_type == "image",
        WeChatMessage.recalled.is_(False),
        WeChatMessage.image_urls.isnot(None),
    ).order_by(WeChatMessage.id.asc()).all()

    images = []
    for message in rows:
        for item in _normalize_image_items(message.image_urls):
            images.append({
                "msg_id": message.id,
                "url": item["url"],
                "thumb_url": item["thumb_url"],
                "width": item.get("width"),
                "height": item.get("height"),
                "is_mine": message.sender_id in my_ids,
                "created_at": message.created_at.isoformat() if message.created_at else None,
            })

    return jsonify({"images": images, "total": len(images)})


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

    my_ids, their_ids, partner = resolve_context(user)
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
    my_ids, their_ids, _ = resolve_context(user)
    data = request.get_json(silent=True) or {}
    message_ids = data.get("message_ids", [])
    if message_ids:
        WeChatMessage.query.filter(
            WeChatMessage.id.in_(message_ids),
            WeChatMessage.receiver_id.in_(my_ids),
        ).update({WeChatMessage.is_read: True}, synchronize_session=False)
        db.session.commit()
    return jsonify({"ok": True})


@wechat_chat_bp.route("/api/messages/mark_all_read", methods=["POST"])
@login_required
def api_mark_all_read():
    """将当前用户收到的全部未读消息标记为已读。"""
    user = get_current_user()
    my_ids, their_ids, _ = resolve_context(user)
    updated = WeChatMessage.query.filter(
        WeChatMessage.receiver_id.in_(my_ids),
        WeChatMessage.is_read == False,
        WeChatMessage.recalled == False,
    ).update({WeChatMessage.is_read: True}, synchronize_session=False)
    db.session.commit()
    return jsonify({"ok": True, "updated": updated})


@wechat_chat_bp.route("/api/unread_count", methods=["GET"])
@login_required
def api_unread_count():
    user = get_current_user()
    my_ids, their_ids, _ = resolve_context(user)
    count = WeChatMessage.query.filter(
        WeChatMessage.receiver_id.in_(my_ids),
        WeChatMessage.is_read == False,
        WeChatMessage.recalled == False,
    ).count()
    return jsonify({"unread": count})


@wechat_chat_bp.route("/api/messages/search", methods=["GET"])
@login_required
def api_search_messages():
    user = get_current_user()
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"results": [], "q": ""})

    my_ids, their_ids, partner = resolve_context(user)
    if not partner:
        return jsonify({"results": [], "q": q})

    conversation = _conversation_filter(my_ids, their_ids)
    hits = WeChatMessage.query.filter(
        WeChatMessage.recalled.is_(False), conversation,
        WeChatMessage.content.ilike(f"%{q}%"),
    ).order_by(WeChatMessage.created_at.asc()).limit(50).all()

    results = []
    for message in hits:
        item = message.to_dict()
        item["is_mine"] = message.sender_id in my_ids
        results.append(item)
    return jsonify({"results": results, "q": q})


@wechat_chat_bp.route("/api/partner/last_seen", methods=["GET"])
@login_required
def api_partner_last_seen():
    """返回对方最后上线时间。"""
    user = get_current_user()
    _, their_ids, partner = resolve_context(user)
    if not partner:
        return jsonify({"visible": False, "last_seen": None, "display_name": None})

    # 对方可能有多个账号行（同一个人的历史别名），取最近一次上线时间
    last_seen = None
    for other in WeChatUser.query.filter(WeChatUser.id.in_(their_ids)).all():
        if other.last_seen and (last_seen is None or other.last_seen > last_seen):
            last_seen = other.last_seen

    return jsonify({
        "visible": True,
        "last_seen": last_seen.isoformat() if last_seen else None,
        "display_name": partner.display_name or person_label(partner),
    })


@wechat_chat_bp.route("/api/login-history", methods=["GET"])
@login_required
def api_login_history():
    """仅允许蛋蛋查看笨笨的成功登录记录。"""
    user = get_current_user()
    if person_label(user) != "蛋蛋":
        return jsonify({"error": "无权查看登录历史"}), 403

    # 笨笨可能有多个账号行（历史别名），登录记录要合并
    benben_ids = {
        u.id for u in WeChatUser.query.all() if person_label(u) == "笨笨"
    }
    benben = (
        WeChatUser.query.filter(WeChatUser.id.in_(benben_ids)).first()
        if benben_ids else None
    )
    if not benben:
        return jsonify({"entries": [], "user": None})

    try:
        limit = min(max(int(request.args.get("limit", 50)), 1), 100)
    except (TypeError, ValueError):
        limit = 50

    entries = WeChatLoginHistory.query.filter(
        WeChatLoginHistory.user_id.in_(benben_ids)
    ).order_by(
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
    my_ids, their_ids, _ = resolve_context(user)
    msg = db.session.get(WeChatMessage, msg_id)
    if not msg:
        return jsonify({"error": "消息不存在"}), 404
    if msg.sender_id not in my_ids:
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
# chat.py 位于 <root>/app/modules/wechat/，向上 4 级到 <root>，再拼 static/wechat
_PWA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "static", "wechat",
)


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
