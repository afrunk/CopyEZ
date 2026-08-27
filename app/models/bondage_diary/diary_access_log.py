"""
DiaryAccessLog model - 访问记录（关键动作审计）
"""
from app.extensions import db
from app.utils.datetime_utils import now_bj


class DiaryAccessLog(db.Model):
    """访问/操作记录

    只记录关键动作：
    - view_list    : 打开时间线列表
    - view_entry   : 查看具体日志
    - write_entry  : 写新日志
    - edit_entry   : 修改日志
    - write_comment: 写点评
    - edit_comment : 修改点评
    """

    __tablename__ = "diary_access_logs"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("diary_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    action_type = db.Column(db.String(30), nullable=False)
    target_id = db.Column(db.Integer, nullable=True)

    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=now_bj, nullable=False, index=True)

    user = db.relationship("DiaryUser", backref=db.backref("access_logs", lazy="dynamic"))

    ACTION_VIEW_LIST = "view_list"
    ACTION_VIEW_ENTRY = "view_entry"
    ACTION_WRITE_ENTRY = "write_entry"
    ACTION_EDIT_ENTRY = "edit_entry"
    ACTION_DELETE_ENTRY = "delete_entry"
    ACTION_WRITE_COMMENT = "write_comment"
    ACTION_EDIT_COMMENT = "edit_comment"
    ACTION_DELETE_COMMENT = "delete_comment"

    ACTION_CHOICES = [
        (ACTION_VIEW_LIST, "浏览时间线"),
        (ACTION_VIEW_ENTRY, "查看日志"),
        (ACTION_WRITE_ENTRY, "写日志"),
        (ACTION_EDIT_ENTRY, "修改日志"),
        (ACTION_DELETE_ENTRY, "删除日志"),
        (ACTION_WRITE_COMMENT, "写点评"),
        (ACTION_EDIT_COMMENT, "修改点评"),
        (ACTION_DELETE_COMMENT, "删除点评"),
    ]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.display_name if self.user else None,
            "user_role": self.user.role if self.user else None,
            "action_type": self.action_type,
            "target_id": self.target_id,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<DiaryAccessLog {self.id} user={self.user_id} action={self.action_type}>"
