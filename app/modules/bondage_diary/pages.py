"""
BondageDiary pages (HTML rendering).

路由：
  - /diary/                → 时间线（pup / master 都看 pup 的日志）
  - /diary/new             → 写日志表单（pup）
  - /diary/<id>            → 日志详情（pup 自己的 / master 看 pup 的）
  - /diary/<id>/edit       → 修改日志（pup 仅作者）
  - /diary/admin/sessions  → 母狗登录情况（master）
  - /diary/logout          → GET 登出
"""
from flask import (
    Blueprint,
    redirect,
    url_for,
    render_template,
    session,
    abort,
    request,
)

from app.modules.bondage_diary.auth import (
    login_required,
    must_change_check,
    get_current_user,
)
from app.models.bondage_diary import DiaryEntry

diary_pages_bp = Blueprint("diary_pages", __name__, url_prefix="/diary")


def _can_view_entry(user, entry):
    if entry.is_deleted:
        return False
    if user.role == "master":
        return True
    return entry.author_id == user.id


@diary_pages_bp.route("/", methods=["GET"])
@login_required
@must_change_check
def index():
    """时间线主页（所有人）"""
    user = get_current_user()
    return render_template("diary/timeline.html", user=user.to_dict())


@diary_pages_bp.route("/new", methods=["GET"])
@login_required
@must_change_check
def new_entry_page():
    """写日志（仅母狗）"""
    user = get_current_user()
    if user.role != "pup":
        return render_template(
            "diary/placeholder.html",
            user=user.to_dict(),
            message="只有母狗可以写日志",
        )
    return render_template("diary/entry_form.html", user=user.to_dict(), mode="create", entry=None)


@diary_pages_bp.route("/<int:entry_id>", methods=["GET"])
@login_required
@must_change_check
def entry_detail_page(entry_id):
    """日志详情"""
    user = get_current_user()
    entry = DiaryEntry.query.get_or_404(entry_id)
    if not _can_view_entry(user, entry):
        abort(404)
    return render_template(
        "diary/entry_detail.html",
        user=user.to_dict(),
        entry=entry.to_dict(include_content=True),
    )


@diary_pages_bp.route("/<int:entry_id>/edit", methods=["GET"])
@login_required
@must_change_check
def edit_entry_page(entry_id):
    """修改日志（仅作者 pup）"""
    user = get_current_user()
    entry = DiaryEntry.query.get_or_404(entry_id)
    if user.role != "pup" or entry.author_id != user.id:
        abort(403)
    return render_template(
        "diary/entry_form.html",
        user=user.to_dict(),
        mode="edit",
        entry=entry.to_dict(include_content=True),
    )


@diary_pages_bp.route("/admin/sessions", methods=["GET"])
@login_required
@must_change_check
def admin_sessions_page():
    """主人查母狗登录情况"""
    user = get_current_user()
    if user.role != "master":
        return render_template(
            "diary/placeholder.html",
            user=user.to_dict(),
            message="只有主人可以查看",
        )
    return render_template("diary/admin_sessions.html", user=user.to_dict())


@diary_pages_bp.route("/logout", methods=["GET"])
def logout_page():
    """GET 登出"""
    session.pop("diary_user_id", None)
    session.pop("diary_user_role", None)
    return redirect(url_for("diary_auth.login_page"))