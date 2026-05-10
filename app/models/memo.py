"""
Memo model

Fragmented quick notes model for CopyEZ.

Usage:
    from app.models import Memo
    memo = Memo.query.first()
"""

from app.extensions import db
from app.utils.datetime_utils import now_bj


class Memo(db.Model):
    """
    碎片化随心记模型

    与长文 Note 分表存储，互不影响。
    支持置顶、星标等功能。
    """

    __tablename__ = "memos"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    # 由 #标签 自动提取后存入，多个标签用逗号分隔（展示时再拆分）
    tags = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=now_bj, index=True)
    # 置顶/星标（用于重要 memo 快速归档）
    is_pinned = db.Column(db.Boolean, default=False, nullable=False)
    is_starred = db.Column(db.Boolean, default=False, nullable=False)
    pinned_at = db.Column(db.DateTime, nullable=True)
    starred_at = db.Column(db.DateTime, nullable=True)

    def extract_tags(self):
        """从 content 中提取 #标签 列表"""
        import re
        if not self.content:
            return []
        matches = re.findall(r"#(\S+)", self.content)
        # 去重并保持原有顺序
        seen = set()
        ordered = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                ordered.append(m)
        return ordered

    def to_dict(self):
        tags_list = []
        if self.tags:
            tags_list = [t for t in (s.strip() for s in self.tags.split(",")) if t]
        return {
            "id": self.id,
            "content": self.content,
            "tags": tags_list,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_pinned": bool(self.is_pinned),
            "is_starred": bool(self.is_starred),
            "pinned_at": self.pinned_at.isoformat() if self.pinned_at else None,
            "starred_at": self.starred_at.isoformat() if self.starred_at else None,
        }
