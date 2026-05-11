"""
RenovaMate Blueprint - Flask Routes
装修助手模块
"""
from flask import Blueprint, render_template, send_from_directory
import os

bp = Blueprint(
    'renovamate',
    __name__,
    template_folder='../../templates',  # 指向项目根目录的 templates
    static_folder='static',
    url_prefix='/renovamate'
)

# Alias for app.py registration
renovamate_bp = bp


@bp.route('/')
def index():
    """RenovaMate 首页总览"""
    return render_template('renovamate/index.html')


@bp.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files from static/renovamate/css"""
    static_path = os.path.join(os.path.dirname(__file__), 'static', 'renovamate')
    return send_from_directory(os.path.join(static_path, 'css'), filename)


# 后续可扩展：
# @bp.route('/compare')
# def compare():
#     return render_template('renovamate/compare.html')


# 后续可扩展：
# @bp.route('/compare')
# def compare():
#     return render_template('renovamate/compare.html')

# @bp.route('/compare/<category>')
# def compare_detail(category):
#     return render_template('renovamate/compare_detail.html', category=category)

# @bp.route('/budget')
# def budget():
#     return render_template('renovamate/budget.html')

# @bp.route('/progress')
# def progress():
#     return render_template('renovamate/progress.html')

# @bp.route('/notes')
# def notes():
#     return render_template('renovamate/notes.html')
