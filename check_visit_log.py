"""快速检查 visit_log 表内容 + 确认 DB 路径"""
import sys, os
sys.path.insert(0, '.')

from app import app, db, VisitLog

with app.app_context():
    # 打印实际 DB 路径
    print(f"DB URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"DB 文件: {db.engine.url.database}")

    # 列出 instance 目录下的 db 文件
    instance_dir = os.path.join(os.path.dirname(__file__), 'instance')
    if os.path.exists(instance_dir):
        print(f"instance/ 目录文件: {os.listdir(instance_dir)}")

    logs = VisitLog.query.order_by(VisitLog.visited_at.desc()).all()
    print(f"\nvisit_log 表共 {len(logs)} 条记录：")
    for log in logs:
        role = "管理员" if log.is_admin else "访客"
        print(f"  [{log.id}] {log.visited_at}  {role}  IP={log.ip_address}  UA={log.user_agent[:60]}")
