"""LedgerEZ Blueprint"""
from datetime import datetime
import random
from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from app.extensions import db
from app.models import User

ledger_bp = Blueprint("ledger", __name__, url_prefix="/ledger")


def login_required(f):
    """Decorator to require login."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("ledger.login_page"))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Get current logged in user."""
    if "user_id" in session:
        return User.query.get(session["user_id"])
    return None


@ledger_bp.route("/")
@login_required
def ledger_home():
    """LedgerEZ 首页"""
    return render_template("ledger/index.html")


@ledger_bp.route("/bills")
@login_required
def ledger_bills():
    """账单列表"""
    return render_template("ledger/bills.html")


@ledger_bp.route("/stats")
@login_required
def ledger_stats():
    """统计分析"""
    return render_template("ledger/stats.html")


@ledger_bp.route("/settings")
@login_required
def ledger_settings():
    """设置页"""
    return render_template("ledger/settings.html")


@ledger_bp.route("/login")
def login_page():
    """登录页"""
    # If already logged in, redirect to home
    if "user_id" in session:
        return redirect(url_for("ledger.ledger_home"))
    return render_template("ledger/login.html")


@ledger_bp.route("/logout")
def logout_page():
    """退出登录"""
    session.pop("user_id", None)
    return redirect(url_for("ledger.login_page"))


# ─── Bind Partner APIs ──────────────────────────────────────────────────────────

@ledger_bp.route("/api/generate-bind-code", methods=["POST"])
def generate_bind_code():
    """Generate a 6-digit bind code for current user."""
    user = get_current_user()
    if not user:
        return jsonify({"error": "请先登录"}), 401
    
    # Generate 6-digit code
    code = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow()
    
    user.bind_code = code
    user.bind_code_expires_at = expires_at
    db.session.commit()
    
    return jsonify({
        "code": code,
        "expires_in": 300  # 5 minutes
    })


@ledger_bp.route("/api/bind-partner", methods=["POST"])
def bind_partner():
    """Bind with another user using their phone and bind code."""
    user = get_current_user()
    if not user:
        return jsonify({"error": "请先登录"}), 401
    
    data = request.get_json()
    partner_phone = data.get("partner_phone", "").strip()
    partner_code = data.get("partner_code", "").strip()
    
    # Validation
    if not partner_phone or not partner_code:
        return jsonify({"error": "请填写对方手机号和绑定码"}), 400
    
    if len(partner_phone) != 11:
        return jsonify({"error": "请输入正确的11位手机号"}), 400
    
    if not partner_phone.isdigit():
        return jsonify({"error": "手机号只能包含数字"}), 400
    
    # Check self-bind
    if user.phone == partner_phone:
        return jsonify({"error": "不能绑定自己"}), 400
    
    # Check if already bound
    if user.partner_id:
        return jsonify({"error": "你已绑定账本，请先解除绑定"}), 400
    
    # Find partner user
    partner = User.query.filter_by(phone=partner_phone).first()
    if not partner:
        return jsonify({"error": "该用户不存在，请先让对方注册"}), 400
    
    # Check partner already bound to someone else
    if partner.partner_id and partner.partner_id != user.id:
        return jsonify({"error": "该用户已绑定其他账本"}), 400
    
    # Check bind code
    if not partner.bind_code or partner.bind_code != partner_code:
        return jsonify({"error": "绑定码错误"}), 400
    
    # Check bind code expired (5 minutes)
    if not partner.bind_code_expires_at:
        return jsonify({"error": "绑定码已失效，请让对方重新生成"}), 400
    
    time_diff = (datetime.utcnow() - partner.bind_code_expires_at).total_seconds()
    if time_diff > 300:  # 5 minutes
        return jsonify({"error": "绑定码已过期（有效期5分钟），请让对方重新生成"}), 400
    
    # Perform binding - bidirectional
    user.partner_id = partner.id
    partner.partner_id = user.id
    
    # Clear bind codes
    user.bind_code = None
    user.bind_code_expires_at = None
    partner.bind_code = None
    partner.bind_code_expires_at = None
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "partner": {
            "nickname": partner.nickname,
            "phone": partner.phone
        }
    })


@ledger_bp.route("/api/unbind-partner", methods=["POST"])
def unbind_partner():
    """Unbind with current partner."""
    user = get_current_user()
    if not user:
        return jsonify({"error": "请先登录"}), 401
    
    if not user.partner_id:
        return jsonify({"error": "未绑定账本"}), 400
    
    partner = User.query.get(user.partner_id)
    
    # Clear both sides
    user.partner_id = None
    if partner:
        partner.partner_id = None
    
    db.session.commit()
    
    return jsonify({"success": True})


@ledger_bp.route("/api/bind-status", methods=["GET"])
def bind_status():
    """Get current user's binding status."""
    user = get_current_user()
    if not user:
        return jsonify({"error": "请先登录"}), 401
    
    if user.partner_id:
        partner = User.query.get(user.partner_id)
        if partner:
            return jsonify({
                "bound": True,
                "partner": {
                    "nickname": partner.nickname,
                    "phone": partner.phone
                }
            })
    
    return jsonify({"bound": False})
