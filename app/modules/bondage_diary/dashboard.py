"""
BondageDiary dashboard routes (Phase 6).

- GET /diary/api/dashboard/summary: 主人仪表盘 / 母狗概览（一接口两种视野）
- GET /diary/api/entries/uncommented: 主人待点评的日志
- GET /diary/api/notifications/unread: 母狗未读：被点评 / 被修改 的日志 id
- POST /diary/api/notifications/seen: 母狗确认已读
"""
from flask import (
    Blueprint,
    request,
    jsonify,
    session,
)

from app.extensions import db
from app.models.bondage_diary import (
    DiaryAccessLog, DiaryLoginAttempt, DiaryComment,
    DiaryEntry, DiaryEntryRevision, DiaryUser,
)
from app.utils.datetime_utils import now_bj

diary_dashboard_bp = Blueprint("diary_dashboard", __name__, url_prefix="/diary/api")
diary_notifications_bp = Blueprint("diary_notifications", __name__, url_prefix="/diary/api/notifications")


# ── 装饰器延迟导入避免循环 ─────────────────────────────────────────────────────
def _require_auth():
    from app.modules.bondage_diary.auth import login_required, must_change_check
    return login_required, must_change_check


def _current_user():
    from app.modules.bondage_diary.auth import get_current_user
    return get_current_user()


# ── 主人查母狗登录情况 ─────────────────────────────────────────────────────────
@diary_dashboard_bp.route("/admin/sessions", methods=["GET"])
def admin_sessions():
    """主人看母狗的登录情况

    Query:
      - limit: int, 默认 30
      - include_failed: bool, 默认 true
    """
    login_required, must_change_check = _require_auth()

    @login_required
    @must_change_check
    def inner():
        user = _current_user()
        if user.role != "master":
            return jsonify({"error": "只有主人可查看"}), 403

        limit = min(int(request.args.get("limit", 30)), 100)
        include_failed = request.args.get("include_failed", "true").lower() != "false"

        # 母狗账号
        pups = DiaryUser.query.filter_by(role="pup", is_active=True).all()

        # 母狗账号状态
        pup_status = []
        for p in pups:
            locked_until = p.locked_until.isoformat() if p.locked_until else None
            pwd_changed = p.password_changed_at.isoformat() if p.password_changed_at else None
            failed_attempts = p.failed_attempts or 0
            pup_status.append({
                "user_id": p.id,
                "display_name": p.display_name,
                "is_active": p.is_active,
                "must_change_password": p.must_change_password,
                "password_changed_at": pwd_changed,
                "failed_attempts": failed_attempts,
                "is_locked": p.is_locked(),
                "locked_until": locked_until,
            })

        # 最近登录尝试
        q = DiaryLoginAttempt.query
        if not include_failed:
            q = q.filter(DiaryLoginAttempt.success == True)
        attempts = q.order_by(DiaryLoginAttempt.created_at.desc()).limit(limit).all()

        # 统计
        total_success = DiaryLoginAttempt.query.filter_by(success=True).count()
        total_failed = DiaryLoginAttempt.query.filter_by(success=False).count()

        # 最近 30 天失败
        from datetime import timedelta
        from app.utils.datetime_utils import now_bj
        since_30d = now_bj() - timedelta(days=30)
        failed_30d = DiaryLoginAttempt.query.filter(
            DiaryLoginAttempt.success == False,
            DiaryLoginAttempt.created_at >= since_30d,
        ).count()

        # 最近一次成功登录
        last_success = (
            DiaryLoginAttempt.query.filter_by(success=True)
            .order_by(DiaryLoginAttempt.created_at.desc())
            .first()
        )
        last_failed = (
            DiaryLoginAttempt.query.filter_by(success=False)
            .order_by(DiaryLoginAttempt.created_at.desc())
            .first()
        )

        return jsonify({
            "pup_status": pup_status,
            "attempts": [a.to_dict() for a in attempts],
            "stats": {
                "total_success": total_success,
                "total_failed": total_failed,
                "failed_30d": failed_30d,
                "last_success_at": last_success.created_at.isoformat() if last_success and last_success.created_at else None,
                "last_success_ip": last_success.ip_address if last_success else None,
                "last_failed_at": last_failed.created_at.isoformat() if last_failed and last_failed.created_at else None,
                "last_failed_ip": last_failed.ip_address if last_failed else None,
            },
        })
    return inner()


# ── 仪表盘 / 概览（一接口两视野） ─────────────────────────────────────────────
@diary_dashboard_bp.route("/dashboard/summary", methods=["GET"])
def dashboard_summary():
    """主人仪表盘 / 母狗概览"""
    login_required, must_change_check = _require_auth()

    @login_required
    @must_change_check
    def inner():
        user = _current_user()
        if user.role == "master":
            return _master_dashboard()
        else:
            return _pup_overview()
    return inner()


def _master_dashboard():
    """主人仪表盘：待点评 / 最近点评 / 活跃度 / 紧急"""
    # 1) 待点评：母狗所有未评论的日志
    uncommented = (
        db.session.query(DiaryEntry)
        .join(DiaryUser, DiaryUser.id == DiaryEntry.author_id)
        .filter(DiaryUser.role == "pup")
        .filter(DiaryEntry.is_deleted == False)
        .outerjoin(DiaryComment, (DiaryComment.entry_id == DiaryEntry.id) & (DiaryComment.is_deleted == False))
        .filter(DiaryComment.id == None)
        .order_by(DiaryEntry.created_at.desc())
        .limit(5)
        .all()
    )
    uncommented_total = (
        db.session.query(DiaryEntry)
        .join(DiaryUser, DiaryUser.id == DiaryEntry.author_id)
        .filter(DiaryUser.role == "pup")
        .filter(DiaryEntry.is_deleted == False)
        .outerjoin(DiaryComment, (DiaryComment.entry_id == DiaryEntry.id) & (DiaryComment.is_deleted == False))
        .filter(DiaryComment.id == None)
        .count()
    )

    # 2) 最近点评（我发的）
    recent_comments = (
        DiaryComment.query
        .filter_by(master_id=1, is_deleted=False)  # 主人自己
        .order_by(DiaryComment.created_at.desc())
        .limit(5)
        .all()
    )

    # 3) 母狗活跃度（最近 7 天写了多少日志）
    from datetime import timedelta
    since_7d = now_bj() - timedelta(days=7)
    pup_recent_entries = (
        DiaryEntry.query
        .join(DiaryUser, DiaryUser.id == DiaryEntry.author_id)
        .filter(DiaryUser.role == "pup")
        .filter(DiaryEntry.created_at >= since_7d)
        .filter(DiaryEntry.is_deleted == False)
        .count()
    )

    # 4) 紧急：登录失败计数（30 天 / 总）
    since_30d = now_bj() - timedelta(days=30)
    login_fail_30d = DiaryLoginAttempt.query.filter(
        DiaryLoginAttempt.success == False,
        DiaryLoginAttempt.created_at >= since_30d,
    ).count()

    # 5) 主人账号是否需要提醒改密（这里不会,但预留接口）
    pup_users = DiaryUser.query.filter_by(role="pup", is_active=True).all()
    must_change_count = sum(1 for u in pup_users if u.must_change_password)

    return jsonify({
        "view": "master",
        "uncommented_entries": [e.to_dict() for e in uncommented],
        "uncommented_total": uncommented_total,
        "recent_comments": [c.to_dict() for c in recent_comments],
        "pup_recent_entries_7d": pup_recent_entries,
        "login_failures_30d": login_fail_30d,
        "pup_must_change_count": must_change_count,
    })


def _pup_overview():
    """母狗概览：自己日志的待办 / 主人对我的近期点评"""
    user = _current_user()

    # 1) 我的日志里被主人最近点评的
    recent_comments_on_me = (
        db.session.query(DiaryComment)
        .join(DiaryEntry, DiaryEntry.id == DiaryComment.entry_id)
        .filter(DiaryEntry.author_id == user.id)
        .filter(DiaryEntry.is_deleted == False)
        .filter(DiaryComment.is_deleted == False)
        .order_by(DiaryComment.created_at.desc())
        .limit(5)
        .all()
    )

    # 2) 我有多少日志
    my_entries = DiaryEntry.query.filter_by(author_id=user.id, is_deleted=False).count()

    # 3) 主人最近对我日志的修改（这里没有,因为母狗自己改自己的）
    # 改用: 我的日志被pin的 / 被comment的
    pinned_mine = DiaryEntry.query.filter_by(author_id=user.id, is_deleted=False, is_pinned=True).count()

    # 4) 未读数（被点评但我没看到）
    last_seen_raw = session.get("diary_notif_last_seen", 0)
    last_seen = last_seen_raw or 0
    unread_count = (
        db.session.query(DiaryComment)
        .join(DiaryEntry, DiaryEntry.id == DiaryComment.entry_id)
        .filter(DiaryEntry.author_id == user.id)
        .filter(DiaryComment.created_at >= _datetime_from_ts(last_seen))
        .filter(DiaryComment.is_deleted == False)
        .count()
    )

    # 5) 我有待改密码的标志
    must_change = user.must_change_password

    return jsonify({
        "view": "pup",
        "my_entries_total": my_entries,
        "pinned_mine": pinned_mine,
        "recent_comments_on_me": [
            {**c.to_dict(), "entry_mood": c.entry.mood if c.entry else None}
            for c in recent_comments_on_me
        ],
        "unread_notifications": unread_count,
        "must_change_password": must_change,
    })


def _datetime_from_ts(ts):
    """把 epoch 戳转 naive BJ datetime (与 DB 一致)"""
    from datetime import datetime, timezone, timedelta
    if not ts:
        return datetime(1970, 1, 1)
    # epoch 是 UTC，转成 BJ (+8) 然后去掉 tzinfo
    bj = datetime.fromtimestamp(ts, tz=timezone.utc) + timedelta(hours=8)
    return bj.replace(tzinfo=None)


# ── 主人待点评列表 ─────────────────────────────────────────────────────────────
@diary_dashboard_bp.route("/entries/uncommented", methods=["GET"])
def list_uncommented():
    """主人待点评的日志列表"""
    login_required, must_change_check = _require_auth()

    @login_required
    @must_change_check
    def inner():
        user = _current_user()
        if user.role != "master":
            return jsonify({"error": "只有主人可查看待点评"}), 403

        limit = min(int(request.args.get("limit", 30)), 100)
        offset = max(int(request.args.get("offset", 0)), 0)

        q = (
            db.session.query(DiaryEntry)
            .join(DiaryUser, DiaryUser.id == DiaryEntry.author_id)
            .filter(DiaryUser.role == "pup")
            .filter(DiaryEntry.is_deleted == False)
            .outerjoin(DiaryComment, (DiaryComment.entry_id == DiaryEntry.id) & (DiaryComment.is_deleted == False))
            .filter(DiaryComment.id == None)
        )
        total = q.count()
        entries = q.order_by(DiaryEntry.created_at.desc()).limit(limit).offset(offset).all()

        return jsonify({
            "entries": [e.to_dict() for e in entries],
            "total": total,
            "has_more": (offset + len(entries)) < total,
        })
    return inner()


# ── 母狗未读 ────────────────────────────────────────────────────────────────────
@diary_notifications_bp.route("/unread", methods=["GET"])
def unread_notifications():
    """母狗未读：被点评过的日志 id 列表 + 计数"""
    login_required, must_change_check = _require_auth()

    @login_required
    @must_change_check
    def inner():
        user = _current_user()
        if user.role != "pup":
            return jsonify({"unread_count": 0, "entry_ids": []})

        since = _datetime_from_ts(session.get("diary_notif_last_seen", 0))

        # 我所有日志里、在 since 之后被点评的（合并成 entry_id 列表）
        rows = (
            db.session.query(DiaryComment.entry_id, db.func.count(DiaryComment.id))
            .join(DiaryEntry, DiaryEntry.id == DiaryComment.entry_id)
            .filter(DiaryEntry.author_id == user.id)
            .filter(DiaryComment.created_at >= since)
            .filter(DiaryComment.is_deleted == False)
            .group_by(DiaryComment.entry_id)
            .all()
        )

        # 详细 list（按 entry_id 不重复）
        detail = []
        for entry_id, cnt in rows:
            c = (
                DiaryComment.query
                .filter_by(entry_id=entry_id, is_deleted=False)
                .order_by(DiaryComment.created_at.desc())
                .first()
            )
            if c:
                detail.append({
                    "entry_id": entry_id,
                    "comment_count": cnt,
                    "latest_comment_id": c.id,
                    "latest_content": c.content_text[:80],
                    "latest_at": c.created_at.isoformat() if c.created_at else None,
                })

        total = sum(cnt for _, cnt in rows)
        return jsonify({
            "unread_count": total,
            "entry_ids": [r[0] for r in rows],
            "details": detail,
        })
    return inner()


@diary_notifications_bp.route("/seen", methods=["POST"])
def mark_seen():
    """母狗标记已读（写过去时间戳，避免和刚好同时刻的评论竞争）"""
    login_required, must_change_check = _require_auth()

    @login_required
    @must_change_check
    def inner():
        from datetime import timedelta
        session["diary_notif_last_seen"] = (now_bj() - timedelta(seconds=1)).timestamp()
        return jsonify({"ok": True})
    return inner()