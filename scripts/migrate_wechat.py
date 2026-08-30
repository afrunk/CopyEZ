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
import io

# 强制 UTF-8 输出，避免 Windows / GBK 终端打印 emoji 时挂掉
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

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

        # -- 1. 建表（表存在则跳过）---------------------------------------
        print("\n[1/3] 检查并创建表...")
        try:
            db.create_all()
            print("    [OK] 表结构就绪（已存在则跳过）")
        except Exception as e:
            print(f"    [WARN]  建表异常（可能已存在）: {e}")

        # 增量补列：表已存在但缺新字段时，用 ALTER TABLE 追加
        print("    检查并补列...")
        inspector = db.inspect(db.engine)
        existing_columns = {c["name"] for c in inspector.get_columns("wechat_users")}

        COLUMNS_TO_ADD = [
            ("display_name",   "TEXT NOT NULL DEFAULT ''"),
            ("password_hash",  "TEXT NOT NULL DEFAULT ''"),
            ("avatar_type",    "TEXT NOT NULL DEFAULT 'color'"),
            ("avatar_color",   "TEXT NOT NULL DEFAULT '#6366F1'"),
            ("avatar_emoji",   "TEXT"),
            ("avatar_url",     "TEXT"),
            ("created_at",     "TIMESTAMP"),
            ("last_seen",      "TIMESTAMP"),
        ]

        for col_name, col_def in COLUMNS_TO_ADD:
            if col_name not in existing_columns:
                try:
                    db.session.execute(
                        db.text(f"ALTER TABLE wechat_users ADD COLUMN {col_name} {col_def}")
                    )
                    db.session.commit()
                    print(f"    [OK] 新增列: {col_name}")
                except Exception as e:
                    db.session.rollback()
                    print(f"    [WARN]  新增列 {col_name} 失败（可能已存在）: {e}")

        # -- 1b. 补 wechat_messages 缺失的列 -----------------------------
        print("\n    检查 wechat_messages 补列...")
        existing_msg_cols = {c["name"] for c in inspector.get_columns("wechat_messages")}

        MSG_COLUMNS_TO_ADD = [
            ("content",       "TEXT NOT NULL DEFAULT ''"),
            ("msg_type",      "TEXT NOT NULL DEFAULT 'text'"),
            ("image_urls",    "TEXT"),
            ("recalled",      "INTEGER NOT NULL DEFAULT 0"),
            ("is_read",       "INTEGER NOT NULL DEFAULT 0"),
            ("created_at",    "TIMESTAMP"),
            # 关键：之前漏了 receiver_id，导致 chat 历史消息查询时所有消息都被过滤掉
            ("receiver_id",   "INTEGER"),
        ]

        for col_name, col_def in MSG_COLUMNS_TO_ADD:
            if col_name not in existing_msg_cols:
                try:
                    db.session.execute(
                        db.text(f"ALTER TABLE wechat_messages ADD COLUMN {col_name} {col_def}")
                    )
                    db.session.commit()
                    print(f"    [OK] 新增列: wechat_messages.{col_name}")
                except Exception as e:
                    db.session.rollback()
                    print(f"    [WARN]  新增列 wechat_messages.{col_name} 失败（可能已存在）: {e}")

        # -- 1b-2. 补 wechat_login_history 缺失的列 -------------------------
        #     服务器上早期版本的表只有 user_id / login_at 列，
        #     写入时缺少 logged_in_at 会直接 500，导致登录接口看起来"账号不存在"。
        print("\n    检查 wechat_login_history 补列...")
        try:
            existing_login_cols = {c["name"] for c in inspector.get_columns("wechat_login_history")}
        except Exception:
            # 表都不存在就让 create_all 处理
            existing_login_cols = set()

        LOGIN_HISTORY_COLUMNS_TO_ADD = [
            ("user_id",       "INTEGER"),
            ("logged_in_at",  "TIMESTAMP"),
            ("ip_address",    "TEXT"),
            ("user_agent",    "TEXT"),
        ]

        for col_name, col_def in LOGIN_HISTORY_COLUMNS_TO_ADD:
            if col_name not in existing_login_cols:
                try:
                    db.session.execute(
                        db.text(f"ALTER TABLE wechat_login_history ADD COLUMN {col_name} {col_def}")
                    )
                    db.session.commit()
                    print(f"    [OK] 新增列: wechat_login_history.{col_name}")
                except Exception as e:
                    db.session.rollback()
                    print(f"    [WARN]  新增列 wechat_login_history.{col_name} 失败（可能已存在）: {e}")

        # -- 1c. 数据回填（幂等）------------------------------------------
        print("\n    数据回填...")
        try:
            # msg_type <- message_type（仅在历史数据 msg_type 为空时）
            null_msg_type = db.session.execute(
                db.text("SELECT COUNT(*) FROM wechat_messages WHERE msg_type IS NULL OR msg_type = ''")
            ).scalar()
            if null_msg_type and null_msg_type > 0:
                db.session.execute(db.text("""
                    UPDATE wechat_messages
                    SET msg_type = CASE
                        WHEN message_type IN ('text','image') THEN message_type
                        ELSE 'text'
                    END
                    WHERE msg_type IS NULL OR msg_type = ''
                """))
                db.session.commit()
                print(f"    [OK] 回填 msg_type: {null_msg_type} 行")

            # is_read <- read_at NOT NULL
            null_is_read = db.session.execute(
                db.text("SELECT COUNT(*) FROM wechat_messages WHERE is_read = 0 AND read_at IS NOT NULL")
            ).scalar()
            if null_is_read and null_is_read > 0:
                db.session.execute(db.text("""
                    UPDATE wechat_messages SET is_read = 1
                    WHERE is_read = 0 AND read_at IS NOT NULL
                """))
                db.session.commit()
                print(f"    [OK] 回填 is_read: {null_is_read} 行")

            # recalled <- is_deleted=1 OR recalled_at NOT NULL
            null_recalled = db.session.execute(
                db.text("SELECT COUNT(*) FROM wechat_messages WHERE recalled = 0 AND (is_deleted = 1 OR recalled_at IS NOT NULL)")
            ).scalar()
            if null_recalled and null_recalled > 0:
                db.session.execute(db.text("""
                    UPDATE wechat_messages SET recalled = 1
                    WHERE recalled = 0 AND (is_deleted = 1 OR recalled_at IS NOT NULL)
                """))
                db.session.commit()
                print(f"    [OK] 回填 recalled: {null_recalled} 行")

            # receiver_id <- 推断：sender_id=1->2，sender_id=2->1
            null_receiver = db.session.execute(
                db.text("SELECT COUNT(*) FROM wechat_messages WHERE receiver_id IS NULL")
            ).scalar()
            if null_receiver and null_receiver > 0:
                db.session.execute(db.text("""
                    UPDATE wechat_messages
                    SET receiver_id = CASE sender_id
                        WHEN 1 THEN 2
                        WHEN 2 THEN 1
                        ELSE receiver_id
                    END
                    WHERE receiver_id IS NULL
                """))
                db.session.commit()
                print(f"    [OK] 回填 receiver_id: {null_receiver} 行")

            # image_urls <- content（旧实现把 url 存 content）
            null_image = db.session.execute(
                db.text("SELECT COUNT(*) FROM wechat_messages WHERE (msg_type = 'image' OR message_type = 'image' OR message_type IN ('burn_image','flash_image')) AND (image_urls IS NULL OR image_urls = '' OR image_urls = '[]') AND content IS NOT NULL AND content != ''")
            ).scalar()
            if null_image and null_image > 0:
                db.session.execute(db.text("""
                    UPDATE wechat_messages
                    SET image_urls = '["' || content || '"]'
                    WHERE (msg_type = 'image' OR message_type = 'image'
                           OR message_type IN ('burn_image','flash_image'))
                      AND (image_urls IS NULL OR image_urls = '' OR image_urls = '[]')
                      AND content IS NOT NULL AND content != ''
                """))
                db.session.commit()
                print(f"    [OK] 回填 image_urls: {null_image} 行")
        except Exception as e:
            db.session.rollback()
            print(f"    [WARN]  数据回填失败: {e}")

        # -- 1d. 旧列放宽 NOT NULL 约束（SQLite 重建表方案）-------------
        #     旧 message_type / is_deleted 列 NOT NULL 会让 SQLAlchemy 写新数据时报
        #     IntegrityError，因为模型里没有这些列。
        print("\n    检查旧列 NOT NULL 约束...")
        try:
            # PRAGMA table_info 的第 4 个字段：notnull (1=NOT NULL, 0=nullable)
            info_rows = db.session.execute(db.text("PRAGMA table_info(wechat_messages)")).fetchall()
            legacy_notnull = [row[1] for row in info_rows if row[1] in ("message_type", "is_deleted") and row[3] == 1]

            if legacy_notnull:
                print(f"    [WARN]  旧 NOT NULL 列: {legacy_notnull}，重建表...")
                db.session.execute(db.text("""
                    CREATE TABLE wechat_messages_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender_id INTEGER,
                        receiver_id INTEGER,
                        content TEXT,
                        message_type VARCHAR(20),
                        msg_type VARCHAR(20),
                        image_urls TEXT,
                        recalled INTEGER DEFAULT 0,
                        is_read INTEGER DEFAULT 0,
                        is_deleted INTEGER DEFAULT 0,
                        recalled_at DATETIME,
                        read_at TIMESTAMP,
                        created_at DATETIME
                    )
                """))
                # 按列存在性复制，缺失列填 NULL
                col_names_in_old = {row[1] for row in info_rows}
                select_parts = []
                for tc in ("sender_id", "receiver_id", "content", "message_type",
                          "msg_type", "image_urls", "recalled", "is_read",
                          "is_deleted", "recalled_at", "read_at", "created_at"):
                    if tc in col_names_in_old:
                        select_parts.append(f'"{tc}"')
                    else:
                        select_parts.append("NULL")
                db.session.execute(db.text(f"""
                    INSERT INTO wechat_messages_new
                        (sender_id, receiver_id, content, message_type,
                         msg_type, image_urls, recalled, is_read,
                         is_deleted, recalled_at, read_at, created_at)
                    SELECT {", ".join(select_parts)} FROM wechat_messages
                """))
                db.session.execute(db.text("DROP TABLE wechat_messages"))
                db.session.execute(db.text("ALTER TABLE wechat_messages_new RENAME TO wechat_messages"))
                db.session.commit()
                print("    [OK] 表重建完成")
            else:
                print("    [OK] 无需重建（约束已放宽或不存在）")
        except Exception as e:
            db.session.rollback()
            print(f"    [WARN]  重建表失败: {e}")

        # -- 2. 定义要导入的账号 -----------------------------------------
        #    username  -> 数据库里的登录名
        #    display   -> 页面显示名
        #    password  -> 当前服务器上已设定的密码明文
        #
        #    [WARN]  注意：请根据实际情况修改这里的密码。
        #        如果账号已在数据库里（已修改过密码），这个脚本不会覆盖它。
        ACCOUNTS = [
            {"username": "笨笨", "display": "笨笨", "password": "123456"},
            {"username": "蛋蛋", "display": "蛋蛋", "password": "123456"},
        ]

        # -- 3. 幂等导入账号 ---------------------------------------------
        print("\n[2/3] 导入账号...")
        created = []
        skipped = []

        for acc in ACCOUNTS:
            existing = WeChatUser.query.filter_by(username=acc["username"]).first()
            if existing:
                skipped.append(acc["username"])
                print(f"    [NEXT]  跳过（已存在）: {acc['username']} ({acc['display']})")
            else:
                user = WeChatUser(
                    username=acc["username"],
                    display_name=acc["display"],
                )
                user.set_password(acc["password"])
                db.session.add(user)
                db.session.commit()
                created.append(acc["username"])
                print(f"    [OK] 创建账号: {acc['username']} ({acc['display']})")

        # -- 4. 汇总 ------------------------------------------------------
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
