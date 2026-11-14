"""
Gongwen 模块 - 机关材料写作提示词工作台

URL 前缀: /gongwen
模板目录: templates/gongwen/index.html

说明:
本模块是一个"独立 App"，对外只提供固定网址（如 /gongwen），
页面本身是一个自包含的 HTML（CSS/JS 全部内联，无外部依赖），
参数保存在浏览器 localStorage，不写入数据库。
"""
from flask import Blueprint
import os

# 从 blueprint 文件向上到达项目根目录
# __file__ = app/modules/gongwen/__init__.py
_blueprint_dir = os.path.dirname(os.path.abspath(__file__))    # app/modules/gongwen
_modules_dir = os.path.dirname(_blueprint_dir)                  # app/modules
_app_dir = os.path.dirname(_modules_dir)                       # app
_project_root = os.path.dirname(_app_dir)                      # 项目根目录

gongwen_bp = Blueprint(
    'gongwen',
    __name__,
    template_folder=os.path.join(_project_root, 'templates'),
    url_prefix='/gongwen'
)

# 路由必须在底部导入，避免循环导入
from . import routes  # noqa: E402,F401

__all__ = ['gongwen_bp']
