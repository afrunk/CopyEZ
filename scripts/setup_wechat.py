"""
WeChat 初始化脚本

用法：
    python scripts/setup_wechat.py

功能：
    - 创建两个中文登录账号：笨笨 / 123456，蛋蛋 / 123456
    - 账号已存在时同步显示名和初始密码（幂等）
"""
import importlib.util
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.extensions import db
from app.models.wechat import WeChatUser


ACCOUNTS = (
    ("笨笨", "笨笨", "123456"),
    ("蛋蛋", "蛋蛋", "123456"),
)


def init_user(username: str, display_name: str, password: str) -> WeChatUser:
    """初始化中文账号，兼容旧版本使用英文登录名的记录。"""
    user = WeChatUser.query.filter_by(username=username).first()
    if user is None:
        user = WeChatUser.query.filter_by(display_name=display_name).first()
    if user is None:
        user = WeChatUser(username=username, display_name=display_name)
        db.session.add(user)
    else:
        user.username = username
        user.display_name = display_name

    user.set_password(password)
    db.session.commit()
    print(f"[完成] {username} 已就绪（id={user.id}）")
    return user


def load_application():
    spec = importlib.util.spec_from_file_location(
        "top_app", os.path.join(PROJECT_ROOT, "app.py")
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载 app.py")
    top = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(top)
    return top.app


def main():
    application = load_application()
    with application.app_context():
        for account in ACCOUNTS:
            init_user(*account)
        print("\n两个中文聊天账号已完成初始化。")


if __name__ == "__main__":
    main()
