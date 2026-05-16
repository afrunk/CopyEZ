"""
DecorationCategory model

RenovaMate category model for sub-categories.

Usage:
    from app.models.renovamate import DecorationCategory
    categories = DecorationCategory.query.filter_by(project_id=project.id).all()
"""

from app.extensions import db
from app.utils.datetime_utils import now_bj


class DecorationCategory(db.Model):
    """
    装修子分类模型

    存储装修分类的子分类（如：中央空调、新风系统、冰箱等）。
    必须关联到一个装修项目和一个分类大类。
    """

    __tablename__ = "decoration_categories"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("decoration_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("decoration_category_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(10), default="📦")
    budget = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default="not_started")
    view_mode = db.Column(db.String(20), default="card")
    description = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    is_enabled = db.Column(db.Boolean, default=True)

    # 选中的方案 ID（关联到 CompareItem）
    selected_plan_id = db.Column(
        db.Integer,
        db.ForeignKey("renovamate_compare_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    created_at = db.Column(db.DateTime, default=now_bj)
    updated_at = db.Column(db.DateTime, default=now_bj, onupdate=now_bj)

    def to_dict(self):
        """转换为字典，用于 JSON 响应"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "group_id": self.group_id,
            "name": self.name,
            "icon": self.icon,
            "budget": self.budget,
            "status": self.status,
            "view_mode": self.view_mode,
            "description": self.description,
            "sort_order": self.sort_order,
            "is_enabled": self.is_enabled,
            "selected_plan_id": self.selected_plan_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def get_status_display(status):
        """获取状态的中文显示"""
        status_map = {
            "not_started": "未开始",
            "comparing": "比价中",
            "selected": "已选方案",
            "ongoing": "进行中",
            "pending_confirm": "待确认"
        }
        return status_map.get(status, status)

    @staticmethod
    def get_view_mode_display(view_mode):
        """获取展示方式的中文显示"""
        mode_map = {
            "table": "表格模式",
            "card": "卡片模式",
            "list": "清单模式"
        }
        return mode_map.get(view_mode, view_mode)
