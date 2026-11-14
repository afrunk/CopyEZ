"""Gongwen 模块路由"""
from flask import render_template

from . import gongwen_bp


@gongwen_bp.route('/')
def index():
    """机关材料写作提示词工作台首页"""
    return render_template('gongwen/index.html')
