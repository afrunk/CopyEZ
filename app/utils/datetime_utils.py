"""
DateTime utilities

Centralized datetime handling for Beijing Time (UTC+8).

Usage:
    from app.utils.datetime_utils import now_bj, BJ_TZ

Current status:
    - Phase 3: Migrated from app.py to avoid circular imports
"""

from datetime import datetime, timezone, timedelta


# 北京时区（UTC+8）
BJ_TZ = timezone(timedelta(hours=8))


def now_bj():
    """
    返回当前北京时间（naive datetime，不带时区信息）。

    用于 SQLAlchemy 模型的 default 参数，避免使用 utcnow 导致 ±8h 误差。

    返回 naive datetime 便于与 SQLite DATETIME 列直接比较与减法。
    """
    return datetime.now(BJ_TZ).replace(tzinfo=None)
