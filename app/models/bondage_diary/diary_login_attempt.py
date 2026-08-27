"""
DiaryLoginAttempt model - 登录尝试审计（防爆破）
"""
from app.extensions import db
from app.utils.datetime_utils import now_bj


class DiaryLoginAttempt(db.Model):
    """登录尝试记录

    用于：
    1. 检测单 IP 失败频次（>5/15min → 软锁）
    2. 检测单角色失败频次（>10/1h → 角色锁）
    3. 主人解角色锁时审计
    """

    __tablename__ = "diary_login_attempts"

    id = db.Column(db.Integer, primary_key=True)

    attempted_role = db.Column(db.String(20), nullable=True)
    ip_address = db.Column(db.String(64), nullable=True, index=True)

    success = db.Column(db.Boolean, default=False, nullable=False)

    user_agent = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=now_bj, nullable=False, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "attempted_role": self.attempted_role,
            "ip_address": self.ip_address,
            "success": self.success,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<DiaryLoginAttempt {self.id} role={self.attempted_role} success={self.success}>"
