"""CopyEZ module - 公文素材库"""
from app.modules.copyez.guide import guide_page
from app.modules.copyez.search import search_page
from app.modules.copyez.note_pages import notes_page
from app.modules.copyez.memo import (
    api_memos,
    api_memo_pin,
    api_memo_star,
    api_memo_detail,
    memo_upload_image,
)
from app.modules.copyez.category import (
    get_categories,
    get_tags,
)
from app.modules.copyez.dashboard import (
    api_activity_stats,
    api_tag_collection,
)
from app.modules.copyez.formatting import api_format_markdown
from app.modules.copyez.upload_utils import upload_image
from app.modules.copyez.quote import collect_quote_items
from app.modules.copyez.memos import memos_bp
from app.modules.copyez.quotes import quotes_bp
from app.modules.copyez.scrape import scrape_bp
from app.modules.copyez.note_api import note_api_bp
from app.modules.copyez.note_queries import note_queries_bp
from app.modules.copyez.note_meta import note_meta_bp
from app.modules.copyez.note_relations import note_relations_bp
from app.modules.copyez.note_pages import note_pages_bp

__all__ = [
    "guide_page",
    "search_page",
    "api_memos",
    "api_memo_pin",
    "api_memo_star",
    "api_memo_detail",
    "memo_upload_image",
    "get_categories",
    "get_tags",
    "api_activity_stats",
    "api_tag_collection",
    "api_format_markdown",
    "upload_image",
    "collect_quote_items",
]
