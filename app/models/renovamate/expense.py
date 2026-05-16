"""
Expense Model - 装修实际花费记录
"""
from datetime import datetime
from app.extensions import db


class Expense(db.Model):
    """装修实际花费记录"""
    __tablename__ = 'renovamate_expenses'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey('decoration_projects.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('decoration_categories.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    compare_item_id = db.Column(
        db.Integer,
        db.ForeignKey('renovamate_compare_items.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    title = db.Column(db.String(200), default='')          # 支出名称
    amount = db.Column(db.Integer, default=0)               # 金额（分）
    pay_date = db.Column(db.Date, nullable=True)           # 支付日期
    pay_method = db.Column(db.String(50), default='')       # 支付方式
    vendor = db.Column(db.String(200), default='')         # 收款方/商家
    receipt_image = db.Column(db.String(500), default='')  # 收据图片（占位）
    note = db.Column(db.Text, default='')                  # 备注

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'category_id': self.category_id,
            'compare_item_id': self.compare_item_id,
            'title': self.title,
            'amount': self.amount,
            'pay_date': self.pay_date.isoformat() if self.pay_date else None,
            'pay_method': self.pay_method,
            'vendor': self.vendor,
            'receipt_image': self.receipt_image,
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<Expense {self.id}: {self.title} ¥{self.amount}>'
