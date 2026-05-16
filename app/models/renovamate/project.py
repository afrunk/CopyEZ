"""
DecorationProject model

RenovaMate project settings.

Usage:
    from app.models.renovamate import DecorationProject
    project = DecorationProject.query.first()
"""

from app.extensions import db
from app.utils.datetime_utils import now_bj


class DecorationProject(db.Model):
    """
    装修项目模型

    存储装修项目的基本信息、预算和当前阶段。
    第一版只支持单个项目。
    """

    __tablename__ = "decoration_projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    house_area = db.Column(db.String(20), nullable=True)
    style = db.Column(db.String(50), nullable=True)
    total_budget = db.Column(db.Integer, nullable=True, default=0)
    current_stage = db.Column(db.String(20), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=now_bj)
    updated_at = db.Column(db.DateTime, default=now_bj, onupdate=now_bj)

    # 阶段枚举值
    STAGE_CHOICES = [
        ("design", "设计阶段"),
        ("demolition", "拆改阶段"),
        ("water", "水电阶段"),
        ("mud", "泥工阶段"),
        ("wood", "木工阶段"),
        ("paint", "油漆阶段"),
        ("install", "安装阶段"),
        ("soft", "软装阶段"),
    ]

    def stage_display(self):
        """返回当前阶段的中文显示"""
        for key, label in self.STAGE_CHOICES:
            if self.current_stage == key:
                return label
        return self.current_stage or "未设置"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "house_area": self.house_area,
            "style": self.style,
            "total_budget": self.total_budget or 0,
            "current_stage": self.current_stage,
            "stage_display": self.stage_display(),
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
