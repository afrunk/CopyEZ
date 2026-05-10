"""
Ledger Transaction model.
"""
from datetime import datetime

from app.extensions import db


class Transaction(db.Model):
    """Transaction: income or expense record with owner."""

    __tablename__ = "ledger_transactions"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("ledger_users.id"), nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey("ledger_accounts.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("ledger_categories.id"), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # income, expense
    remark = db.Column(db.String(200), default="")
    transaction_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = db.relationship("User", back_populates="transactions")
    account = db.relationship("Account", back_populates="transactions")
    category = db.relationship("LedgerCategory", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction {self.transaction_type} {self.amount} on {self.transaction_date}>"
