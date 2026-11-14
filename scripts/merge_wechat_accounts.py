"""归并 WeChat 别名账号的历史消息（幂等）。

背景：数据库里同一个人被拆成了多行账号：
    id=1 笨笨、id=2 蛋蛋     ← 主账号，持有全部历史消息
    id=3 benben、id=4 dandan ← 别名账号，只有零星几条

消息按 sender_id / receiver_id 挂在具体账号行上，所以用别名账号登录时
只能看到挂在那个 id 上的那几条消息。

本脚本只做一件事：把别名账号的历史消息改挂到同组的主账号 id 上。
账号行本身保留（否则 dandan / benben 这类登录名会失效，手机就登不进去了）。

用法：
    python scripts/merge_wechat_accounts.py            # 只做检查，不改数据
    python scripts/merge_wechat_accounts.py --apply    # 真正执行归并
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.extensions import db
from app.models.wechat import WeChatUser, WeChatMessage
from app.modules.wechat.identity import person_label

APPLY = "--apply" in sys.argv


def load_application():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "top_app", os.path.join(PROJECT_ROOT, "app.py")
    )
    top = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(top)
    return top.app


def main():
    app = load_application()
    with app.app_context():
        users = WeChatUser.query.all()

        # 按「人」分组
        groups = {}
        for u in users:
            groups.setdefault(person_label(u), []).append(u)

        print("=" * 60)
        print("当前账号分组：")
        for label, members in groups.items():
            print(f"\n  [{label}]")
            for m in members:
                sent = WeChatMessage.query.filter(WeChatMessage.sender_id == m.id).count()
                recv = WeChatMessage.query.filter(WeChatMessage.receiver_id == m.id).count()
                print(f"    id={m.id}  username={m.username!r}  display_name={m.display_name!r}"
                      f"  发出={sent} 收到={recv}")

        # 主账号 = 同组里 id 最小的那个（历史消息都在它身上）
        canonical = {label: min(m.id for m in members) for label, members in groups.items()}

        print("\n" + "=" * 60)
        print("计划：")
        for label, members in groups.items():
            keep = canonical[label]
            for m in members:
                if m.id == keep:
                    continue
                sent = WeChatMessage.query.filter(WeChatMessage.sender_id == m.id).count()
                recv = WeChatMessage.query.filter(WeChatMessage.receiver_id == m.id).count()
                print(f"  别名 id={m.id} ({m.username}) 的消息（发出 {sent} / 收到 {recv}）"
                      f" → 改挂到 id={keep} ({label})")
        print("  账号行全部保留，dandan / benben 等登录名继续可用")
        print("=" * 60)

        if not APPLY:
            print("\n这是检查模式，未修改任何数据。")
            print("确认无误后执行：python scripts/merge_wechat_accounts.py --apply")
            return

        # ── 执行归并 ──────────────────────────────────────────────
        for label, members in groups.items():
            keep = canonical[label]
            for m in members:
                if m.id == keep:
                    continue
                WeChatMessage.query.filter(WeChatMessage.sender_id == m.id).update(
                    {WeChatMessage.sender_id: keep}, synchronize_session=False
                )
                WeChatMessage.query.filter(WeChatMessage.receiver_id == m.id).update(
                    {WeChatMessage.receiver_id: keep}, synchronize_session=False
                )
                db.session.commit()
                print(f"  [OK] id={m.id} 的消息已改挂到 id={keep}")

            # 别名账号的登录历史也归到主账号
            try:
                from app.models.wechat import WeChatLoginHistory
                for m in members:
                    if m.id == keep:
                        continue
                    WeChatLoginHistory.query.filter(
                        WeChatLoginHistory.user_id == m.id
                    ).update({WeChatLoginHistory.user_id: keep}, synchronize_session=False)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"  [WARN] 登录历史归并失败: {e}")

        print("\n归并完成。最终账号列表：")
        for u in WeChatUser.query.all():
            sent = WeChatMessage.query.filter(WeChatMessage.sender_id == u.id).count()
            recv = WeChatMessage.query.filter(WeChatMessage.receiver_id == u.id).count()
            print(f"  id={u.id}  username={u.username!r}  display_name={u.display_name!r}"
                  f"  发出={sent} 收到={recv}")
        print(f"\n消息总数：{WeChatMessage.query.count()}")


if __name__ == "__main__":
    main()
