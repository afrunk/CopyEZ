"""
LedgerEZ Authentication Blueprint.
"""
from flask import Blueprint, request, jsonify, session, redirect, url_for

from app.extensions import db
from app.models import User

auth_bp = Blueprint("ledger_auth", __name__, url_prefix="/ledger/auth")


def login_required(f):
    """Decorator to require login for routes."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "请先登录", "redirect": "/ledger/auth/login"}), 401
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Get current logged in user."""
    if "user_id" in session:
        return User.query.get(session["user_id"])
    return None


def get_current_user_id():
    """Get current logged in user ID."""
    return session.get("user_id")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user."""
    data = request.get_json()
    
    phone = data.get("phone", "").strip()
    password = data.get("password", "")
    nickname = data.get("nickname", "").strip()
    role = data.get("role", "me")
    
    # Validation
    if not phone or len(phone) < 11:
        return jsonify({"error": "请输入正确的手机号"}), 400
    if not password or len(password) < 6:
        return jsonify({"error": "密码至少6位"}), 400
    if not nickname:
        return jsonify({"error": "请输入昵称"}), 400
    if role not in ["me", "partner"]:
        return jsonify({"error": "身份只能是'我'或'他人'"}), 400
    
    # Check if phone already exists
    if User.query.filter_by(phone=phone).first():
        return jsonify({"error": "该手机号已注册"}), 400
    
    # Create user
    user = User(phone=phone, nickname=nickname, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    # Auto login after register
    session.permanent = True
    session["user_id"] = user.id
    
    return jsonify({
        "ok": True,
        "user": {
            "id": user.id,
            "nickname": user.nickname,
            "role": user.role,
            "phone": user.phone
        }
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login user."""
    data = request.get_json()
    
    phone = data.get("phone", "").strip()
    password = data.get("password", "")
    
    if not phone or not password:
        return jsonify({"error": "请输入手机号和密码"}), 400
    
    user = User.query.filter_by(phone=phone).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "手机号或密码错误"}), 401
    
    # Set session
    session.permanent = True
    session["user_id"] = user.id
    
    return jsonify({
        "ok": True,
        "user": {
            "id": user.id,
            "nickname": user.nickname,
            "role": user.role,
            "phone": user.phone
        }
    })


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Logout user."""
    session.pop("user_id", None)
    return jsonify({"ok": True})


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_me():
    """Get current user info."""
    user = get_current_user()
    return jsonify({
        "id": user.id,
        "nickname": user.nickname,
        "role": user.role,
        "phone": user.phone
    })


@auth_bp.route("/check", methods=["GET"])
def check_login():
    """Check if user is logged in."""
    if "user_id" in session:
        user = get_current_user()
        if user:
            return jsonify({
                "logged_in": True,
                "user": {
                    "id": user.id,
                    "nickname": user.nickname,
                    "role": user.role,
                    "phone": user.phone
                }
            })
    return jsonify({"logged_in": False})


@auth_bp.route("/wife", methods=["GET"])
@login_required
def get_wife_info():
    """Get wife user info if exists."""
    wife = User.query.filter_by(role="wife").first()
    if wife:
        return jsonify({
            "has_wife": True,
            "wife": {
                "id": wife.id,
                "nickname": wife.nickname,
                "phone": wife.phone
            }
        })
    return jsonify({"has_wife": False})
