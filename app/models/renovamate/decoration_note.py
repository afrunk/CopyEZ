"""
DecorationNote Model - 装修手册记录
"""
from datetime import datetime
from app.extensions import db


class DecorationNote(db.Model):
    """装修手册记录"""
    __tablename__ = 'renovamate_notes'

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
    task_id = db.Column(
        db.Integer,
        db.ForeignKey('renovamate_progress_tasks.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    compare_item_id = db.Column(
        db.Integer,
        db.ForeignKey('renovamate_compare_items.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    stage = db.Column(db.String(20), default='design')     # 装修阶段
    title = db.Column(db.String(200), nullable=False)       # 记录标题
    source_url = db.Column(db.String(500), default='')     # 来源链接
    content = db.Column(db.Text, default='')               # 记录内容

    # JSON 存储的标签列表（第一版用 JSON 文本）
    tags = db.Column(db.Text, default='[]')

    # JSON 存储的图片 URL 列表（第一版用文本占位）
    image_urls = db.Column(db.Text, default='[]')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Stage 枚举: design / demolition / water / mud / wood / paint / install / soft
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

    # 旧值兼容映射: 保存时统一转换为新枚举值
    STAGE_MIGRATION_MAP = {
        'demo': 'demolition',
        'electrical': 'water',
        'tiles': 'mud',
    }

    def normalize_stage(self, stage):
        """兼容旧值并转换为标准枚举"""
        if stage in self.STAGE_MIGRATION_MAP:
            return self.STAGE_MIGRATION_MAP[stage]
        return stage

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'category_id': self.category_id,
            'task_id': self.task_id,
            'compare_item_id': self.compare_item_id,
            'stage': self.stage,
            'title': self.title,
            'source_url': self.source_url,
            'content': self.content,
            'tags': self.tags or '[]',
            'image_urls': self.image_urls or '[]',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<DecorationNote {self.id}: {self.title}>'
