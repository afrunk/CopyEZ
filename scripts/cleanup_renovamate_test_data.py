#!/usr/bin/env python3
"""
RenovaMate 测试数据清理脚本

用途：清理 RenovaMate 模块中的开发测试数据，不影响 CopyEZ 原功能

使用方法：
    python scripts/cleanup_renovamate_test_data.py        # 默认：只清理测试业务数据
    python scripts/cleanup_renovamate_test_data.py --all  # 全量清理（包括项目和分类）
    python scripts/cleanup_renovamate_test_data.py --dry  # 预览模式（不实际删除）
    python scripts/cleanup_renovamate_test_data.py --help # 显示帮助

默认清理范围（不包含 --all 参数时）：
    - renovamate_compare_items   (方案数据)
    - renovamate_expenses       (花费记录)
    - renovamate_progress_tasks  (装修任务)
    - renovamate_notes          (装修手册)

全量清理（包含 --all 参数时）：
    - decor_project_categories   (项目-分类关联，可选)
    - decoration_categories      (子分类)
    - decoration_category_groups (分类大类)
    - decoration_projects       (装修项目)
    + 默认清理的所有表

不会清理：
    - CopyEZ 相关表（notes, memos, categories 等）
    - 任何 CopyEZ 原功能数据
"""

import os
import sys
import argparse

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 默认清理的表（测试业务数据）
DEFAULT_TABLES = [
    'renovamate_compare_items',
    'renovamate_expenses',
    'renovamate_progress_tasks',
    'renovamate_notes',
]

# 全量清理的表（包括项目和分类）
ALL_TABLES = [
    'renovamate_compare_items',
    'renovamate_expenses',
    'renovamate_progress_tasks',
    'renovamate_notes',
    'decoration_categories',
    'decoration_category_groups',
    'decoration_projects',
]


def get_db_path():
    """获取数据库路径"""
    # 尝试多个可能的路径
    possible_paths = [
        os.path.join(os.path.dirname(__file__), '..', 'instance', 'copyez.db'),
        os.path.join(os.path.dirname(__file__), '..', 'copyez.db'),
        'instance/copyez.db',
        'copyez.db',
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return os.path.abspath(path)

    raise FileNotFoundError("找不到数据库文件 instance/copyez.db")


def get_tables_to_clean(all_mode=False):
    """获取需要清理的表列表"""
    if all_mode:
        return ALL_TABLES
    return DEFAULT_TABLES


def check_table_exists(cursor, table_name):
    """检查表是否存在"""
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None


def get_table_counts(cursor, tables):
    """获取各表的记录数量"""
    counts = {}
    for table in tables:
        if check_table_exists(cursor, table):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]
        else:
            counts[table] = 0
    return counts


def clean_tables(cursor, tables, dry_run=False):
    """清理指定表的数据"""
    for table in tables:
        if not check_table_exists(cursor, table):
            print(f"  - {table}: 表不存在，跳过")
            continue

        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]

        if count == 0:
            print(f"  - {table}: 无数据，跳过")
            continue

        if dry_run:
            print(f"  - {table}: 将删除 {count} 条记录 (预览模式)")
        else:
            cursor.execute(f"DELETE FROM {table}")
            print(f"  - {table}: 已删除 {count} 条记录")


def print_separator():
    """打印分隔线"""
    print("=" * 60)


def print_header(title):
    """打印标题"""
    print()
    print_separator()
    print(f"  {title}")
    print_separator()


def main():
    parser = argparse.ArgumentParser(
        description="清理 RenovaMate 模块的测试数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python scripts/cleanup_renovamate_test_data.py        # 默认清理测试业务数据
  python scripts/cleanup_renovamate_test_data.py --all  # 全量清理（包括项目和分类）
  python scripts/cleanup_renovamate_test_data.py --dry  # 预览模式

警告：
  - 此脚本会删除数据，操作不可恢复！
  - 默认不会删除项目和分类数据
  - 使用 --all 参数才会删除项目和分类
        """
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='全量清理模式（包括项目和分类数据）'
    )
    parser.add_argument(
        '--dry', '-d',
        action='store_true',
        help='预览模式：只显示将要删除的数量，不实际删除'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='跳过确认直接执行（危险！）'
    )

    args = parser.parse_args()

    # 获取数据库路径
    try:
        db_path = get_db_path()
    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)

    print_header("RenovaMate 测试数据清理工具")
    print(f"数据库路径: {db_path}")

    # 获取要清理的表
    tables = get_tables_to_clean(args.all)
    mode = "全量清理" if args.all else "默认清理"
    print(f"清理模式: {mode}")
    print()

    # 连接数据库
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查表是否存在并获取数量
    print_header("当前数据统计")
    counts = get_table_counts(cursor, tables)

    total = sum(counts.values())
    if total == 0:
        print("所有 RenovaMate 表都是空的，无需清理。")
        conn.close()
        sys.exit(0)

    for table, count in counts.items():
        if count > 0:
            print(f"  {table}: {count} 条记录")

    print()
    print(f"总计: {total} 条记录将被清理")

    if args.all:
        print()
        print("【警告】全量清理将删除以下数据：")
        print("  - 装修项目（DecorationProject）")
        print("  - 分类大类（DecorationCategoryGroup）")
        print("  - 子分类（DecorationCategory）")
        print("  - 以及所有测试业务数据")

    # 预览模式
    if args.dry:
        print()
        print_header("预览模式 - 将会执行的操作")
        clean_tables(cursor, tables, dry_run=True)
        conn.close()
        sys.exit(0)

    # 确认删除
    if args.yes:
        print()
        print("已跳过确认（--yes 参数）")
    else:
        print()
        print("请确认是否执行清理？")
        print("输入 'yes' 确认删除，或按 Ctrl+C 取消：")

        try:
            confirm = input("> ").strip().lower()
        except KeyboardInterrupt:
            print("\n\n已取消操作。")
            conn.close()
            sys.exit(0)

        if confirm != 'yes':
            print("\n已取消操作。")
            conn.close()
            sys.exit(0)

    # 执行清理
    print()
    print_header("正在清理数据...")
    clean_tables(cursor, tables, dry_run=False)

    # 提交更改
    conn.commit()

    # 显示清理后的数量
    print()
    print_header("清理后的数据统计")
    remaining_total = 0
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        remaining_total += count
        if count > 0:
            print(f"  {table}: {count} 条记录")
        else:
            print(f"  {table}: 0 条记录")

    print()
    print(f"总计剩余: {remaining_total} 条记录")

    conn.close()

    print()
    print_separator()
    print("清理完成！")
    print_separator()
    print()
    print("提示：")
    print("  - 如需清理 SQLite WAL 文件以减小数据库大小，可手动删除 .db-wal 和 .db-shm 文件")
    print("  - 或在 SQLite 中执行: PRAGMA wal_checkpoint(TRUNCATE);")


if __name__ == '__main__':
    main()
