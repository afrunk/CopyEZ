"""
DiaryImage model - 日志图片（一对多）
"""
from app.extensions import db
from app.utils.datetime_utils import now_bj


class DiaryImage(db.Model):
    """日志图片"""

    __tablename__ = "diary_images"

    id = db.Column(db.Integer, primary_key=True)

    entry_id = db.Column(
        db.Integer,
        db.ForeignKey("diary_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    image_path = db.Column(db.String(500), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)

    sort_order = db.Column(db.Integer, default=0, nullable=False)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=now_bj, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "entry_id": self.entry_id,
            "image_path": self.image_path,
            "image_url": self.image_url,
            "sort_order": self.sort_order,
            "width": self.width,
            "height": self.height,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<DiaryImage {self.id} of entry {self.entry_id}>"
