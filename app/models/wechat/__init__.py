"""
WeChat models package

Usage:
    from app.models.wechat import WeChatUser, WeChatMessage
"""
from app.models.wechat.wechat_user import WeChatUser
from app.models.wechat.wechat_message import WeChatMessage
from app.models.wechat.wechat_login_history import WeChatLoginHistory
from app.models.wechat.wechat_push_subscription import WeChatPushSubscription

__all__ = [
    "WeChatUser",
    "WeChatMessage",
    "WeChatLoginHistory",
    "WeChatPushSubscription",
]
