"""
WeChat 用户资料 / 密码 / 头像 API
URL prefix: /wechat/api/me
"""
from flask import Blueprint, request, jsonify, session

from app.modules.wechat.auth import login_required, get_current_user
from app.extensions import db
from app.models.wechat import WeChatUser

me_bp = Blueprint("wechat_me", __name__, url_prefix="/wechat/api/me")


@me_bp.route("/profile", methods=["POST"])
@login_required
def update_profile():
    """更新显示名称"""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    display_name = (data.get("display_name") or "").strip()

    if not display_name:
        return jsonify({"error": "显示名称不能为空"}), 400
    if len(display_name) > 20:
        return jsonify({"error": "显示名称不超过 20 字符"}), 400
    if " " in display_name or not display_name.replace(" ", ""):
        return jsonify({"error": "显示名称不能包含纯空格"}), 400

    user.display_name = display_name
    db.session.commit()
    return jsonify(user.to_dict())


@me_bp.route("/password", methods=["POST"])
@login_required
def update_password():
    """修改密码"""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    old_password = data.get("old_password") or ""
    new_password = data.get("new_password") or ""
    confirm_password = data.get("confirm_password") or ""

    if not old_password:
        return jsonify({"error": "请输入当前密码"}), 400
    if not new_password:
        return jsonify({"error": "请输入新密码"}), 400
    if len(new_password) < 8:
        return jsonify({"error": "新密码至少 8 位"}), 400
    if new_password == old_password:
        return jsonify({"error": "新密码不能与当前密码相同"}), 400
    if new_password != confirm_password:
        return jsonify({"error": "两次新密码不一致"}), 400
    if not user.check_password(old_password):
        return jsonify({"error": "当前密码错误"}), 401

    user.set_password(new_password)
    db.session.commit()
    return jsonify({"ok": True, "message": "密码已修改"})


AVATAR_COLORS = {"#6366F1", "#10B981", "#F59E0B", "#EF4444",
                   "#EC4899", "#06B6D4", "#8B5CF6", "#F97316",
                   "#14B8A6", "#84CC16"}


@me_bp.route("/avatar", methods=["POST"])
@login_required
def update_avatar():
    """更新头像类型/颜色/emoji"""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    avatar_type = (data.get("type") or "color").strip()
    avatar_color = (data.get("color") or "#6366F1").strip()
    avatar_emoji = (data.get("emoji") or "").strip() or None
    avatar_url = (data.get("avatar_url") or "").strip() or None

    if avatar_type not in ("color", "emoji", "image"):
        avatar_type = "color"

    if avatar_type == "color":
        if avatar_color not in AVATAR_COLORS:
            avatar_color = "#6366F1"
        user.avatar_type = "color"
        user.avatar_color = avatar_color
        user.avatar_emoji = None
        user.avatar_url = None
    elif avatar_type == "emoji":
        user.avatar_type = "emoji"
        user.avatar_emoji = avatar_emoji[:8] if avatar_emoji else None
        user.avatar_url = None
    else:  # image
        user.avatar_type = "image"
        user.avatar_url = avatar_url
        user.avatar_emoji = None

    db.session.commit()
    return jsonify(user.to_dict())
