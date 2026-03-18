import sqlite3
import os

# 搜索所有可能的数据库位置
search_paths = [
    os.path.dirname(__file__),
    os.getcwd(),
    os.path.expanduser("~"),
    "C:\\",
]

db_path = None
db_dir = None

for root in search_paths:
    if os.path.exists(root):
        for dirpath, dirnames, filenames in os.walk(root):
            for f in filenames:
                if f.endswith('.db'):
                    full_path = os.path.join(dirpath, f)
                    print(f"找到数据库: {full_path}")
                    # 检查是否是目标数据库（通过检查表）
                    try:
                        conn = sqlite3.connect(full_path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = [row[0] for row in cursor.fetchall()]
                        if 'audit_profile' in tables:
                            print(f"  -> 这是目标数据库！包含 audit_profile 表")
                            db_path = full_path
                            db_dir = dirpath
                            conn.close()
                            break
                        conn.close()
                    except:
                        pass
            if db_path:
                break
    if db_path:
        break

if not db_path:
    print("未找到包含 audit_profile 表的数据库文件")
    print(f"\n当前工作目录: {os.getcwd()}")
    print(f"脚本目录: {os.path.dirname(__file__)}")
    exit(1)

print(f"\n使用数据库路径: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 获取当前表结构
cursor.execute("PRAGMA table_info(audit_profile)")
columns = [row[1] for row in cursor.fetchall()]
print(f"当前列: {columns}")

# 检查并添加 tags 列
if 'tags' not in columns:
    cursor.execute("ALTER TABLE audit_profile ADD COLUMN tags TEXT DEFAULT '[]'")
    conn.commit()
    print("添加 tags 列成功")
else:
    print("tags 列已存在")

# 检查并添加 ledger_master 列
if 'ledger_master' not in columns:
    cursor.execute("ALTER TABLE audit_profile ADD COLUMN ledger_master TEXT")
    conn.commit()
    print("添加 ledger_master 列成功")
else:
    print("ledger_master 列已存在")

# 检查并添加 ledger_slave 列
if 'ledger_slave' not in columns:
    cursor.execute("ALTER TABLE audit_profile ADD COLUMN ledger_slave TEXT")
    conn.commit()
    print("添加 ledger_slave 列成功")
else:
    print("ledger_slave 列已存在")

# 验证最终表结构
cursor.execute("PRAGMA table_info(audit_profile)")
columns = [row[1] for row in cursor.fetchall()]
print(f"最终列: {columns}")

print("\n成功！数据库已修复。")

conn.close()