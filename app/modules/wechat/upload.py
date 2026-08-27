"""
WeChat 图片上传路由
URL prefix: /wechat/api/upload
"""
import os
import time
import secrets
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app

from app.modules.wechat.auth import login_required

wechat_upload_bp = Blueprint("wechat_upload", __name__, url_prefix="/wechat/api/upload")

ALLOWED_EXT = {"jpg", "jpeg", "png", "gif", "webp"}
MAX_BYTES = 8 * 1024 * 1024  # 8MB
UPLOAD_DIR = Path("static/wechat/uploads")


@wechat_upload_bp.route("/image", methods=["POST"])
@login_required
def upload_image():
    """上传图片（单文件或多文件）

    form: images[]=File (可多张)
    返回: { urls: ["/static/wechat/uploads/xxx.jpg", ...] }
    """
    files = request.files.getlist("images")
    if not files:
        # 单文件兼容
        single = request.files.get("image")
        if single:
            files = [single]

    if not files:
        return jsonify({"error": "没有选择图片"}), 400

    # 确保目录存在
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    urls = []
    for f in files:
        if not f or not f.filename:
            continue

        # 检查扩展名
        ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
        if ext not in ALLOWED_EXT:
            return jsonify({"error": f"不支持的格式: {ext}"}), 400

        # 检查大小（读一遍）
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(0)
        if size > MAX_BYTES:
            return jsonify({"error": f"图片超过 {MAX_BYTES // 1024 // 1024}MB"}), 400

        # 文件名: <timestamp>_<random>.<ext>
        fname = f"{int(time.time())}_{secrets.token_hex(4)}.{ext}"
        save_path = UPLOAD_DIR / fname
        f.save(str(save_path))

        urls.append(f"/static/wechat/uploads/{fname}")

    if not urls:
        return jsonify({"error": "保存失败"}), 500

    return jsonify({"urls": urls}), 201
