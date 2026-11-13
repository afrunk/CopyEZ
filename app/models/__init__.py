"""
Database models

This package contains all SQLAlchemy models for CopyEZ.

Usage:
    from app.models import Note, Memo, CustomCategory

Current status:
    - Phase 3: Models migrated from app.py
    - Phase 3: now_bj imported from app.utils.datetime_utils
"""

from app.models.note import Note
from app.models.memo import Memo
from app.models.category import CustomCategory

# BondageDiary (Phase 7)
from app.models.bondage_diary import (
    DiaryUser,
    DiaryEntry,
    DiaryImage,
    DiaryComment,
    DiaryEntryRevision,
    DiaryAccessLog,
    DiaryLoginAttempt,
)

# WeChat (私密聊天)
from app.models.wechat import WeChatUser, WeChatMessage

__all__ = [
    "Note",
    "Memo",
    "CustomCategory",
    "DiaryUser",
    "DiaryEntry",
    "DiaryImage",
    "DiaryComment",
    "DiaryEntryRevision",
    "DiaryAccessLog",
    "DiaryLoginAttempt",
    "WeChatUser",
    "WeChatMessage",
    "WeChatLoginHistory",
]
