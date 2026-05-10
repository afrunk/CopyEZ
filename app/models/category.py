"""
CustomCategory model

User-defined secondary category model for CopyEZ.

Usage:
    from app.models import CustomCategory
    category = CustomCategory.query.first()
"""

from app.extensions import db
from app.utils.datetime_utils import now_bj


class CustomCategory(db.Model):
    """
    用户自定义的二级分类模型

    用于管理素材的分类层级结构。
    """

    __tablename__ = "custom_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    main_category = db.Column(db.String(50), nullable=True)  # 关联的一级分类（可选）
    created_at = db.Column(db.DateTime, default=now_bj)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "main_category": self.main_category
        }
