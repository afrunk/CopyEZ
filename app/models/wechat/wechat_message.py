"""
WeChatMessage model - 聊天消息
"""
from app.extensions import db
from app.utils.datetime_utils import now_bj


class WeChatMessage(db.Model):
    """私密聊天消息"""

    __tablename__ = "wechat_messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("wechat_users.id"), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey("wechat_users.id"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    msg_type = db.Column(db.String(20), default="text", nullable=False, index=True)  # text / image
    image_urls = db.Column(db.JSON, nullable=True)  # ['/static/wechat/uploads/xxx.jpg', ...]
    recalled = db.Column(db.Boolean, default=False, nullable=False)  # 撤回
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=now_bj, nullable=False, index=True)

    sender = db.relationship("WeChatUser", foreign_keys=[sender_id], backref="sent_messages")
    receiver = db.relationship("WeChatUser", foreign_keys=[receiver_id], backref="received_messages")

    def mark_read(self) -> None:
        self.is_read = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "sender_name": self.sender.display_name if self.sender else None,
            "receiver_id": self.receiver_id,
            "content": self.content,
            "msg_type": self.msg_type or "text",
            "image_urls": self.image_urls or [],
            "recalled": self.recalled,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_mine": False,
        }

    def __repr__(self):
        return f"<WeChatMessage {self.id}: {self.sender_id} -> {self.receiver_id}>"
