"""
DiaryComment model - 主人的点评
"""
from app.extensions import db
from app.utils.datetime_utils import now_bj


class DiaryComment(db.Model):
    """主人对日志的点评"""

    __tablename__ = "diary_comments"

    id = db.Column(db.Integer, primary_key=True)

    entry_id = db.Column(
        db.Integer,
        db.ForeignKey("diary_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    master_id = db.Column(
        db.Integer,
        db.ForeignKey("diary_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    content_text = db.Column(db.Text, nullable=False, default="")

    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=now_bj, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=now_bj, onupdate=now_bj, nullable=False)

    master = db.relationship("DiaryUser", backref=db.backref("comments", lazy="dynamic"))

    def to_dict(self, include_content: bool = True) -> dict:
        data = {
            "id": self.id,
            "entry_id": self.entry_id,
            "master_id": self.master_id,
            "master_name": self.master.display_name if self.master else None,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_content:
            data["content_text"] = self.content_text
        return data

    def __repr__(self):
        return f"<DiaryComment {self.id} on entry {self.entry_id}>"
