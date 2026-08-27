"""
DiaryEntry model - 调教日志（母狗发的日记主表）
"""
from app.extensions import db
from app.utils.datetime_utils import now_bj


class DiaryEntry(db.Model):
    """调教日志主表"""

    __tablename__ = "diary_entries"

    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(
        db.Integer,
        db.ForeignKey("diary_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    content_text = db.Column(db.Text, nullable=False, default="")
    mood = db.Column(db.String(20), nullable=True)

    is_pinned = db.Column(db.Boolean, default=False, nullable=False, index=True)
    pinned_at = db.Column(db.DateTime, nullable=True)

    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)

    current_revision_id = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=now_bj, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=now_bj, onupdate=now_bj, nullable=False)

    # 复合索引：列表查询常用 (is_deleted, created_at)
    __table_args__ = (
        db.Index("ix_diary_entries_list", "is_deleted", "created_at"),
    )

    author = db.relationship("DiaryUser", backref=db.backref("entries", lazy="dynamic"))
    images = db.relationship(
        "DiaryImage",
        backref="entry",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="DiaryImage.sort_order",
    )
    comments = db.relationship(
        "DiaryComment",
        backref="entry",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="DiaryComment.created_at",
    )
    revisions = db.relationship(
        "DiaryEntryRevision",
        backref="entry",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="DiaryEntryRevision.edited_at.desc()",
    )

    def to_dict(self, include_content: bool = True) -> dict:
        data = {
            "id": self.id,
            "author_id": self.author_id,
            "author_name": self.author.display_name if self.author else None,
            "author_role": self.author.role if self.author else None,
            "mood": self.mood,
            "is_pinned": self.is_pinned,
            "pinned_at": self.pinned_at.isoformat() if self.pinned_at else None,
            "is_deleted": self.is_deleted,
            "image_count": self.images.count() if self.id else 0,
            "comment_count": self.comments.count() if self.id else 0,
            "revision_count": self.revisions.count() if self.id else 0,
            "current_revision_id": self.current_revision_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_content:
            data["content_text"] = self.content_text
            data["images"] = [img.to_dict() for img in self.images]
        return data

    def __repr__(self):
        return f"<DiaryEntry {self.id} by user {self.author_id}>"
