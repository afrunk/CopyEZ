"""
WeChat 模块增量迁移脚本

用途：服务器已有数据库，追加 wechat_users / wechat_messages 两张表，
     并将账号（带原密码 hash）写入数据库。

使用场景：
    服务器部署时，从 GitHub 拉取新代码后运行一次即可。

用法：
    python scripts/migrate_wechat.py

功能：
    1. 只建表（表已存在则跳过）
    2. 幂等导入账号（账号已存在则跳过，保留原密码）
    3. 打印详细日志，便于 CI/CD 确认状态
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def main():
    try:
        from app import create_app
        application = create_app()
    except (ImportError, AttributeError):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "top_app", os.path.join(PROJECT_ROOT, "app.py")
        )
        top = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(top)
        application = top.app

    with application.app_context():
        from app.extensions import db
        from app.models.wechat import WeChatUser, WeChatMessage

        # ── 1. 建表（表存在则跳过）───────────────────────────────────────
        print("\n[1/3] 检查并创建表...")
        try:
            db.create_all()
            print("    ✅ 表结构就绪（已存在则跳过）")
        except Exception as e:
            print(f"    ⚠️  建表异常（可能已存在）: {e}")

        # ── 2. 定义要导入的账号 ─────────────────────────────────────────
        #    username  → 数据库里的登录名
        #    display   → 页面显示名
        #    password  → 当前服务器上已设定的密码明文
        #
        #    ⚠️  注意：请根据实际情况修改这里的密码。
        #        如果账号已在数据库里（已修改过密码），这个脚本不会覆盖它。
        ACCOUNTS = [
            {"username": "benben", "display": "笨笨",   "password": "123456"},
            {"username": "dandan", "display": "蛋蛋",   "password": "123456"},
        ]

        # ── 3. 幂等导入账号 ─────────────────────────────────────────────
        print("\n[2/3] 导入账号...")
        created = []
        skipped = []

        for acc in ACCOUNTS:
            existing = WeChatUser.query.filter_by(username=acc["username"]).first()
            if existing:
                skipped.append(acc["username"])
                print(f"    ⏭️  跳过（已存在）: {acc['username']} ({acc['display']})")
            else:
                user = WeChatUser(
                    username=acc["username"],
                    display_name=acc["display"],
                )
                user.set_password(acc["password"])
                db.session.add(user)
                db.session.commit()
                created.append(acc["username"])
                print(f"    ✅ 创建账号: {acc['username']} ({acc['display']})")

        # ── 4. 汇总 ──────────────────────────────────────────────────────
        print("\n[3/3] 完成汇总")
        print(f"    新建账号: {created if created else '无'}")
        print(f"    跳过账号: {skipped if skipped else '无'}")

        # 验证
        total = WeChatUser.query.count()
        print(f"\n    当前 WeChat 账号总数: {total}")
        for u in WeChatUser.query.all():
            print(f"      - {u.username} ({u.display_name})")


if __name__ == "__main__":
    main()
