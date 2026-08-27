"""
BondageDiary image upload (Phase 3).

URL prefix: /diary/api/upload
"""
import os
from uuid import uuid4

from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
    url_for,
)

from app.modules.bondage_diary.auth import login_required, must_change_check, get_current_user
from app.utils.presets import ALLOWED_IMAGE_EXTENSIONS

diary_upload_bp = Blueprint("diary_upload", __name__, url_prefix="/diary/api/upload")


@diary_upload_bp.route("/image", methods=["POST"])
@login_required
@must_change_check
def upload_image():
    """
    上传日志图片。
    - field name: image
    - 保存到 static/diary/uploads/（与 CopyEZ 的 static/uploads/ 隔离）
    - 返回可直接访问的 URL
    """
    if "image" not in request.files:
        return jsonify({"success": False, "message": "未收到图片文件"}), 400

    file = request.files["image"]
    if not file or file.filename == "":
        return jsonify({"success": False, "message": "文件名为空"}), 400

    # 从原始文件名提取扩展名（避免 secure_filename 在 Windows 下丢失扩展名）
    original = file.filename
    if "." not in original:
        return jsonify({"success": False, "message": "文件无扩展名"}), 400
    ext = original.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({
            "success": False,
            "message": f"不支持的图片格式，支持: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}",
        }), 400

    random_name = f"{uuid4().hex}.{ext}"
    upload_dir = os.path.join(current_app.root_path, "static", "diary", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    save_path = os.path.join(upload_dir, random_name)
    file.save(save_path)

    file_url = url_for("static", filename=f"diary/uploads/{random_name}")
    return jsonify({
        "success": True,
        "url": file_url,
        "filename": random_name,
        "size": os.path.getsize(save_path),
    })
