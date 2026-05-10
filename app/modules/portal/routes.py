"""Portal 模块路由"""
from flask import render_template


def portal_index():
    """门户主页：展示 Logo 和入口卡片"""
    return render_template("portal.html")


def orc_documents_page():
    """ORC_documents 产品介绍页"""
    return render_template("landing.html")
