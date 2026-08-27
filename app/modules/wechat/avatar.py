"""
WeChat 用户头像上传
URL prefix: /wechat/api/upload
"""
import os
import time
import secrets
import io
from pathlib import Path
from PIL import Image
from flask import Blueprint, request, jsonify, current_app

from app.modules.wechat.auth import login_required
from app.extensions import db
from app.models.wechat import WeChatUser

avatar_bp = Blueprint("wechat_avatar_upload", __name__, url_prefix="/wechat/api/upload")

ALLOWED_EXT = {"jpg", "jpeg", "png", "gif", "webp"}
AVATAR_DIR = Path("static/wechat/avatars")
MAX_BYTES = 2 * 1024 * 1024  # 2MB
TARGET_SIZE = (256, 256)


@avatar_bp.route("/avatar", methods=["POST"])
@login_required
def upload_avatar():
    """上传用户头像

    multipart: avatar=File
    返回: { avatar_url: "/static/wechat/avatars/xxx.jpg" }
    """
    file = request.files.get("avatar")
    if not file or not file.filename:
        return jsonify({"error": "没有选择图片"}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXT:
        return jsonify({"error": f"不支持的格式: {ext}"}), 400

    # 检查大小
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_BYTES:
        return jsonify({"error": "图片不超过 2MB"}), 400

    # 读图片
    img_data = file.read()

    try:
        img = Image.open(io.BytesIO(img_data))
        img = img.convert("RGBA")
    except Exception:
        return jsonify({"error": "无法读取图片"}), 400

    # 缩放到 256x256 正方形
    # 先 crop 成 1:1
    w, h = img.size
    if w != h:
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        img = img.crop((left, top, left + side, top + side))

    img = img.resize(TARGET_SIZE, Image.LANCZOS)

    # 保存为 JPEG（圆形 mask 时转 RGB）
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"user_avatar_{int(time.time())}_{secrets.token_hex(4)}.jpg"
    save_path = AVATAR_DIR / fname

    # 圆形裁剪
    mask = Image.new("L", TARGET_SIZE, 0)
    from PIL import ImageDraw
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0) + TARGET_SIZE, fill=255)
    img_rgba = img
    img_rgb = Image.new("RGB", TARGET_SIZE, (255, 255, 255))
    img_rgb.paste(img_rgba, (0, 0), mask)

    img_rgb.save(str(save_path), "JPEG", quality=85, optimize=True)

    url = f"/static/wechat/avatars/{fname}"
    return jsonify({"avatar_url": url}), 201
