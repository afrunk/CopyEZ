"""
BondageDiary access log routes (Phase 5).

提供核心能力：
- log_action(user_id, action_type, target_id=None): 写埋点 helper，外部模块调用
- GET /diary/api/access/logs: 主人查看操作流水（分页）
- GET /diary/api/access/stats: 主人看综合统计

埋点接入点（写到对应模块）：
  - entries.py: write_entry / edit_entry / delete_entry
  - comments.py: write_comment / edit_comment / delete_comment
  - auth.py: 登录成功（登录失败走 DiaryLoginAttempt）

注意：避免循环导入 - 装饰器延迟导入
"""
from flask import (
    Blueprint,
    request,
    jsonify,
)

from app.extensions import db
from app.models.bondage_diary import DiaryAccessLog, DiaryLoginAttempt

diary_access_bp = Blueprint("diary_access", __name__, url_prefix="/diary/api/access")


# ── 公开 helper（其他模块 import 此函数埋点） ────────────────────────────────────
def log_action(user_id, action_type, target_id=None):
    """写一条埋点日志（在调用方事务里 add，统一 commit）

    Args:
        user_id: int, 操作人
        action_type: str, DiaryAccessLog.ACTION_* 之一
        target_id: int|None, 关联对象（如 entry_id / comment_id）
    """
    try:
        log = DiaryAccessLog(
            user_id=user_id,
            action_type=action_type,
            target_id=target_id,
            ip_address=request.remote_addr if request else None,
            user_agent=(request.headers.get("User-Agent", "")[:255]) if request else None,
        )
        db.session.add(log)
    except Exception:
        # 埋点失败不能阻塞主流程
        pass


# ── 装饰器延迟导入避免循环 ─────────────────────────────────────────────────────
def _require_auth():
    from app.modules.bondage_diary.auth import login_required, must_change_check
    return login_required, must_change_check


# ── 主人查操作流水 ─────────────────────────────────────────────────────────────
@diary_access_bp.route("/logs", methods=["GET"])
def list_logs():
    """操作流水（仅主人）

    Query:
      - limit: int, 默认 50
      - offset: int, 默认 0
      - user_id: int, 可选（按用户筛选）
      - action_type: str, 可选
    """
    login_required, must_change_check = _require_auth()

    @login_required
    @must_change_check
    def inner():
        from app.modules.bondage_diary.auth import get_current_user
        user = get_current_user()
        if user.role != "master":
            return jsonify({"error": "只有主人可查看操作日志"}), 403

        limit = min(int(request.args.get("limit", 50)), 200)
        offset = max(int(request.args.get("offset", 0)), 0)
        user_id = request.args.get("user_id", type=int)
        action_type = request.args.get("action_type")

        q = DiaryAccessLog.query
        if user_id:
            q = q.filter(DiaryAccessLog.user_id == user_id)
        if action_type:
            q = q.filter(DiaryAccessLog.action_type == action_type)

        total = q.count()
        logs = q.order_by(DiaryAccessLog.created_at.desc()).limit(limit).offset(offset).all()

        login_failures = DiaryLoginAttempt.query.filter_by(success=False).count()

        return jsonify({
            "logs": [log.to_dict() for log in logs],
            "total": total,
            "login_failures": login_failures,
            "has_more": (offset + len(logs)) < total,
        })
    return inner()


@diary_access_bp.route("/stats", methods=["GET"])
def get_stats():
    """综合统计（仅主人）"""
    login_required, must_change_check = _require_auth()

    @login_required
    @must_change_check
    def inner():
        from app.modules.bondage_diary.auth import get_current_user
        user = get_current_user()
        if user.role != "master":
            return jsonify({"error": "只有主人可查看统计"}), 403

        from sqlalchemy import func
        from app.models.bondage_diary import (
            DiaryEntry, DiaryComment, DiaryUser,
        )

        rows = (
            db.session.query(
                DiaryAccessLog.user_id,
                DiaryAccessLog.action_type,
                func.count(DiaryAccessLog.id),
            )
            .group_by(DiaryAccessLog.user_id, DiaryAccessLog.action_type)
            .all()
        )

        user_summary = {}
        for uid, action, count in rows:
            user_summary.setdefault(uid, {})[action] = count

        entry_total = DiaryEntry.query.filter_by(is_deleted=False).count()
        comment_total = DiaryComment.query.filter_by(is_deleted=False).count()

        from datetime import timedelta
        from app.utils.datetime_utils import now_bj
        since = now_bj() - timedelta(days=30)
        recent_count = DiaryAccessLog.query.filter(DiaryAccessLog.created_at >= since).count()

        login_fail_total = DiaryLoginAttempt.query.filter_by(success=False).count()
        login_fail_recent = DiaryLoginAttempt.query.filter(
            DiaryLoginAttempt.success == False,
            DiaryLoginAttempt.created_at >= since,
        ).count()

        return jsonify({
            "user_summary": user_summary,
            "entry_total": entry_total,
            "comment_total": comment_total,
            "recent_actions_30d": recent_count,
            "login_failures_total": login_fail_total,
            "login_failures_30d": login_fail_recent,
            "all_users": [
                {"id": u.id, "display_name": u.display_name, "role": u.role}
                for u in DiaryUser.query.filter_by(is_active=True).all()
            ],
        })
    return inner()


@diary_access_bp.route("/action-types", methods=["GET"])
def list_action_types():
    """返回所有合法的 action_type 与中文名"""
    login_required, must_change_check = _require_auth()

    @login_required
    @must_change_check
    def inner():
        return jsonify({
            "actions": [
                {"type": k, "label": v}
                for k, v in DiaryAccessLog.ACTION_CHOICES
            ]
        })
    return inner()