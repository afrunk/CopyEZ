"""
Ledger Category model.
"""
from datetime import datetime

from app.extensions import db


class LedgerCategory(db.Model):
    """Category for income/expense transactions."""

    __tablename__ = "ledger_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    category_type = db.Column(db.String(10), nullable=False)  # income, expense
    icon = db.Column(db.String(30), default="tag")
    color = db.Column(db.String(7), default="#6b7280")
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship("Transaction", back_populates="category", lazy="dynamic")

    def __repr__(self):
        return f"<LedgerCategory {self.name} type={self.category_type}>"
