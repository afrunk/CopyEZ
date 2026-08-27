"""WeChat module - 私密聊天"""
from app.modules.wechat.auth import wechat_auth_bp
from app.modules.wechat.chat import wechat_chat_bp

__all__ = [
    "wechat_auth_bp",
    "wechat_chat_bp",
]
