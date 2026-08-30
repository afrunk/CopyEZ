"""
WeChatPushSubscription - Web Push 订阅记录

每条记录代表「某个 wechat 用户在某台设备上订阅了推送」。
笨笨和蛋蛋各可以有多台设备订阅，每条消息会向该用户所有订阅广播。

字段：
- user_id        wechat_users.id 的归属
- endpoint       浏览器 Service Worker 注册的推送 URL（autopush / FCM 等）
- p256dh         加密公钥（base64url）
- auth           共享密钥（base64url）
- user_agent     UA 摘要，用于排查「我手机订阅了几次」
- created_at     订阅时间
- last_used_at   最近一次推送触发时间（用于清理过期订阅）
"""
from datetime import datetime
from app.extensions import db


class WeChatPushSubscription(db.Model):
    __tablename__ = "wechat_push_subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    endpoint = db.Column(db.String(500), nullable=False, unique=True)
    p256dh = db.Column(db.String(200), nullable=False)
    auth = db.Column(db.String(100), nullable=False)
    user_agent = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "endpoint": self.endpoint,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }

    def __repr__(self):
        return f"<WeChatPushSubscription {self.id} user={self.user_id}>"
