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
    avatar_color = db.Column(db.String(7), nullable=False, default="#07C160")
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
            "avatar_color": self.avatar_color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }

    def __repr__(self):
        return f"<WeChatUser {self.id}: {self.display_name} (@{self.username})>"
