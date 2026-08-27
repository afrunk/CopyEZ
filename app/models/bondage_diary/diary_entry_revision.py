"""
DiaryEntryRevision model - 日志修改版本记录
"""
from app.extensions import db
from app.utils.datetime_utils import now_bj


class DiaryEntryRevision(db.Model):
    """日志修改历史版本

    每次修改日志，会保留：
    - 上一版 content_text
    - 上一版图片路径快照（JSON）
    - 编辑时间
    - 编辑人
    """

    __tablename__ = "diary_entry_revisions"

    id = db.Column(db.Integer, primary_key=True)

    entry_id = db.Column(
        db.Integer,
        db.ForeignKey("diary_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    revision_number = db.Column(db.Integer, nullable=False)

    prev_content_text = db.Column(db.Text, nullable=False, default="")
    prev_images_json = db.Column(db.Text, nullable=False, default="[]")

    edited_by_id = db.Column(
        db.Integer,
        db.ForeignKey("diary_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    edited_at = db.Column(db.DateTime, default=now_bj, nullable=False, index=True)

    editor = db.relationship("DiaryUser", foreign_keys=[edited_by_id])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "entry_id": self.entry_id,
            "revision_number": self.revision_number,
            "prev_content_text": self.prev_content_text,
            "prev_images_json": self.prev_images_json,
            "edited_by_id": self.edited_by_id,
            "edited_by_name": self.editor.display_name if self.editor else None,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
        }

    def __repr__(self):
        return f"<DiaryEntryRevision {self.id} (entry {self.entry_id}, rev {self.revision_number})>"
