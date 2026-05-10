"""CopyEZ 模块 - 随心记 Memo API"""
from flask import jsonify, request, url_for, current_app
from app.extensions import db
from app.models import Memo
from app.utils.datetime_utils import now_bj
import os
from uuid import uuid4
from werkzeug.utils import secure_filename

from app.modules.copyez.upload_utils import allowed_image


def api_memos():
    """随心记 API：
    - POST /api/memos  新建一条随心记
    - GET  /api/memos  获取按时间倒序排列的列表
    """
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        content = (data.get("content") or request.form.get("content") or "").strip()
        if not content:
            return jsonify({"success": False, "message": "内容不能为空"}), 400

        memo = Memo(content=content)
        tags = memo.extract_tags()
        if tags:
            memo.tags = ",".join(tags)

        db.session.add(memo)
        db.session.commit()

        return jsonify({"success": True, "memo": memo.to_dict()}), 201

    memos = (
        Memo.query.order_by(
            Memo.is_pinned.desc(),
            Memo.pinned_at.desc(),
            Memo.created_at.desc(),
            Memo.id.desc(),
        )
        .limit(200)
        .all()
    )
    return jsonify({"memos": [m.to_dict() for m in memos]})


def api_memo_pin(memo_id: int):
    """随心记：置顶/取消置顶"""
    memo = Memo.query.get_or_404(memo_id)
    data = request.get_json(silent=True) or {}
    pinned = data.get("pinned", None)

    if pinned is None:
        pinned = not bool(memo.is_pinned)
    else:
        pinned = bool(pinned)

    memo.is_pinned = pinned
    memo.pinned_at = now_bj() if pinned else None
    db.session.commit()
    return jsonify({"success": True, "memo": memo.to_dict()}), 200


def api_memo_star(memo_id: int):
    """随心记：星标/取消星标"""
    memo = Memo.query.get_or_404(memo_id)
    data = request.get_json(silent=True) or {}
    starred = data.get("starred", None)

    if starred is None:
        starred = not bool(memo.is_starred)
    else:
        starred = bool(starred)

    memo.is_starred = starred
    memo.starred_at = now_bj() if starred else None
    db.session.commit()
    return jsonify({"success": True, "memo": memo.to_dict()}), 200


def api_memo_detail(memo_id: int):
    """随心记单条记录 API：
    - PUT    /api/memos/<id>  修改内容并重新提取标签
    - DELETE /api/memos/<id>  删除该随心记
    """
    memo = Memo.query.get_or_404(memo_id)

    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        content = (data.get("content") or "").strip()
        if not content:
            return jsonify({"success": False, "message": "内容不能为空"}), 400

        memo.content = content
        tags = memo.extract_tags()
        memo.tags = ",".join(tags) if tags else None
        db.session.commit()

        return jsonify({"success": True, "memo": memo.to_dict()}), 200

    db.session.delete(memo)
    db.session.commit()
    return jsonify({"success": True, "message": "随心记已删除"}), 200


def memo_upload_image():
    """
    随心记 Memo 专用图片上传接口：
    - 支持剪贴板粘贴、拖拽上传图片
    - 图片保存到 /static/uploads/memos/ 目录
    - 如安装 Pillow，则自动将宽度压缩到不超过 1200px（等比例缩放）
    - 返回可直接用于 Markdown 的访问 URL
    """
    from flask import current_app
    Image = None
    try:
        from PIL import Image as PILImage
        Image = PILImage
    except ImportError:
        pass

    if "image" not in request.files:
        return jsonify({"success": False, "message": "未收到图片文件"}), 400

    file = request.files["image"]

    if not file or file.filename == "":
        return jsonify({"success": False, "message": "文件名为空"}), 400

    if not allowed_image(file.filename):
        return jsonify({"success": False, "message": "不支持的图片格式"}), 400

    original_name = secure_filename(file.filename)
    ext = original_name.rsplit(".", 1)[1].lower()
    random_name = f"{uuid4().hex}.{ext}"

    upload_dir = os.path.join(current_app.root_path, "static", "uploads", "memos")
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, random_name)

    if Image is not None:
        try:
            img = Image.open(file.stream)
            img = img.convert("RGB") if img.mode in ("P", "RGBA") else img

            max_width = 1200
            if img.width > max_width:
                new_height = int(img.height * max_width / img.width)
                img = img.resize((max_width, new_height), Image.LANCZOS)

            img.save(save_path, quality=85, optimize=True)
        except Exception as e:
            try:
                file.stream.seek(0)
            except Exception:
                pass
            file.save(save_path)
    else:
        file.save(save_path)

    file_url = url_for("static", filename=f"uploads/memos/{random_name}")

    return jsonify(
        {
            "success": True,
            "url": file_url,
            "filename": random_name,
        }
    )
