"""
WeChat 用户设置页面
URL prefix: /wechat/settings
"""
from flask import Blueprint, render_template

from app.modules.wechat.auth import login_required

wechat_settings_bp = Blueprint("wechat_settings", __name__, url_prefix="/wechat/settings")


@wechat_settings_bp.route("")
@login_required
def settings_page():
    return render_template("wechat/settings.html")
