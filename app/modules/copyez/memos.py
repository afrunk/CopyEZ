"""
Memos (随心记) module.

Simple streaming memory notes - minimal distractions from the long-form system.
"""

from flask import Blueprint, render_template

memos_bp = Blueprint("memos", __name__)


@memos_bp.route("/memos")
def memos_page():
    """随心记页面：极简短信流式记忆，不干扰长文体系"""
    return render_template("memos.html")
