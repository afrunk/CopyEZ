"""
BondageDiary auth routes.

URL prefix: /diary/auth
"""
from functools import wraps

from flask import (
    Blueprint,
    request,
    jsonify,
    session,
    redirect,
    url_for,
    render_template,
    current_app,
)

from app.extensions import db
from app.models.bondage_diary import DiaryUser, DiaryAccessLog
from app.modules.bondage_diary.security import (
    authenticate_by_credentials,
    authenticate_by_password,
    fake_delay,
    record_login_attempt,
    ip_is_soft_locked,
    ip_lock_until,
    increment_user_fail,
    reset_user_fail,
    user_is_locked,
    password_strength_ok,
    GENERIC_LOGIN_ERROR,
)
from app.modules.bondage_diary.access_log import log_action

diary_auth_bp = Blueprint("diary_auth", __name__, url_prefix="/diary/auth")


# ── 装饰器 ──────────────────────────────────────────────────────────────────
def login_required(f):
    """要求登录"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "diary_user_id" not in session:
            # API 返回 JSON；页面跳转登录
            if request.path.startswith("/diary/api/"):
                return jsonify({"error": "请先登录", "redirect": "/diary/auth/login"}), 401
            return redirect(url_for("diary_auth.login_page", next=request.path))
        return f(*args, **kwargs)
    return decorated


def get_current_user() -> DiaryUser | None:
    uid = session.get("diary_user_id")
    if not uid:
        return None
    return DiaryUser.query.get(uid)


def must_change_check(f):
    """拦截 must_change_password"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if user and user.must_change_password:
            # 允许访问改密页本身
            if request.path.endswith("/change_password") or request.path.endswith("/logout"):
                return f(*args, **kwargs)
            # 上传图片 / 写日志等操作不应被拦截（允许先提交，回头再改密）
            _safe_paths = {
                "/diary/api/upload/image",
                "/diary/api/entries",
                "/diary/api/comments",
                "/diary/api/auth/change_password",
                "/diary/api/lock_status",
            }
            for _p in _safe_paths:
                if request.path.startswith(_p):
                    return f(*args, **kwargs)
            # API：返回 403 + redirect
            if request.path.startswith("/diary/api/"):
                return jsonify({"error": "请先修改初始密码", "redirect": "/diary/auth/change_password"}), 403
            return redirect(url_for("diary_auth.change_password_page"))
        return f(*args, **kwargs)
    return decorated


# ── 页面 ────────────────────────────────────────────────────────────────────
@diary_auth_bp.route("/login", methods=["GET"])
def login_page():
    """登录页（单一输入框，无角色按钮）"""
    if "diary_user_id" in session:
        return redirect(url_for("diary_pages.index"))
    return render_template("diary/login.html")


@diary_auth_bp.route("/change_password", methods=["GET"])
@login_required
def change_password_page():
    """改密页"""
    user = get_current_user()
    return render_template(
        "diary/change_password.html",
        user=user.to_dict(),
        must_change=user.must_change_password,
    )


# ── API ────────────────────────────────────────────────────────────────────
@diary_auth_bp.route("/api/login", methods=["POST"])
def api_login():
    """登录

    优先使用账号+密码: { username, password }
    兼容旧字段: { password }  (按密码识别用户)
    """
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password", "") or ""

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    # 1) IP 软锁检查
    if ip_is_soft_locked(ip):
        fake_delay()
        return jsonify({"error": GENERIC_LOGIN_ERROR, "locked": True}), 423

    # 2) 尝试登录（恒定时间近似）
    # 注意：用户传了 username 但为空 ≠ 旧接口,应当直接视为无效
    if username:
        user = authenticate_by_credentials(username, password)
    elif "username" in data:
        # 显式传空 username → 拒绝
        fake_delay()
        return jsonify({"error": GENERIC_LOGIN_ERROR}), 401
    else:
        # 兼容旧版"只输密码"接口
        user = authenticate_by_password(password)

    # 3) 无论成功失败都延迟
    fake_delay()

    if not user:
        # 记录失败（不知道尝试的角色，所以 attempted_role=None）
        record_login_attempt(attempted_role=None, ip=ip, success=False)
        # 通用错误
        return jsonify({"error": GENERIC_LOGIN_ERROR}), 401

    # 4) 成功
    record_login_attempt(attempted_role=user.role, ip=ip, success=True)
    reset_user_fail(user)

    session.permanent = True
    session["diary_user_id"] = user.id
    session["diary_user_role"] = user.role

    # 登录成功埋点（写入操作日志，独立 user_id=0 表示"未登录用户"）
    # 注意：record_login_attempt 已记录登录尝试，这里只记业务侧"登录成功"
    log_action(user.id, "login_success", target_id=None)

    next_url = data.get("next") or url_for("diary_pages.index")

    return jsonify({
        "ok": True,
        "user": user.to_dict(),
        "must_change_password": user.must_change_password,
        "next": next_url,
    })


@diary_auth_bp.route("/api/logout", methods=["POST"])
@login_required
def api_logout():
    session.pop("diary_user_id", None)
    session.pop("diary_user_role", None)
    return jsonify({"ok": True})


@diary_auth_bp.route("/api/me", methods=["GET"])
@login_required
@must_change_check
def api_me():
    user = get_current_user()
    return jsonify(user.to_dict())


@diary_auth_bp.route("/api/change_password", methods=["POST"])
@login_required
def api_change_password():
    """改密

    body: { old_password, new_password }
    """
    user = get_current_user()
    if not user:
        return jsonify({"error": "未登录"}), 401

    data = request.get_json(silent=True) or {}
    old = data.get("old_password", "") or ""
    new = data.get("new_password", "") or ""

    if not user.check_password(old):
        fake_delay()
        return jsonify({"error": "旧密码错误"}), 401

    # 历史 demo 账号(S/M)允许短密码，其他账号仍走强度策略
    if user.username not in DiaryUser.SHORT_PWD_USERNAMES:
        ok, reason = password_strength_ok(new)
        if not ok:
            return jsonify({"error": reason}), 400

    user.set_password(new)
    db.session.commit()
    return jsonify({"ok": True, "must_change_password": False})


@diary_auth_bp.route("/api/lock_status", methods=["GET"])
def api_lock_status():
    """告知前端 IP 是否被锁（用于显示倒计时）。不返回内部细节。"""
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    until_ts = ip_lock_until(ip)
    if until_ts:
        return jsonify({"locked": True, "until": until_ts})
    return jsonify({"locked": False})


# ── 主人重置母狗密码（应急通道） ─────────────────────────────────────────────────────────────
@diary_auth_bp.route("/api/reset_pup_password", methods=["POST"])
@login_required
def api_reset_pup_password():
    """主人重置母狗的密码（二次密码验证 + 操作日志）

    body: { master_password: str, new_password: str }
    """
    user = get_current_user()
    if not user or user.role != "master":
        return jsonify({"error": "只有主人可以重置"}), 403

    data = request.get_json(silent=True) or {}
    master_pwd = data.get("master_password", "") or ""
    new_pwd = data.get("new_password", "") or ""

    fake_delay()
    if not user.check_password(master_pwd):
        log_action(user.id, "reset_pup_password_fail", target_id=None)
        db.session.commit()
        return jsonify({"error": "主人密码错误"}), 401

    ok, reason = password_strength_ok(new_pwd)
    if not ok:
        return jsonify({"error": reason}), 400

    # 找母狗(只重置第一个 active 的)
    target = DiaryUser.query.filter_by(role="pup", is_active=True).first()
    if not target:
        return jsonify({"error": "找不到母狗账号"}), 404

    target.set_password(new_pwd)
    # 历史 demo 账号(S/M)允许短密码，跳过 must_change 强制
    if target.username in DiaryUser.SHORT_PWD_USERNAMES:
        target.must_change_password = False
    else:
        target.must_change_password = True  # 强制母狗下次登录改密
    log_action(user.id, "reset_pup_password", target_id=target.id)
    db.session.commit()
    return jsonify({
        "ok": True,
        "target_user_id": target.id,
        "must_change_password": True,
    })
