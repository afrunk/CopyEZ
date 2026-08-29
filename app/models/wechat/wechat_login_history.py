"""Successful WeChat login records."""
from app.extensions import db
from app.utils.datetime_utils import now_bj


class WeChatLoginHistory(db.Model):
    __tablename__ = "wechat_login_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("wechat_users.id"),
        nullable=False,
        index=True,
    )
    logged_in_at = db.Column(db.DateTime, default=now_bj, nullable=False, index=True)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)

    user = db.relationship("WeChatUser", backref="login_history")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "logged_in_at": (
                self.logged_in_at.isoformat() if self.logged_in_at else None
            ),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
        }
