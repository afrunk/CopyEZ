"""
DecorationCategoryGroup model

RenovaMate category group model.

Usage:
    from app.models.renovamate import DecorationCategoryGroup
    groups = DecorationCategoryGroup.query.filter_by(project_id=project.id).all()
"""

from app.extensions import db
from app.utils.datetime_utils import now_bj


class DecorationCategoryGroup(db.Model):
    """
    装修分类大类模型

    存储装修分类的大类（如：设备系统、家电家具、主材选择等）。
    必须关联到一个装修项目。
    """

    __tablename__ = "decoration_category_groups"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("decoration_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(10), default="🏠")
    description = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    is_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_bj)
    updated_at = db.Column(db.DateTime, default=now_bj, onupdate=now_bj)

    def to_dict(self):
        """转换为字典，用于 JSON 响应"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "icon": self.icon,
            "description": self.description,
            "sort_order": self.sort_order,
            "is_enabled": self.is_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
