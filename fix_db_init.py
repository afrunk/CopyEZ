"""修复数据库初始化问题"""
from app import app, db, Note, Memo, AuditProfile, CustomCategory, AuditLog, VisitLog, VisitAlias, AuditActionLog, ensure_schema

with app.app_context():
    # 先创建所有表
    print("正在创建所有数据库表...")
    db.create_all()
    print("db.create_all() 执行完成")
    
    # 执行迁移逻辑
    print("正在执行数据库迁移...")
    ensure_schema()
    print("数据库初始化完成！")
    
    # 验证
    from sqlalchemy import inspect
    insp = inspect(db.engine)
    table_names = insp.get_table_names()
    print(f"当前数据库表: {table_names}")
    
    # 检查 visit_log 表是否有记录
    count = VisitLog.query.count()
    print(f"VisitLog 表记录数: {count}")
