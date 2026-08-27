"""WeChat module - 私密聊天"""
from app.modules.wechat.auth import wechat_auth_bp
from app.modules.wechat.chat import wechat_chat_bp
from app.modules.wechat.upload import wechat_upload_bp
from app.modules.wechat.avatar import avatar_bp
from app.modules.wechat.settings_page import wechat_settings_bp
from app.modules.wechat.me_api import me_bp

__all__ = [
    "wechat_auth_bp",
    "wechat_chat_bp",
    "wechat_upload_bp",
    "avatar_bp",
    "wechat_settings_bp",
    "me_bp",
]
