"""WeChat login/logout history records."""
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
    # 登录/登出事件类型，保持与线上数据库实际列一致
    event_type = db.Column(db.String(20), nullable=False, default="login")
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=now_bj, nullable=False, index=True)
    # 旧模型里是 NOT NULL；线上表里实际为 NULL。改为可选以兼容历史数据。
    logged_in_at = db.Column(db.DateTime, nullable=True, index=True)

    user = db.relationship("WeChatUser", backref="login_history")

    def to_dict(self) -> dict:
        # 前端按 created_at 渲染时间；如果同时存在 logged_in_at（部分旧记录会补齐）也可显示
        ts = self.logged_in_at or self.created_at
        return {
            "id": self.id,
            "event_type": self.event_type,
            "logged_in_at": self.logged_in_at.isoformat() if self.logged_in_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            # 兼容字段：给前端一个统一的时间键
            "time": ts.isoformat() if ts else None,
        }
