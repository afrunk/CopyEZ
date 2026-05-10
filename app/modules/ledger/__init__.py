"""LedgerEZ module - 个人记账本"""
from app.modules.ledger.routes import ledger_bp
from app.modules.ledger.api import ledger_api_bp

__all__ = ["ledger_bp", "ledger_api_bp"]
