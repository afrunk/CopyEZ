"""
Upload Utilities - CopyEZ 公文素材库

提供统一的图片上传工具：
- ALLOWED_IMAGE_EXTENSIONS: 从 config.py 导入
- allowed_image(): 校验文件扩展名是否在允许列表中
- upload_image(): 通用编辑器图片上传（长文 Note 使用）

本模块仅 upload_image() 需要 current_app，其他函数是纯工具函数。
"""

from app.utils.presets import ALLOWED_IMAGE_EXTENSIONS
from flask import jsonify, request, url_for
from werkzeug.utils import secure_filename
from uuid import uuid4
import os


def allowed_image(filename: str) -> bool:
    """
    校验图片文件扩展名是否在允许列表中。

    参数:
        filename: 上传文件的原始文件名

    返回:
        True 如果扩展名在 ALLOWED_IMAGE_EXTENSIONS 中，否则 False
    """
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


def upload_image():
    """
    通用编辑器图片"即粘即传"接口（长文 Note 使用）：
    - 接收前端粘贴的图片文件（field 名称为 image）
    - 保存到 /static/uploads/ 目录下
    - 返回可直接用于 Markdown 的访问 URL
    """
    from flask import current_app

    if "image" not in request.files:
        return jsonify({"success": False, "message": "未收到图片文件"}), 400

    file = request.files["image"]

    if not file or file.filename == "":
        return jsonify({"success": False, "message": "文件名为空"}), 400

    if not allowed_image(file.filename):
        return jsonify({"success": False, "message": "不支持的图片格式"}), 400

    # 生成安全文件名 + 随机前缀，避免覆盖
    original_name = secure_filename(file.filename)
    ext = original_name.rsplit(".", 1)[1].lower()
    random_name = f"{uuid4().hex}.{ext}"

    upload_dir = os.path.join(current_app.root_path, "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    save_path = os.path.join(upload_dir, random_name)
    file.save(save_path)

    # 生成可访问的 URL（供 Markdown 使用）
    file_url = url_for("static", filename=f"uploads/{random_name}")

    return jsonify(
        {
            "success": True,
            "url": file_url,
            "filename": random_name,
        }
    )
