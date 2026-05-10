"""
Note model

Core material/article model for CopyEZ.

Usage:
    from app.models import Note
    note = Note.query.first()
"""

from app.extensions import db
from app.utils.datetime_utils import now_bj


class Note(db.Model):
    """
    核心素材模型

    用于存储长文素材，支持分类、标签、批注等功能。
    """

    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    tags = db.Column(db.String(255), nullable=True)  # 保留旧字段以兼容
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=now_bj)
    # 记录最近一次编辑时间，支持"二次加工 / 修改"场景
    updated_at = db.Column(db.DateTime, default=now_bj, onupdate=now_bj)
    # 存储划线的位置、颜色和批注内容（JSON 格式）
    annotations = db.Column(db.Text, nullable=True)
    # 存储右侧总体的深度思考笔记
    global_thought = db.Column(db.Text, nullable=True)
    # 一级分类：全文、框架、短文摘要（三选一）
    mainCategory = db.Column(db.String(50), nullable=True)
    # 二级分类：讲话精神、调研报告、会议精神、经验材料综述、讲话材料等
    subCategory = db.Column(db.String(100), nullable=True)
    # 三级标签：数组形式，JSON 存储，如 ['政法类型', '专项行动']
    tags_json = db.Column(db.Text, nullable=True)
    # 发布日期：YYYY-MM-DD 格式
    publishDate = db.Column(db.String(10), nullable=True)
    # 原文链接：URL 字符串
    sourceUrl = db.Column(db.String(500), nullable=True)

    def get_tags_list(self):
        """获取标签列表（从 tags_json 解析）"""
        import json
        if self.tags_json:
            try:
                return json.loads(self.tags_json)
            except:
                return []
        return []

    def set_tags_list(self, tags_list):
        """设置标签列表（保存为 JSON）"""
        import json
        if tags_list:
            self.tags_json = json.dumps(tags_list, ensure_ascii=False)
        else:
            self.tags_json = None
