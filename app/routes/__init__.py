"""Flask Blueprints 统一导出"""
from app.modules.portal import portal_index, orc_documents_page
from app.modules.copyez import guide_page, search_page
from app.modules.ledger import ledger_bp

__all__ = [
    "portal_index",
    "guide_page",
    "orc_documents_page",
    "ledger_bp",
    "search_page",
]
