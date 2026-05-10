"""CopyEZ 模块 - 使用指南页面"""
from flask import render_template


def guide_page():
    """功能指南页面：展示所有功能点的交互式演示"""
    return render_template("guide.html")
