"""
WeChatUser model - 私密聊天用户（笨笨 / 蛋蛋）
"""
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.utils.datetime_utils import now_bj


class WeChatUser(db.Model):
    """私密聊天账号"""

    __tablename__ = "wechat_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # 头像类型: color | emoji | image
    avatar_type = db.Column(db.String(20), default="color", nullable=False)
    # avatar_type=color 时用 avatar_color
    avatar_color = db.Column(db.String(7), nullable=False, default="#6366F1")
    # avatar_type=emoji 时用 avatar_emoji
    avatar_emoji = db.Column(db.String(8), nullable=True)
    # avatar_type=image 时用 avatar_url
    avatar_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=now_bj, nullable=False)
    last_seen = db.Column(db.DateTime, nullable=True)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, raw_password)

    def update_last_seen(self) -> None:
        self.last_seen = now_bj()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name,
            "avatar_type": self.avatar_type or "color",
            "avatar_color": self.avatar_color or "#6366F1",
            "avatar_emoji": self.avatar_emoji or None,
            "avatar_url": self.avatar_url or None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }

    def __repr__(self):
        return f"<WeChatUser {self.id}: {self.display_name} (@{self.username})>"
