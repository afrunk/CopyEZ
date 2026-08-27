"""
WeChat 初始化脚本

用法：
    python scripts/setup_wechat.py

功能：
    - 创建两个账号：笨笨 / 123456，蛋蛋 / 123456
    - 账号不存在才创建（幂等）
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.extensions import db
from app.models.wechat import WeChatUser


def init_user(username: str, display_name: str, password: str) -> WeChatUser | None:
    """初始化一个账号（幂等）"""
    user = WeChatUser.query.filter_by(username=username).first()
    if user:
        print(f"[跳过] {username} 已存在（id={user.id}）")
        return None

    user = WeChatUser(
        username=username,
        display_name=display_name,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print(f"[完成] {username} (display_name={display_name}) 创建成功，id={user.id}")
    return user


def main():
    try:
        from app import create_app
        application = create_app()
    except (ImportError, AttributeError):
        import importlib.util
        spec = importlib.util.spec_from_file_location("top_app", os.path.join(PROJECT_ROOT, "app.py"))
        top = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(top)
        application = top.app

    with application.app_context():
        users = []
        for u in [
            ("benben", "笨笨", "123456"),
            ("dandan", "蛋蛋", "123456"),
        ]:
            user = init_user(u[0], u[1], u[2])
            if user:
                users.append(user)

        if users:
            print(f"\n共创建 {len(users)} 个账号")
        else:
            print("\n所有账号已存在，无变更。")


if __name__ == "__main__":
    main()
