"""
ProgressTask Model - 装修任务进度
"""
from datetime import datetime
from app.extensions import db


class ProgressTask(db.Model):
    """装修任务进度"""
    __tablename__ = 'renovamate_progress_tasks'

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

    title = db.Column(db.String(200), nullable=False)       # 任务名称
    stage = db.Column(db.String(20), default='design')     # 阶段
    status = db.Column(db.String(20), default='pending')   # 状态

    budget_amount = db.Column(db.Integer, default=0)       # 预算金额
    actual_amount = db.Column(db.Integer, default=0)       # 实际花费

    owner = db.Column(db.String(100), default='')          # 负责人
    note = db.Column(db.Text, default='')                  # 备注

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Stage 枚举
    STAGE_CHOICES = [
        ('design', 'design'),
        ('demolition', 'demolition'),
        ('water', 'water'),
        ('mud', 'mud'),
        ('wood', 'wood'),
        ('paint', 'paint'),
        ('install', 'install'),
        ('soft', 'soft'),
    ]

    # Status 枚举
    STATUS_CHOICES = [
        ('pending', 'pending'),
        ('ongoing', 'ongoing'),
        ('review', 'review'),
        ('done', 'done'),
    ]

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'category_id': self.category_id,
            'title': self.title,
            'stage': self.stage,
            'status': self.status,
            'budget_amount': self.budget_amount,
            'actual_amount': self.actual_amount,
            'owner': self.owner,
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<ProgressTask {self.id}: {self.title} [{self.stage}/{self.status}]>'
