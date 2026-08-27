"""
BondageDiary comments CRUD (Phase 4).

URL prefix: /diary/api/comments

权限规则：
  - 评论创建：仅主人（master）
  - 评论修改：仅评论作者（master_id == user.id）
  - 评论删除：评论作者 或 日志作者
  - 评论可见：日志作者(pup)看自己日志的所有评论；master 看自己发的所有评论
"""
from flask import (
    Blueprint,
    request,
    jsonify,
)

from app.extensions import db
from app.models.bondage_diary import DiaryComment, DiaryEntry
from app.modules.bondage_diary.auth import (
    login_required,
    must_change_check,
    get_current_user,
)
from app.modules.bondage_diary.access_log import log_action
from app.models.bondage_diary import DiaryAccessLog

diary_comments_bp = Blueprint("diary_comments", __name__, url_prefix="/diary/api/comments")


# ── 权限 ────────────────────────────────────────────────────────────────────────
def _check_can_edit_comment(user, comment):
    if user.role != "master":
        return False, "只有主人可以发点评"
    if comment.master_id != user.id:
        return False, "只能修改自己的点评"
    return True, ""


def _check_can_delete_comment(user, comment):
    if user.role == "master" and comment.master_id == user.id:
        return True, ""
    # 母狗（日志作者）可以删主人对自己的点评
    entry = DiaryEntry.query.get(comment.entry_id)
    if entry and entry.author_id == user.id:
        return True, ""
    return False, "无权删除该点评"


def _can_view_entry(user, entry):
    if entry.is_deleted:
        return False
    if user.role == "master":
        return True
    return entry.author_id == user.id


# ── 创建（仅主人） ──────────────────────────────────────────────────────────────
@diary_comments_bp.route("", methods=["POST"])
@login_required
@must_change_check
def create_comment():
    """主人发点评

    Body:
      - entry_id: int, 必填
      - content_text: str, 必填
    """
    user = get_current_user()
    if user.role != "master":
        return jsonify({"error": "只有主人可以发点评"}), 403

    data = request.get_json(silent=True) or {}
    entry_id = data.get("entry_id")
    content = (data.get("content_text", "") or "").strip()

    if not entry_id:
        return jsonify({"error": "缺少 entry_id"}), 400
    if not content:
        return jsonify({"error": "点评内容不能为空"}), 400
    if len(content) > 2000:
        return jsonify({"error": "点评内容过长（≤2000 字）"}), 400

    entry = DiaryEntry.query.get(entry_id)
    if not entry or entry.is_deleted:
        return jsonify({"error": "日志不存在"}), 404
    if not _can_view_entry(user, entry):
        return jsonify({"error": "无权点评该日志"}), 403

    comment = DiaryComment(
        entry_id=entry.id,
        master_id=user.id,
        content_text=content,
    )
    db.session.add(comment)
    log_action(user.id, DiaryAccessLog.ACTION_WRITE_COMMENT, target_id=comment.id)
    db.session.commit()

    return jsonify({"ok": True, "id": comment.id}), 201


# ── 列表（可选，按 entry 或按 master） ──────────────────────────────────────────
@diary_comments_bp.route("", methods=["GET"])
@login_required
@must_change_check
def list_comments():
    """列点评

    Query:
      - entry_id: int  → 列某条日志下的点评
      - 仅主人才可指定 entry_id；不指定时主人看自己发的所有点评
    """
    user = get_current_user()
    entry_id = request.args.get("entry_id", type=int)

    q = DiaryComment.query.filter_by(is_deleted=False)

    if entry_id:
        entry = DiaryEntry.query.get(entry_id)
        if not entry:
            return jsonify({"error": "日志不存在"}), 404
        if not _can_view_entry(user, entry):
            return jsonify({"error": "无权查看"}), 403
        q = q.filter(DiaryComment.entry_id == entry_id)
    else:
        # 不带 entry_id：主人看自己所有点评；母狗返回空（前端用 entry 接口拿）
        if user.role != "master":
            return jsonify({"comments": []})
        q = q.filter(DiaryComment.master_id == user.id)

    comments = q.order_by(DiaryComment.created_at.desc()).all()
    return jsonify({
        "comments": [c.to_dict() for c in comments],
    })


# ── 修改 ────────────────────────────────────────────────────────────────────────
@diary_comments_bp.route("/<int:comment_id>", methods=["PUT"])
@login_required
@must_change_check
def update_comment(comment_id):
    """修改点评"""
    user = get_current_user()
    comment = DiaryComment.query.get_or_404(comment_id)

    if comment.is_deleted:
        return jsonify({"error": "点评已删除"}), 404

    ok, reason = _check_can_edit_comment(user, comment)
    if not ok:
        return jsonify({"error": reason}), 403

    data = request.get_json(silent=True) or {}
    if "content_text" in data:
        content = (data.get("content_text") or "").strip()
        if not content:
            return jsonify({"error": "点评内容不能为空"}), 400
        if len(content) > 2000:
            return jsonify({"error": "点评内容过长（≤2000 字）"}), 400
        comment.content_text = content

    log_action(user.id, DiaryAccessLog.ACTION_EDIT_COMMENT, target_id=comment.id)
    db.session.commit()
    return jsonify({"ok": True, "id": comment.id})


# ── 删除 ────────────────────────────────────────────────────────────────────────
@diary_comments_bp.route("/<int:comment_id>", methods=["DELETE"])
@login_required
@must_change_check
def delete_comment(comment_id):
    """删除点评（评论作者 或 日志作者）"""
    user = get_current_user()
    comment = DiaryComment.query.get_or_404(comment_id)

    if comment.is_deleted:
        return jsonify({"error": "点评已删除"}), 404

    ok, reason = _check_can_delete_comment(user, comment)
    if not ok:
        return jsonify({"error": reason}), 403

    comment.is_deleted = True
    log_action(user.id, DiaryAccessLog.ACTION_DELETE_COMMENT, target_id=comment.id)
    db.session.commit()
    return jsonify({"ok": True})