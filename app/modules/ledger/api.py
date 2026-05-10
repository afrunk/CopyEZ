"""
LedgerEZ API routes.
"""
from datetime import datetime, date
from decimal import Decimal

from flask import Blueprint, request, jsonify, session

from app.extensions import db
from app.models import Account, LedgerCategory, Transaction, User

ledger_api_bp = Blueprint("ledger_api", __name__, url_prefix="/ledger/api")


def login_required(f):
    """Decorator to require login."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "请先登录", "redirect": "/ledger/auth/login"}), 401
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    """Get current logged in user."""
    if "user_id" in session:
        return User.query.get(session["user_id"])
    return None


def get_current_user_id():
    """Get current logged in user ID."""
    return session.get("user_id")


# ─── Init API ──────────────────────────────────────────────────────────────

@ledger_api_bp.route("/init", methods=["POST"])
def init_defaults():
    """Seed default categories if none exist."""
    if LedgerCategory.query.count() == 0:
        # Income categories - simplified
        income_cats = [
            ("淘宝收入", "shopping-bag", "#22c55e"),
            ("工资收入", "trending-up", "#16a34a"),
            ("其他收入", "plus-circle", "#6b7280"),
        ]
        # Expense categories - simplified
        expense_cats = [
            ("日常生活", "utensils", "#f97316"),
            ("居住家庭", "home", "#fb923c"),
            ("人情关系", "users", "#8b5cf6"),
            ("电子数码", "smartphone", "#3b82f6"),
            ("淘宝支出", "shopping-cart", "#ec4899"),
            ("大额支出", "credit-card", "#f59e0b"),
            ("其他支出", "more-horizontal", "#94a3b8"),
        ]
        for name, icon, color in income_cats:
            db.session.add(LedgerCategory(name=name, category_type="income", icon=icon, color=color))
        for name, icon, color in expense_cats:
            db.session.add(LedgerCategory(name=name, category_type="expense", icon=icon, color=color))
        db.session.commit()
    return jsonify({"ok": True})


# ─── Account API ──────────────────────────────────────────────────────────────

@ledger_api_bp.route("/accounts", methods=["GET"])
@login_required
def get_accounts():
    """Get accounts for current user."""
    user_id = get_current_user_id()
    accounts = Account.query.filter_by(owner_id=user_id, is_active=True).order_by(Account.sort_order).all()
    return jsonify([
        {
            "id": a.id,
            "name": a.name,
            "account_type": a.account_type,
            "balance": float(a.balance),
            "icon": a.icon,
            "color": a.color,
        }
        for a in accounts
    ])


@ledger_api_bp.route("/accounts", methods=["POST"])
@login_required
def create_account():
    """Create account for current user."""
    data = request.get_json()
    user_id = get_current_user_id()
    account = Account(
        owner_id=user_id,
        name=data["name"],
        account_type=data.get("account_type", "cash"),
        initial_balance=Decimal(str(data.get("initial_balance", 0))),
        icon=data.get("icon", "wallet"),
        color=data.get("color", "#10b981"),
    )
    account.balance = account.initial_balance
    db.session.add(account)
    db.session.commit()
    return jsonify({"id": account.id, "name": account.name}), 201


@ledger_api_bp.route("/accounts/<int:account_id>", methods=["PUT"])
@login_required
def update_account(account_id):
    """Update account - only owner can modify."""
    account = Account.query.get_or_404(account_id)
    if account.owner_id != get_current_user_id():
        return jsonify({"error": "无权修改他人账户"}), 403
    data = request.get_json()
    if "name" in data:
        account.name = data["name"]
    if "icon" in data:
        account.icon = data["icon"]
    if "color" in data:
        account.color = data["color"]
    db.session.commit()
    return jsonify({"id": account.id})


@ledger_api_bp.route("/accounts/<int:account_id>", methods=["DELETE"])
@login_required
def delete_account(account_id):
    """Delete account - only owner can delete."""
    account = Account.query.get_or_404(account_id)
    if account.owner_id != get_current_user_id():
        return jsonify({"error": "无权删除他人账户"}), 403
    account.is_active = False
    db.session.commit()
    return jsonify({"ok": True})


# ─── Category API ─────────────────────────────────────────────────────────────

@ledger_api_bp.route("/categories", methods=["GET"])
def get_categories():
    """Get all categories (public, no auth needed)."""
    cats = LedgerCategory.query.filter_by(is_active=True).order_by(LedgerCategory.sort_order).all()
    return jsonify([
        {
            "id": c.id,
            "name": c.name,
            "category_type": c.category_type,
            "icon": c.icon,
            "color": c.color,
        }
        for c in cats
    ])


@ledger_api_bp.route("/categories", methods=["POST"])
@login_required
def create_category():
    """Create category (admin only for now)."""
    data = request.get_json()
    cat = LedgerCategory(
        name=data["name"],
        category_type=data["category_type"],
        icon=data.get("icon", "tag"),
        color=data.get("color", "#6b7280"),
    )
    db.session.add(cat)
    db.session.commit()
    return jsonify({"id": cat.id, "name": cat.name}), 201


# ─── Transaction API ──────────────────────────────────────────────────────────

@ledger_api_bp.route("/transactions", methods=["GET"])
def get_transactions():
    """Get transactions with owner filtering."""
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    view = request.args.get("view", "me")  # 'me', 'partner', 'combined'
    account_id = request.args.get("account_id", type=int)
    
    user_id = get_current_user_id()
    
    query = Transaction.query
    
    # Filter by view
    if view == "me" and user_id:
        query = query.filter_by(owner_id=user_id)
    elif view == "partner":
        # Get partner's transactions
        current_user = get_current_user()
        if current_user and current_user.partner_id:
            query = query.filter_by(owner_id=current_user.partner_id)
        else:
            query = query.filter_by(owner_id=-1)  # Empty result if not bound
    # 'combined' shows all (no filter)

    if year and month:
        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, month + 1, 1)
        query = query.filter(Transaction.transaction_date >= start,
                             Transaction.transaction_date < end)

    if account_id:
        query = query.filter_by(account_id=account_id)

    transactions = query.order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc()).all()
    
    current_user_id = get_current_user_id()
    return jsonify([
        {
            "id": t.id,
            "owner_id": t.owner_id,
            "owner_name": t.owner.nickname if t.owner else "未知",
            "account_id": t.account_id,
            "account_name": t.account.name if t.account else "未知",
            "account_color": t.account.color if t.account else "#888",
            "category_id": t.category_id,
            "category_name": t.category.name if t.category else "未知",
            "category_icon": t.category.icon if t.category else "circle",
            "category_color": t.category.color if t.category else "#888",
            "amount": float(t.amount),
            "transaction_type": t.transaction_type,
            "remark": t.remark,
            "transaction_date": t.transaction_date.isoformat(),
            "created_at": t.created_at.isoformat(),
            "can_edit": t.owner_id == current_user_id if current_user_id else False,
        }
        for t in transactions
    ])


@ledger_api_bp.route("/transactions", methods=["POST"])
@login_required
def create_transaction():
    """Create transaction - auto assign to current user."""
    data = request.get_json()
    user_id = get_current_user_id()
    
    account = Account.query.get(data["account_id"])
    if not account:
        return jsonify({"error": "账户不存在"}), 400
    
    # Verify account belongs to current user
    if account.owner_id != user_id:
        return jsonify({"error": "只能使用自己的账户"}), 403
    
    trans = Transaction(
        owner_id=user_id,
        account_id=data["account_id"],
        category_id=data["category_id"],
        amount=Decimal(str(data["amount"])),
        transaction_type=data["transaction_type"],
        remark=data.get("remark", ""),
        transaction_date=datetime.strptime(data["transaction_date"], "%Y-%m-%d").date(),
    )
    db.session.add(trans)
    db.session.flush()
    _update_account_balance(account, trans)
    db.session.commit()
    return jsonify({"id": trans.id}), 201


@ledger_api_bp.route("/transactions/<int:trans_id>", methods=["PUT"])
@login_required
def update_transaction(trans_id):
    """Update transaction - only owner can modify."""
    trans = Transaction.query.get_or_404(trans_id)
    if trans.owner_id != get_current_user_id():
        return jsonify({"error": "只能编辑自己的账单"}), 403
    
    data = request.get_json()

    # Rollback from old account
    _reverse_transaction(trans)

    # Apply new
    if "account_id" in data:
        trans.account_id = data["account_id"]
    if "category_id" in data:
        trans.category_id = data["category_id"]
    if "amount" in data:
        trans.amount = Decimal(str(data["amount"]))
    if "transaction_type" in data:
        trans.transaction_type = data["transaction_type"]
    if "remark" in data:
        trans.remark = data["remark"]
    if "transaction_date" in data:
        trans.transaction_date = datetime.strptime(data["transaction_date"], "%Y-%m-%d").date()

    new_account = Account.query.get(trans.account_id)
    db.session.flush()
    _update_account_balance(new_account, trans)
    db.session.commit()
    return jsonify({"id": trans.id})


@ledger_api_bp.route("/transactions/<int:trans_id>", methods=["DELETE"])
@login_required
def delete_transaction(trans_id):
    """Delete transaction - only owner can delete."""
    trans = Transaction.query.get_or_404(trans_id)
    if trans.owner_id != get_current_user_id():
        return jsonify({"error": "只能删除自己的账单"}), 403
    _reverse_transaction(trans)
    db.session.delete(trans)
    db.session.commit()
    return jsonify({"ok": True})


# ─── Stats API ────────────────────────────────────────────────────────────────

@ledger_api_bp.route("/stats/monthly", methods=["GET"])
def monthly_stats():
    """Get monthly stats with owner filtering."""
    year = request.args.get("year", datetime.now().year, type=int)
    month = request.args.get("month", datetime.now().month, type=int)
    view = request.args.get("view", "me")  # 'me', 'partner', 'combined'
    
    user_id = get_current_user_id()
    
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)

    # Build query filter
    date_filter = [
        Transaction.transaction_date >= start,
        Transaction.transaction_date < end
    ]
    
    if view == "me" and user_id:
        date_filter.append(Transaction.owner_id == user_id)
    elif view == "partner":
        # Get partner's stats
        current_user = get_current_user()
        if current_user and current_user.partner_id:
            date_filter.append(Transaction.owner_id == current_user.partner_id)
        else:
            date_filter.append(Transaction.owner_id == -1)  # Empty result

    # Calculate income/expense
    income = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == "income",
        *date_filter
    ).scalar() or 0

    expense = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == "expense",
        *date_filter
    ).scalar() or 0

    # Category breakdown (only for expense)
    cat_breakdown_query = db.session.query(
        LedgerCategory.name,
        LedgerCategory.icon,
        LedgerCategory.color,
        db.func.sum(Transaction.amount).label("total")
    ).join(Transaction).filter(
        Transaction.transaction_type == "expense",
        *date_filter
    ).group_by(LedgerCategory.id).order_by(db.func.sum(Transaction.amount).desc())

    return jsonify({
        "year": year,
        "month": month,
        "view": view,
        "income": float(income),
        "expense": float(expense),
        "balance": float(income) - float(expense),
        "category_breakdown": [
            {"name": c[0], "icon": c[1], "color": c[2], "amount": float(c[3])}
            for c in cat_breakdown_query.all()
        ],
    })


@ledger_api_bp.route("/stats/trend", methods=["GET"])
def monthly_trend():
    """Last 6 months income/expense trend."""
    view = request.args.get("view", "me")
    user_id = get_current_user_id()
    
    today = date.today()
    months = []
    for i in range(5, -1, -1):
        m = (today.month - i - 1) % 12 + 1
        y = today.year - ((today.month - i - 1) // 12)
        start = date(y, m, 1)
        end = date(y + 1 if m == 12 else y, (m % 12) + 1, 1) if m != 12 else date(y + 1, 1, 1)

        date_filter = [
            Transaction.transaction_date >= start,
            Transaction.transaction_date < end
        ]
        
        if view == "me" and user_id:
            date_filter.append(Transaction.owner_id == user_id)
        elif view == "partner":
            current_user = get_current_user()
            if current_user and current_user.partner_id:
                date_filter.append(Transaction.owner_id == current_user.partner_id)
            else:
                date_filter.append(Transaction.owner_id == -1)

        income = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.transaction_type == "income",
            *date_filter
        ).scalar() or 0

        expense = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.transaction_type == "expense",
            *date_filter
        ).scalar() or 0

        months.append({
            "year": y,
            "month": m,
            "label": f"{y}-{m:02d}",
            "income": float(income),
            "expense": float(expense),
        })
    return jsonify(months)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _update_account_balance(account, trans):
    if trans.transaction_type == "income":
        account.balance += trans.amount
    else:
        account.balance -= trans.amount


def _reverse_transaction(trans):
    account = Account.query.get(trans.account_id)
    if not account:
        return
    if trans.transaction_type == "income":
        account.balance -= trans.amount
    else:
        account.balance += trans.amount
