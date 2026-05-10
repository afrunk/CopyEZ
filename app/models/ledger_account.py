"""
Ledger Account model.
"""
from datetime import datetime

from app.extensions import db


class Account(db.Model):
    """Account model: cash, bank cards, Alipay, WeChat Pay, etc. Per-user accounts."""

    __tablename__ = "ledger_accounts"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("ledger_users.id"), nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)
    account_type = db.Column(db.String(20), nullable=False)  # cash, bank, alipay, wechat, other
    initial_balance = db.Column(db.Numeric(12, 2), default=0)
    balance = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    icon = db.Column(db.String(30), default="wallet")
    color = db.Column(db.String(7), default="#10b981")
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = db.relationship("User", back_populates="accounts")
    transactions = db.relationship("Transaction", back_populates="account", lazy="dynamic")

    def __repr__(self):
        return f"<Account {self.name} balance={self.balance}>"
