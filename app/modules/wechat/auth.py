"""

WeChat auth routes.



URL prefix: /wechat/auth

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

)



from app.extensions import db

from app.models.wechat import WeChatUser, WeChatLoginHistory

from app.utils.datetime_utils import now_bj



wechat_auth_bp = Blueprint("wechat_auth", __name__, url_prefix="/wechat/auth")





def login_required(f):

    """要求登录"""

    @wraps(f)

    def decorated(*args, **kwargs):

        if "wechat_user_id" not in session:
            # /wechat/api/* 与 /wechat/push/api/* 都视为 API，返回 401 而非重定向
            # iOS PWA 场景下重定向会让 fetch 收到 302 后报错，订阅永远保存不进去
            if (
                request.path.startswith("/wechat/api/")
                or request.path.startswith("/wechat/push/")
                or request.is_json
                or request.method != "GET"
            ):
                return jsonify({"error": "请先登录", "redirect": "/wechat/auth/login"}), 401
            return redirect(url_for("wechat_auth.login_page", next=request.path))
        return f(*args, **kwargs)

    return decorated





def get_current_user() -> WeChatUser | None:

    uid = session.get("wechat_user_id")

    if not uid:

        return None

    return WeChatUser.query.get(uid)





# ── 页面 ────────────────────────────────────────────────────────────────────

@wechat_auth_bp.route("/login", methods=["GET"])

def login_page():

    """登录页"""

    if "wechat_user_id" in session:

        return redirect(url_for("wechat_chat.chat_page"))

    return render_template("wechat/login.html")





# ── API ─────────────────────────────────────────────────────────────────────

@wechat_auth_bp.route("/api/login", methods=["POST"])

def api_login():

    """登录



    body: { username: "xxx", password: "xxx" }

    """

    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()

    password = data.get("password", "")



    if not username or not password:

        return jsonify({"error": "请输入用户名和密码"}), 400



    user = WeChatUser.query.filter_by(username=username).first()



    if not user or not user.check_password(password):

        return jsonify({"error": "用户名或密码错误"}), 401



    user.update_last_seen()

    # 写入登录历史（表结构异常时不影响登录成功）
    try:
        _now = now_bj()
        db.session.add(WeChatLoginHistory(
            user_id=user.id,
            event_type="login",
            ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
            user_agent=request.headers.get("User-Agent"),
            created_at=_now,
            logged_in_at=_now,
        ))
        db.session.commit()
    except Exception as e:
        # 表缺列等异常不应该阻塞登录，只记录
        db.session.rollback()
        try:
            from flask import current_app
            current_app.logger.warning("写入登录历史失败（不影响登录）: %s", e)
        except Exception:
            pass

    session.permanent = True

    session["wechat_user_id"] = user.id

    session["wechat_username"] = user.username



    next_url = data.get("next") or url_for("wechat_chat.chat_page")



    return jsonify({

        "ok": True,

        "user": user.to_dict(),

        "next": next_url,

    })





@wechat_auth_bp.route("/api/logout", methods=["POST"])

@login_required

def api_logout():

    session.pop("wechat_user_id", None)

    session.pop("wechat_username", None)

    return jsonify({"ok": True})





@wechat_auth_bp.route("/api/me", methods=["GET"])

@login_required

def api_me():

    user = get_current_user()

    return jsonify(user.to_dict())





@wechat_auth_bp.route("/api/heartbeat", methods=["POST"])

@login_required

def api_heartbeat():

    """30秒心跳保活，更新 last_seen"""

    user = get_current_user()

    user.update_last_seen()

    db.session.commit()

    return jsonify({"ok": True})





@wechat_auth_bp.route("/logout", methods=["GET"])

def logout_page():

    """GET 登出"""

    session.pop("wechat_user_id", None)

    session.pop("wechat_username", None)

    return redirect(url_for("wechat_auth.login_page"))

