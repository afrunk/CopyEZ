"""WeChat 图片上传路由
URL prefix: /wechat/api/upload
"""
import os
import secrets
import time
from pathlib import Path

from flask import Blueprint, jsonify, request
from PIL import Image, ImageOps, UnidentifiedImageError

from app.modules.wechat.auth import login_required

wechat_upload_bp = Blueprint("wechat_upload", __name__, url_prefix="/wechat/api/upload")

ALLOWED_EXT = {"jpg", "jpeg", "png", "gif", "webp"}
MAX_BYTES = 8 * 1024 * 1024  # 8MB
THUMB_MAX_EDGE = 480
UPLOAD_DIR = Path(__file__).resolve().parents[3] / "static" / "wechat" / "uploads"
THUMB_DIR = UPLOAD_DIR / "thumbs"


def _save_optimized_original(image: Image.Image, source_path: Path, image_format: str) -> None:
    """保存兼容原 URL 的原图，动画 GIF 保持原文件。"""
    if image_format == "PNG":
        image.save(source_path, format=image_format, optimize=True)
    elif image_format == "JPEG":
        image.convert("RGB").save(
            source_path, format="JPEG", quality=88, optimize=True, progressive=True
        )
    elif image_format == "WEBP":
        image.save(source_path, format="WEBP", quality=88, method=6)
    else:
        image.save(source_path)


def _create_thumbnail(image: Image.Image, thumb_path: Path, image_format: str) -> None:
    """生成气泡和缩略条使用的轻量图片。

    image 在传入前已经做过 EXIF 方向归一化（见 upload_image），
    这里不再重复 transpose，避免缩略图和原图出现 90° 错位。
    """
    thumb = image.copy()
    thumb.thumbnail((THUMB_MAX_EDGE, THUMB_MAX_EDGE), Image.Resampling.LANCZOS)
    if image_format == "GIF":
        thumb = thumb.convert("RGB")
    elif thumb.mode not in ("RGB", "RGBA"):
        thumb = thumb.convert("RGBA" if "A" in thumb.getbands() else "RGB")
    thumb.save(thumb_path, format="WEBP", quality=75, method=6)


@wechat_upload_bp.route("/image", methods=["POST"])
@login_required
def upload_image():
    """上传图片并生成缩略图。

    返回 urls 兼容旧前端，images 提供原图、缩略图和尺寸信息。
    """
    files = request.files.getlist("images")
    if not files:
        single = request.files.get("image")
        if single:
            files = [single]

    if not files:
        return jsonify({"error": "没有选择图片"}), 400

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    THUMB_DIR.mkdir(parents=True, exist_ok=True)

    urls = []
    images = []
    for file_storage in files:
        if not file_storage or not file_storage.filename:
            continue

        ext = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else ""
        if ext not in ALLOWED_EXT:
            return jsonify({"error": f"不支持的格式: {ext}"}), 400

        file_storage.seek(0, os.SEEK_END)
        size = file_storage.tell()
        file_storage.seek(0)
        if size > MAX_BYTES:
            return jsonify({"error": f"图片超过 {MAX_BYTES // 1024 // 1024}MB"}), 400

        fname = f"{int(time.time())}_{secrets.token_hex(4)}.{ext}"
        save_path = UPLOAD_DIR / fname
        thumb_name = f"{Path(fname).stem}_thumb.webp"
        thumb_path = THUMB_DIR / thumb_name

        try:
            with Image.open(file_storage) as image:
                image_format = (image.format or ext).upper()
                image.verify()
            file_storage.seek(0)
            with Image.open(file_storage) as image:
                # 统一 EXIF 方向：原图和缩略图必须来自同一份"摆正"的像素。
                # 否则手机横拍照片（EXIF Orientation=6）会出现：
                #   原图  = 原始像素且 EXIF 已被 PIL 丢弃 → 浏览器按原始方向显示
                #   缩略图 = 被 exif_transpose 旋转 90°     → 与原图差 90°
                # 结果就是大图和缩略图对不上。
                oriented = ImageOps.exif_transpose(image)
                width, height = oriented.size

                if image_format == "GIF":
                    # 动画 GIF 保留原始字节（保住帧序列与 EXIF）
                    file_storage.seek(0)
                    save_path.write_bytes(file_storage.read())
                else:
                    _save_optimized_original(oriented, save_path, image_format)

                thumb_url = f"/static/wechat/uploads/thumbs/{thumb_name}"
                try:
                    _create_thumbnail(oriented, thumb_path, image_format)
                except (OSError, ValueError):
                    thumb_url = f"/static/wechat/uploads/{fname}"
        except (UnidentifiedImageError, OSError, ValueError):
            if save_path.exists():
                save_path.unlink()
            if thumb_path.exists():
                thumb_path.unlink()
            return jsonify({"error": "图片文件无效或已损坏"}), 400

        url = f"/static/wechat/uploads/{fname}"
        urls.append(url)
        images.append({"url": url, "thumb_url": thumb_url, "width": width, "height": height})

    if not urls:
        return jsonify({"error": "保存失败"}), 500

    return jsonify({"urls": urls, "images": images}), 201
