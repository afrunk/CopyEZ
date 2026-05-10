"""CopyEZ 模块 - 搜索页面路由"""
from flask import request, render_template


def search_page():
    """全量搜索结果页：长文 + 随心记 双 Tab 展示"""
    q = request.args.get("q", "").strip()
    return render_template("search.html", q=q)
