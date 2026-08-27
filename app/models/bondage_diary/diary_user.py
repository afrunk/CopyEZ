"""
DiaryUser model - 调教日记参与者（主人 / 母狗）
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.utils.datetime_utils import now_bj


class DiaryUser(db.Model):
    """调教日记参与者"""

    __tablename__ = "diary_users"

    id = db.Column(db.Integer, primary_key=True)

    display_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, index=True)  # 'master' | 'pup'

    password_hash = db.Column(db.String(255), nullable=False)

    avatar = db.Column(db.String(500), nullable=True)

    must_change_password = db.Column(db.Boolean, default=True, nullable=False)
    password_changed_at = db.Column(db.DateTime, nullable=True)

    failed_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=now_bj, nullable=False)
    updated_at = db.Column(db.DateTime, default=now_bj, onupdate=now_bj, nullable=False)

    ROLE_MASTER = "master"
    ROLE_PUP = "pup"
    ROLE_CHOICES = [
        (ROLE_MASTER, "master"),
        (ROLE_PUP, "pup"),
    ]

    # 历史 demo 账号（密码可短于强度策略，方便记忆）
    SHORT_PWD_USERNAMES = {"S", "M"}

    def set_password(self, raw_password: str) -> None:
        """设置密码（bcrypt 哈希）"""
        self.password_hash = generate_password_hash(raw_password)
        self.must_change_password = False
        self.password_changed_at = now_bj()

    def check_password(self, raw_password: str) -> bool:
        """校验密码"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, raw_password)

    def is_locked(self) -> bool:
        """是否处于锁定状态"""
        if not self.locked_until:
            return False
        return self.locked_until > now_bj()

    def lock_for_minutes(self, minutes: int) -> None:
        """锁定指定分钟"""
        from datetime import timedelta
        self.locked_until = now_bj() + timedelta(minutes=minutes)
        self.failed_attempts = 0

    def unlock(self) -> None:
        """解锁"""
        self.locked_until = None
        self.failed_attempts = 0

    def to_dict(self, include_sensitive: bool = False) -> dict:
        data = {
            "id": self.id,
            "display_name": self.display_name,
            "username": self.username,
            "role": self.role,
            "avatar": self.avatar,
            "must_change_password": self.must_change_password,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_sensitive:
            data["failed_attempts"] = self.failed_attempts
            data["locked_until"] = self.locked_until.isoformat() if self.locked_until else None
            data["password_changed_at"] = self.password_changed_at.isoformat() if self.password_changed_at else None
        return data

    def __repr__(self):
        return f"<DiaryUser {self.id}: {self.display_name} ({self.role})>"
