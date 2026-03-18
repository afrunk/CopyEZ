"""上传服务器前将契约状态重置为「未确认」。运行: python reset_contract.py"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from app import AuditProfile

with app.app_context():
    profile = AuditProfile.query.first()
    if not profile:
        print("没有档案，无需重置。")
    else:
        profile.contract_json = None
        db.session.commit()
        print("契约已重置为未确认，可以上传服务器。")
