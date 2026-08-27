"""BondageDiary module - 调教日记"""
from app.modules.bondage_diary.auth import diary_auth_bp
from app.modules.bondage_diary.entries import diary_entries_bp
from app.modules.bondage_diary.comments import diary_comments_bp
from app.modules.bondage_diary.access_log import diary_access_bp
from app.modules.bondage_diary.upload import diary_upload_bp
from app.modules.bondage_diary.pages import diary_pages_bp
from app.modules.bondage_diary.dashboard import diary_dashboard_bp, diary_notifications_bp

__all__ = [
    "diary_auth_bp",
    "diary_entries_bp",
    "diary_comments_bp",
    "diary_access_bp",
    "diary_upload_bp",
    "diary_pages_bp",
    "diary_dashboard_bp",
    "diary_notifications_bp",
]
