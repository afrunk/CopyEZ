"""
BondageDiary entries CRUD (Phase 3).

URL prefix: /diary/api/entries

权限规则：
  - 母狗（pup）：可创建日志；只能修改/删除自己(author_id == user.id) 的日志
  - 主人（master）：可创建点评（Phase 4）；可删除任意日志
  - 主人**不能**修改母狗的日志文本（只能点评）

版本化（修改历史）：
  - 每次 PUT /api/entries/<id>，把当前 content_text + 图片列表快照写入
    diary_entry_revisions，然后才覆盖 entry
"""
import json
from flask import (
    Blueprint,
    request,
    jsonify,
    abort,
)

from app.extensions import db
from app.utils.datetime_utils import now_bj
from app.models.bondage_diary import (
    DiaryEntry,
    DiaryImage,
    DiaryEntryRevision,
    DiaryAccessLog,
)
from app.modules.bondage_diary.auth import (
    login_required,
    must_change_check,
    get_current_user,
)
from app.modules.bondage_diary.access_log import log_action

diary_entries_bp = Blueprint("diary_entries", __name__, url_prefix="/diary/api/entries")


# ── 权限 ────────────────────────────────────────────────────────────────────────
def _check_can_edit_entry(user, entry):
    """谁能改日志内容"""
    if user.role == "master":
        return False, "主人不能修改日志内容"
    if entry.author_id != user.id:
        return False, "只能修改自己的日志"
    return True, ""


def _check_can_delete_entry(user, entry):
    """谁能删日志"""
    if user.role == "master":
        return True, ""
    if entry.author_id != user.id:
        return False, "只能删除自己的日志"
    return True, ""


# ── 列表 ────────────────────────────────────────────────────────────────────────
@diary_entries_bp.route("", methods=["GET"])
@login_required
@must_change_check
def list_entries():
    """日志时间线（默认按 created_at 倒序）

    Query:
      - limit: int, 默认 20
      - offset: int, 默认 0
      - author_role: 'pup' | 'master' (master 调用时可筛)
    """
    limit = min(int(request.args.get("limit", 20)), 100)
    offset = max(int(request.args.get("offset", 0)), 0)
    author_role = request.args.get("author_role")

    user = get_current_user()
    q = DiaryEntry.query.filter_by(is_deleted=False)

    # pup 只能看自己的日志
    if user.role == "pup":
        q = q.filter(DiaryEntry.author_id == user.id)
    elif author_role:
        # master 端可按角色筛
        from app.models.bondage_diary import DiaryUser
        target_ids = [u.id for u in DiaryUser.query.filter_by(role=author_role, is_active=True).all()]
        q = q.filter(DiaryEntry.author_id.in_(target_ids)) if target_ids else q.filter(DiaryEntry.id == -1)

    entries = q.order_by(
        DiaryEntry.is_pinned.desc(),
        DiaryEntry.created_at.desc(),
    ).limit(limit).offset(offset).all()

    return jsonify({
        "entries": [e.to_dict() for e in entries],
        "has_more": len(entries) == limit,
    })


# ── 详情 ────────────────────────────────────────────────────────────────────────
@diary_entries_bp.route("/<int:entry_id>", methods=["GET"])
@login_required
@must_change_check
def get_entry(entry_id):
    """日志详情（含图片 + 评论 + 修改历史摘要）"""
    user = get_current_user()
    entry = DiaryEntry.query.get_or_404(entry_id)

    if entry.is_deleted:
        return jsonify({"error": "日志已删除"}), 404

    # pup 只能看自己
    if user.role == "pup" and entry.author_id != user.id:
        return jsonify({"error": "无权查看"}), 403

    data = entry.to_dict(include_content=True)
    data["images"] = [img.to_dict() for img in entry.images]
    data["comments"] = [c.to_dict() for c in entry.comments.filter_by(is_deleted=False)]
    data["revision_count"] = entry.revisions.count()
    return jsonify(data)


# ── 创建 ────────────────────────────────────────────────────────────────────────
@diary_entries_bp.route("", methods=["POST"])
@login_required
@must_change_check
def create_entry():
    """发日志

    Body:
      - content_text: str, 必填
      - mood: str, 可选
      - image_urls: list[str], 可选（已上传的 URL 列表）
    """
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    content = (data.get("content_text", "") or "").strip()
    mood = (data.get("mood", "") or "").strip() or None
    image_urls = data.get("image_urls", []) or []

    if not content:
        return jsonify({"error": "内容不能为空"}), 400
    if len(content) > 10000:
        return jsonify({"error": "内容过长（≤10000 字）"}), 400
    if len(image_urls) > 9:
        return jsonify({"error": "图片最多 9 张"}), 400

    entry = DiaryEntry(
        author_id=user.id,
        content_text=content,
        mood=mood,
    )
    db.session.add(entry)
    db.session.flush()  # 拿到 entry.id

    # 关联图片
    for idx, url in enumerate(image_urls):
        img = DiaryImage(
            entry_id=entry.id,
            image_url=url,
            image_path=url,  # 用 URL 当 path（不做磁盘映射）
            sort_order=idx,
        )
        db.session.add(img)

    log_action(user.id, DiaryAccessLog.ACTION_WRITE_ENTRY, target_id=entry.id)
    db.session.commit()

    return jsonify({"ok": True, "id": entry.id}), 201


# ── 修改（带版本化） ─────────────────────────────────────────────────────────────
@diary_entries_bp.route("/<int:entry_id>", methods=["PUT"])
@login_required
@must_change_check
def update_entry(entry_id):
    """修改日志

    Body（全部可选）:
      - content_text: str
      - mood: str
      - image_urls: list[str]  # 提供则全量替换

    行为：
      1) 把当前内容 + 图片列表快照写入 diary_entry_revisions
      2) 覆盖 entry 字段
      3) 替换图片列表
    """
    user = get_current_user()
    entry = DiaryEntry.query.get_or_404(entry_id)

    if entry.is_deleted:
        return jsonify({"error": "日志已删除"}), 404

    ok, reason = _check_can_edit_entry(user, entry)
    if not ok:
        return jsonify({"error": reason}), 403

    data = request.get_json(silent=True) or {}

    # 1) 快照当前版本
    existing_images = [{"url": img.image_url, "sort_order": img.sort_order} for img in entry.images]
    revision = DiaryEntryRevision(
        entry_id=entry.id,
        revision_number=(entry.revisions.count() + 1),
        prev_content_text=entry.content_text,
        prev_images_json=json.dumps(existing_images, ensure_ascii=False),
        edited_by_id=user.id,
    )
    db.session.add(revision)

    # 2) 覆盖字段
    if "content_text" in data:
        new_content = (data.get("content_text") or "").strip()
        if not new_content:
            return jsonify({"error": "内容不能为空"}), 400
        if len(new_content) > 10000:
            return jsonify({"error": "内容过长（≤10000 字）"}), 400
        entry.content_text = new_content

    if "mood" in data:
        entry.mood = (data.get("mood") or "").strip() or None

    # 3) 替换图片（如提供）
    if "image_urls" in data:
        new_urls = data.get("image_urls") or []
        if len(new_urls) > 9:
            return jsonify({"error": "图片最多 9 张"}), 400
        # 删除旧图
        for img in list(entry.images):
            db.session.delete(img)
        db.session.flush()
        # 新建
        for idx, url in enumerate(new_urls):
            db.session.add(DiaryImage(
                entry_id=entry.id,
                image_url=url,
                image_path=url,
                sort_order=idx,
            ))

    log_action(user.id, DiaryAccessLog.ACTION_EDIT_ENTRY, target_id=entry.id)
    db.session.commit()
    return jsonify({"ok": True, "id": entry.id})


# ── 删除 ────────────────────────────────────────────────────────────────────────
@diary_entries_bp.route("/<int:entry_id>", methods=["DELETE"])
@login_required
@must_change_check
def delete_entry(entry_id):
    """删除日志（软删）"""
    user = get_current_user()
    entry = DiaryEntry.query.get_or_404(entry_id)

    ok, reason = _check_can_delete_entry(user, entry)
    if not ok:
        return jsonify({"error": reason}), 403

    entry.is_deleted = True
    log_action(user.id, DiaryAccessLog.ACTION_DELETE_ENTRY, target_id=entry.id)
    db.session.commit()
    return jsonify({"ok": True})


# ── 修改历史 ─────────────────────────────────────────────────────────────────────
@diary_entries_bp.route("/<int:entry_id>/revisions", methods=["GET"])
@login_required
@must_change_check
def list_revisions(entry_id):
    """列出某条日志的所有历史版本（主人才能看）"""
    user = get_current_user()
    if user.role != "master":
        return jsonify({"error": "只有主人可以查看修改历史"}), 403

    entry = DiaryEntry.query.get_or_404(entry_id)
    revisions = entry.revisions.order_by(DiaryEntryRevision.edited_at.desc()).all()
    return jsonify({
        "entry_id": entry.id,
        "revisions": [r.to_dict() for r in revisions],
    })


# ── 置顶 / 取消置顶 ─────────────────────────────────────────────────────────────
@diary_entries_bp.route("/<int:entry_id>/pin", methods=["POST"])
@login_required
@must_change_check
def toggle_pin(entry_id):
    """主人置顶 / 取消置顶

    Body: { on: bool }
    """
    user = get_current_user()
    if user.role != "master":
        return jsonify({"error": "只有主人可以置顶"}), 403

    entry = DiaryEntry.query.get_or_404(entry_id)
    if entry.is_deleted:
        return jsonify({"error": "日志已删除"}), 404

    data = request.get_json(silent=True) or {}
    on = bool(data.get("on", not entry.is_pinned))

    entry.is_pinned = on
    entry.pinned_at = now_bj() if on else None
    log_action(user.id, "pin_entry" if on else "unpin_entry", target_id=entry.id)
    db.session.commit()
    return jsonify({"ok": True, "is_pinned": entry.is_pinned})
