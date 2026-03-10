from datetime import datetime, timedelta, date
import os
import re
import traceback
import random

from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text, distinct, func
from markupsafe import Markup
import json
import markdown
import bleach
from werkzeug.utils import secure_filename
from uuid import uuid4
from werkzeug.exceptions import HTTPException
from urllib.parse import quote
from utils.scraper.manager import scrape_manager
try:
    # 可选依赖：用于图片等比例压缩，降低随心记图片占用
    from PIL import Image
except ImportError:
    Image = None
try:
    # 可选依赖：用于“摘抄语录本”导出为 Word
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
    from docx.oxml.ns import qn
    from docx.shared import Pt
except ImportError:
    Document = None
    WD_ALIGN_PARAGRAPH = None
    WD_LINE_SPACING = None
    qn = None
    Pt = None

app = Flask(__name__)

# 使用本地 sqlite 数据库存储素材（项目根目录）
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///copyez.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("COPYEZ_SECRET_KEY", "copyez-secret-key")
# 持久会话：默认 30 天免登录（用于后续极简登录体系）
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

# 禁用模板缓存，确保每次请求都重新渲染模板（开发环境）
app.config["TEMPLATES_AUTO_RELOAD"] = True

# 性能优化配置（针对 2核2G 阿里云服务器）
# 禁用 JSON 排序，减少 CPU 开销
app.config["JSON_SORT_KEYS"] = False
# 设置 JSON 响应不自动格式化，减少内存占用
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
# SQLAlchemy 连接池配置：限制连接数，避免内存占用过高
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_size": 5,  # 连接池大小
    "max_overflow": 10,  # 最大溢出连接数
    "pool_pre_ping": True,  # 连接前检查连接有效性
    "pool_recycle": 3600,  # 连接回收时间（秒）
}

db = SQLAlchemy(app)


@app.template_filter('urlquote')
def urlquote_filter(s):
    """URL编码字符串的过滤器，用于模板中编码URL参数"""
    if s is None:
        return ''
    return quote(str(s), safe='')


@app.errorhandler(Exception)
def handle_unexpected_error(e):
    """开发环境：捕获所有未处理异常，在页面上直接输出 traceback 方便排查。"""
    # 重要：不要把 404/400 等 HTTP 异常强行变成 500
    # 否则像 favicon.ico、缺失静态资源都会被显示为 500，误导排查
    if isinstance(e, HTTPException):
        return e
    # 构造简单的纯文本调试页面（仅在本机使用，部署前请删除/注释）
    tb = traceback.format_exc()
    debug_html = f"""
    <html>
      <head><title>Server Error</title></head>
      <body>
        <h1>Unhandled Exception</h1>
        <pre>{tb}</pre>
      </body>
    </html>
    """
    return debug_html, 500


def ensure_schema():
    """
    简单的"自修复"逻辑：
    - 发现本地 sqlite 里还没有 notes.updated_at，就自动补一个列，避免手动删库。
    - 发现没有 notes.annotations 和 notes.global_thought，也自动补上。
    - 发现没有 notes.mainCategory, notes.subCategory, notes.tags_json，也自动补上。
    """
    engine = db.engine
    insp = inspect(engine)

    table_names = insp.get_table_names()

    # 如果 notes 表还不存在，交给 create_all 去创建即可
    if "notes" not in table_names:
        return

    cols = [c["name"] for c in insp.get_columns("notes")]
    
    # 迁移 updated_at 字段
    if "updated_at" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE notes ADD COLUMN updated_at DATETIME"))
    
    # 迁移 annotations 字段（用于存储划线批注的 JSON）
    if "annotations" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE notes ADD COLUMN annotations TEXT"))
    
    # 迁移 global_thought 字段（用于存储深度思考笔记）
    if "global_thought" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE notes ADD COLUMN global_thought TEXT"))
    
    # 迁移 mainCategory 字段（一级分类：全文、框架、短文摘要）
    if "mainCategory" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE notes ADD COLUMN mainCategory VARCHAR(50)"))
    
    # 迁移 subCategory 字段（二级分类：讲话精神、调研报告等）
    if "subCategory" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE notes ADD COLUMN subCategory VARCHAR(100)"))
    
    # 迁移 tags_json 字段（三级标签：数组形式，JSON 存储）
    if "tags_json" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE notes ADD COLUMN tags_json TEXT"))
            # 将现有的 tags 字段（逗号分隔字符串）迁移到 tags_json（JSON 数组）
            # 注意：这里只迁移结构，不迁移数据，因为旧数据格式不同
    
    # 迁移 publishDate 字段（发布日期：YYYY-MM-DD 格式）
    if "publishDate" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE notes ADD COLUMN publishDate VARCHAR(10)"))
    
    # 迁移 sourceUrl 字段（原文链接：URL 字符串）
    if "sourceUrl" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE notes ADD COLUMN sourceUrl VARCHAR(500)"))
    
    # 创建 custom_categories 表（如果不存在）
    if "custom_categories" not in insp.get_table_names():
        db.create_all()
        # 初始化预置分类
        _init_preset_categories()
    else:
        # 如果表已存在，检查是否需要初始化预置分类
        if CustomCategory.query.count() == 0:
            _init_preset_categories()

    # === Memo 表的自修复迁移（置顶/星标） ===
    # 兼容老库：为 memos 表补充 is_pinned / is_starred / pinned_at / starred_at 字段
    if "memos" in table_names:
        memo_cols = [c["name"] for c in insp.get_columns("memos")]

        if "is_pinned" not in memo_cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE memos ADD COLUMN is_pinned BOOLEAN DEFAULT 0"))

        if "is_starred" not in memo_cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE memos ADD COLUMN is_starred BOOLEAN DEFAULT 0"))

        if "pinned_at" not in memo_cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE memos ADD COLUMN pinned_at DATETIME"))

        if "starred_at" not in memo_cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE memos ADD COLUMN starred_at DATETIME"))


def _init_preset_categories():
    """初始化预置的二级分类到数据库"""
    for main_cat, sub_cats in PRESET_CATEGORIES.items():
        for sub_cat in sub_cats:
            # 检查是否已存在
            existing = CustomCategory.query.filter_by(name=sub_cat).first()
            if not existing:
                category = CustomCategory(name=sub_cat, main_category=main_cat)
                db.session.add(category)
    db.session.commit()


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    tags = db.Column(db.String(255), nullable=True)  # 保留旧字段以兼容
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 记录最近一次编辑时间，支持"二次加工 / 修改"场景
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
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
        if self.tags_json:
            try:
                return json.loads(self.tags_json)
            except:
                return []
        return []
    
    def set_tags_list(self, tags_list):
        """设置标签列表（保存为 JSON）"""
        if tags_list:
            self.tags_json = json.dumps(tags_list, ensure_ascii=False)
        else:
            self.tags_json = None


class Memo(db.Model):
    """碎片化随心记（与长文 Note 分表存储，互不影响）"""
    __tablename__ = "memos"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    # 由 #标签 自动提取后存入，多个标签用逗号分隔（展示时再拆分）
    tags = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    # 置顶/星标（用于重要 memo 快速归档）
    is_pinned = db.Column(db.Boolean, default=False, nullable=False)
    is_starred = db.Column(db.Boolean, default=False, nullable=False)
    pinned_at = db.Column(db.DateTime, nullable=True)
    starred_at = db.Column(db.DateTime, nullable=True)

    def extract_tags(self):
        """从 content 中提取 #标签 列表"""
        if not self.content:
            return []
        matches = re.findall(r"#(\S+)", self.content)
        # 去重并保持原有顺序
        seen = set()
        ordered = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                ordered.append(m)
        return ordered

    def to_dict(self):
        tags_list = []
        if self.tags:
            tags_list = [t for t in (s.strip() for s in self.tags.split(",")) if t]
        return {
            "id": self.id,
            "content": self.content,
            "tags": tags_list,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_pinned": bool(self.is_pinned),
            "is_starred": bool(self.is_starred),
            "pinned_at": self.pinned_at.isoformat() if self.pinned_at else None,
            "starred_at": self.starred_at.isoformat() if self.starred_at else None,
        }


class CustomCategory(db.Model):
    """用户自定义的二级分类"""
    __tablename__ = "custom_categories"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    main_category = db.Column(db.String(50), nullable=True)  # 关联的一级分类（可选）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "main_category": self.main_category
        }


def estimate_text_length(markdown_text: str) -> int:
    """
    粗略估算正文字数，用于阅读页右侧“当前篇目：XXXX 字”的统计展示。
    - 不改动渲染逻辑，只在后端做一个轻量级统计。
    """
    if not markdown_text:
        return 0

    text = markdown_text

    # 1) 去掉 fenced code block（```...```）
    text = re.sub(r"```[\s\S]*?```", "", text)

    # 2) 去掉行内代码（`...`）
    text = re.sub(r"`[^`]*`", "", text)

    # 3) 去掉图片（![alt](url)）
    text = re.sub(r"!\[[^\]]*]\([^)]*\)", "", text)

    # 4) 处理链接（[text](url)）：保留可见文本
    text = re.sub(r"\[([^\]]*?)\]\([^)]*\)", r"\1", text)

    # 5) 去掉 HTML 标签（有些内容可能混入 HTML）
    text = re.sub(r"<[^>]+>", "", text)

    # 6) 去掉常见 Markdown 标记符号
    text = re.sub(r"[>#*_~\-]+", " ", text)

    # 7) 去掉所有空白，只统计实际字符数（适配中文场景）
    text = re.sub(r"\s+", "", text).strip()
    return len(text)


def collect_quote_items():
    """
    遍历所有带批注的文章，提取「高亮原文 + 批注」列表，
    并按“文章”维度聚合，供“摘抄语录本”和导出复用。

    返回结构（按文章创建时间倒序排列）：
    [
        {
            "note_id": 1,
            "note_title": "XXX",
            "items": [
                {"text": "<span class='hl-red'>...</span>", "comment": "..."},
                ...
            ]
        },
        ...
    ]
    """
    grouped_by_note = {}
    notes = (
        Note.query
        .filter(Note.annotations.isnot(None), Note.annotations != "")
        .order_by(Note.created_at.desc())
        .all()
    )

    def _sanitize_quote_html(html: str) -> str:
        """
        语录本展示：允许极少量 HTML（主要是 <span class="hl-..."> 高亮），其余全部剥离。
        """
        if not html:
            return ""
        cleaned = bleach.clean(
            html,
            tags=["span", "br", "strong", "em", "b", "i", "u", "s"],
            attributes={"span": ["class"]},
            strip=True,
        )
        # 仅保留允许的高亮 class，避免注入其它 class 干扰页面
        allowed = {"hl-red", "hl-blue", "hl-bold"}

        def _filter_class_attr(match):
            cls_raw = match.group(1) or ""
            kept = [c for c in cls_raw.split() if c in allowed]
            if not kept:
                return ""
            return f'class="{" ".join(kept)}"'

        cleaned = re.sub(r'class="([^"]*)"', _filter_class_attr, cleaned)
        cleaned = re.sub(r"\s+>", ">", cleaned)  # 清理被移除 class 后的多余空格
        return cleaned

    for note in notes:
        try:
            items = json.loads(note.annotations)
        except Exception:
            continue
        if not isinstance(items, list):
            continue

        for item in items:
            text_val = (item.get("text") or "").strip()
            comment_val = (item.get("comment") or "").strip()
            if not text_val:
                continue

            # 仅保留“长度 >= 50 字”的语录，过短的不进入摘抄语录本
            # - 这里按“可见字符数”计算：先去掉 HTML 标签和所有空白
            visible_text = re.sub(r"<[^>]+>", "", text_val)  # 去掉 <span> 等标签
            visible_text = re.sub(r"\s+", "", visible_text)  # 去掉空白字符
            if len(visible_text) < 50:
                continue
            safe_text_html = _sanitize_quote_html(text_val)
            note_group = grouped_by_note.setdefault(
                note.id,
                {
                    "note_id": note.id,
                    "note_title": note.title,
                    "items": [],
                },
            )
            note_group["items"].append(
                {
                    "text": safe_text_html,
                    "comment": comment_val,
                    "note_id": note.id,
                    "note_title": note.title,
                }
            )

    # 转换为列表，并按文章创建时间倒序排列，方便浏览最新素材
    note_id_to_created_at = {n.id: n.created_at for n in notes}
    groups = list(grouped_by_note.values())
    groups.sort(
        key=lambda g: (
            note_id_to_created_at.get(g["note_id"]) or datetime.min,
            g["note_id"],
        ),
        reverse=True,
    )
    return groups


# 预置的公文分类知识库
PRESET_CATEGORIES = {
    "全文": [
        "大、中型会议讲话",
        "座谈会发言",
        "开班动员",
        "总结讲话",
        "调研报告",
        "年度工作总结",
        "述职报告",
        "专题请示",
        "实施方案",
        "暂行办法",
        "指导意见",
        "行动计划",
        "典型经验材料",
        "先进事迹",
        "工作综述",
        "信息快报",
        "批复",
        "通报",
        "通知",
        "函询"
    ],
    "框架": [
        "讲话框架",
        "报告框架",
        "方案框架",
        "总结框架"
    ],
    "短文摘要": [
        "要点摘要",
        "核心观点",
        "金句摘录"
    ]
}

# 预置的三级标签（业务/领域）
PRESET_TAGS = [
    # 政法业务
    "平安建设",
    "法治建设",
    "社会治理",
    "扫黑除恶",
    "维稳工作",
    # 组织人事
    "队伍建设",
    "廉政教育",
    "教育整顿",
    "基层党建",
    # 专项行动
    "大练兵",
    "大排查",
    "利剑行动",
    "清网行动",
    # 其他常用标签
    "党建",
    "政法类型",
    "专项行动",
    "安全生产",
    "环境保护",
    "乡村振兴",
    "经济发展"
]


# HTML 安全白名单：允许图片与基础排版标签（不破坏公文版式）
ALLOWED_HTML_TAGS = [
    # 文本与段落
    "p", "br", "span", "div", "strong", "em", "b", "i", "u", "s",
    # 标题
    "h1", "h2", "h3", "h4", "h5", "h6",
    # 列表
    "ul", "ol", "li",
    # 代码块与引用
    "pre", "code", "blockquote",
    # 表格
    "table", "thead", "tbody", "tr", "th", "td",
    # 链接与图片
    "a", "img",
    # 其它常见结构
    "hr"
]

ALLOWED_HTML_ATTRIBUTES = {
    # 全局允许的基础属性（不包含 style，避免破坏统一排版）
    "*": ["id", "class"],
    "a": ["href", "title", "target", "rel", "class"],
    # 图片必须显式允许 src / alt / class / data-src，否则会被 bleach 清洗掉
    "img": ["src", "alt", "title", "class", "data-src"],
}


def clean_word_formatting(text: str) -> str:
    """
    清理从 Word 粘贴过来的格式问题：
    - 移除段首多余空格和特殊空白符（如 &nbsp;）
    - 统一处理全角/半角空格
    """
    # 移除段首的连续空格（包括全角空格）
    text = re.sub(r'^[\s\u3000\u00A0]+', '', text)
    # 移除 HTML 实体空格
    text = text.replace('&nbsp;', ' ')
    text = text.replace('\u00A0', ' ')  # 不间断空格
    text = text.replace('\u3000', ' ')  # 全角空格
    # 清理多余的连续空格
    text = re.sub(r' +', ' ', text)
    return text.strip()


def deep_clean_content(content: str) -> str:
    """
    深度清洗函数：对从 Word 粘贴的长文本执行强力格式清洗
    - 逐行扫描：将内容按行分割
    - 正则清洗：对每一行执行 re.sub(r'^[ \t\u00A0\u3000]+', '', line)
      - [ \t] 匹配普通空格和制表符
      - \u00A0 匹配 Word 常见的 &nbsp;（不间断空格）
      - \u3000 匹配中文全角空格
    - 规范化换行：合并连续的多个空行为一个
    - 预期结果：数据库中存储的每一段开头都必须是"绝对顶格"的汉字，没有任何空白
    """
    if not content:
        return content
    
    # 统一换行符为 \n
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    
    # 逐行扫描并清洗：去除每一行行首的所有空格、制表符、不间断空格、全角空格
    # 使用 re.MULTILINE 标志，确保 ^ 匹配每一行的开头
    content = re.sub(r'^[ \t\u00A0\u3000]+', '', content, flags=re.MULTILINE)
    
    # 规范化换行：将连续的多个空行（2个及以上）合并为一个空行
    content = re.sub(r'\n\n+', '\n\n', content)
    
    # 去除首尾的空白字符（但保留内部的换行结构）
    content = content.strip()
    
    return content


def auto_structure_speech_markdown(content: str) -> str:
    """
    针对“政法系统讲话稿 / 经验交流稿”这类 Word 粘贴文本的轻量级结构化工具。
    
    设计目标：
    - 识别「一、二、三、」这类总分结构，自动升级为 Markdown 标题（# 一级标题）
    - 识别「第一阶段……。」「一是突出党性。」「二是自我超越。」等句式，
      自动为首句加粗，生成 **第一阶段……。** 的效果
    - 完全兼容已有内容：如果用户已经手写了 # / ## 标题，则不做任何结构化改写
    
    触发条件（防误伤）：
    - 原文中不存在任何以 # 开头的 Markdown 标题
    - 且至少出现 2 条“总分结构”行（如「一、」「二、」「三、」），
      或至少出现 2 条「一是」「二是」这类小条目句式，才启用自动结构化
    """
    if not content:
        return content

    # 统一换行
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    lines = content.splitlines()

    # 如果用户已经手写 Markdown 标题，则不做任何处理，完全尊重原文
    if any(re.match(r"^\s*#+\s+", line) for line in lines):
        return content

    # 统计是否满足“讲话稿结构”特征，避免普通材料被误改
    top_heading_pattern = re.compile(r"^\s*[一二三四五六七八九十]{1,3}、")
    # 子层级标题模式：例如「（一）主要做法」「（二）下步打算」
    sub_heading_pattern = re.compile(r"^\s*（[一二三四五六七八九十]{1,3}）")
    bullet_sentence_pattern = re.compile(r"^\s*[一二三四五六七八九十][是要]")

    top_heading_count = sum(1 for line in lines if top_heading_pattern.match(line or ""))
    bullet_sentence_count = sum(1 for line in lines if bullet_sentence_pattern.match(line or ""))

    if top_heading_count < 2 and bullet_sentence_count < 2:
        # 特征不明显，当成普通文章，不启用自动结构化
        return content

    processed_lines = []

    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()

        # 空行原样保留（交给 deep_clean_content 做后续规范化）
        if not stripped:
            processed_lines.append(line)
            continue

        # 1）总分结构：「一、心路历程：……」「二、成长感悟：……」
        if top_heading_pattern.match(stripped):
            # 直接作为一级标题输出（后续渲染时再按公文样式展示）
            processed_lines.append("# " + stripped)
            continue

        # 1.1）子层级结构：「（一）主要做法」「（二）下步打算」
        if sub_heading_pattern.match(stripped):
            # 作为二级标题输出
            processed_lines.append("## " + stripped)
            continue

        # 2）阶段型小标题：「第一阶段，在……阶段。后文……」
        #    只将首句（以全角句号“。”结尾）加粗，后面的正文保持普通段落
        m_phase = re.match(r"^(第[一二三四五六七八九十]{1,3}阶段[^。]*。)(.*)$", stripped)
        if m_phase:
            head = m_phase.group(1).strip()
            tail = m_phase.group(2).lstrip()
            if tail:
                processed_lines.append(f"**{head}**{tail}")
            else:
                processed_lines.append(f"**{head}**")
            continue

        # 3）条目型句式：「一是突出党性。……」「二是自我超越。……」
        #    同样仅加粗首句，保持后文原样
        m_bullet = re.match(r"^([一二三四五六七八九十][是要][^。]*。)(.*)$", stripped)
        if m_bullet:
            head = m_bullet.group(1).strip()
            tail = m_bullet.group(2).lstrip()
            if tail:
                processed_lines.append(f"**{head}**{tail}")
            else:
                processed_lines.append(f"**{head}**")
            continue

        # 其它行保持不变
        processed_lines.append(line)

    return "\n".join(processed_lines)


def render_content(raw_content: str, return_toc: bool = False):
    """
    内容解析器（彻底修复版）：彻底修复长文档多个自然段被合并为一个 <p> 标签的问题
    
    核心策略：
    1. 行首去污：只删除行首空白字符，保留空行本身
    2. 强制段落分隔：确保每个非空行都被空行包围，强制 Markdown 识别为独立段落
    3. Markdown 渲染后，在 HTML 层面再次强制拆分段落（双重保险）
    
    参数:
        raw_content: 原始 Markdown 内容
        return_toc: 如果为 True，返回 (html, toc_html) 元组；否则只返回 html
    
    返回:
        如果 return_toc=False: Markup(html)
        如果 return_toc=True: (Markup(html), toc_html)
    """
    if not raw_content:
        if return_toc:
            return Markup(''), ''
        return Markup('')
    
    # 统一换行符为 \n
    raw_content = raw_content.replace("\r\n", "\n").replace("\r", "\n")
    
    # 第一步：行首去污
    # 使用 lstrip 只删除行首的空白字符，保留空行本身
    lines = [line.lstrip(' \t\u00A0\u3000') for line in raw_content.splitlines()]
    
    # 第二步：强制段落识别
    # 核心策略：确保每个非空行都被识别为独立段落
    # 规则：每个非空行后面都必须有一个空行（除非下一行已经是空行）
    # 这样，无论原始内容中两个段落之间是否有空行，最终都会变成独立段落
    processed_lines = []
    for i, line in enumerate(lines):
        # 如果当前行非空
        if line.strip():
            processed_lines.append(line)
            # 如果不是最后一行
            if i < len(lines) - 1:
                next_line = lines[i + 1]
                # 如果下一行也非空，必须在当前行后面加一个空行
                # 如果下一行是空行，就不加（保持原有的空行）
                if next_line.strip():
                    processed_lines.append('')
            # 如果是最后一行且非空，后面不需要加空行
        else:
            # 如果当前行是空行，保持原样（不做任何处理）
            processed_lines.append(line)
    
    cleaned_content = '\n'.join(processed_lines)
    
    # 标题标准修正 - 确保 # 后面必须有空格
    cleaned_content = re.sub(r'^(#+)([^#\s])', r'\1 \2', cleaned_content, flags=re.MULTILINE)
    
    # 规范化换行 - 将连续的多个空行合并为一个空行（最多保留一个空行）
    # 注意：这个操作必须在添加空行之后进行，确保每个段落之间只有一个空行
    cleaned_content = re.sub(r'\n\n+', '\n\n', cleaned_content)
    
    # 去除首尾空白字符
    cleaned_content = cleaned_content.strip()
    
    # 第三步：配置 Markdown 解析器，强制生成唯一的英文 ID
    # 使用计数器生成 section-1, section-2, section-3... 格式的 ID
    section_counter = [0]  # 使用列表以便在闭包中修改
    
    def english_slugify(text, separator='-'):
        """
        生成英文 ID：section-1, section-2, section-3...
        注意：Python-Markdown 的 slugify 函数只接受一个参数（text），
        但我们可以使用闭包来维护计数器，实现用户要求的 'section-' + str(y) 格式
        """
        section_counter[0] += 1
        return f'section-{section_counter[0]}'
    
    # 配置 markdown 扩展：toc 扩展会自动为标题生成 ID
    # 注意：我们通过在每个非空行后添加空行来让 Markdown 识别为独立段落
    # 不使用 nl2br，因为我们已经通过添加空行来确保段落分隔
    md = markdown.Markdown(
        extensions=['toc', 'fenced_code', 'tables'],
        extension_configs={
            'toc': {
                'baselevel': 1,
                'slugify': english_slugify  # 强制使用英文 ID（通过闭包实现计数器）
            }
        }
    )
    
    # 转换为 HTML
    html = md.convert(cleaned_content)
    
    # 核心：从解析器对象中显式提取生成的 TOC
    toc_html = md.toc if hasattr(md, 'toc') and md.toc else ''

    # 第四步：在 HTML 层面强制拆分段落（双重保险）
    # 策略1：把 <p> 里的 <br> 强制拆成多个段落
    import re as re_module

    def split_paragraphs_by_br(html_content: str) -> str:
        pattern = re_module.compile(r'<p([^>]*)>(.*?)</p>', re_module.DOTALL)

        def _replace(match):
            attrs = match.group(1)
            inner = match.group(2)

            # 根据 <br> / <br /> / <br/> 分割
            parts = re_module.split(r'<br\s*/?>\s*', inner)
            parts = [p for p in parts if p.strip()]

            # 如果没有 <br>，保持原状
            if len(parts) <= 1:
                return match.group(0)

            # 否则每一段独立成 <p>
            return ''.join(f'<p{attrs}>{p}</p>' for p in parts)

        return pattern.sub(_replace, html_content)

    html = split_paragraphs_by_br(html)
    
    # 策略2：基于原始内容的行信息，强制拆分被合并的段落
    # 如果 Markdown 把多个段落合并成了一个 <p>，我们需要基于原始行信息拆分
    # 方法：保存原始非空行的列表（排除标题），然后在 HTML 中查找对应的长段落，强制拆分
    original_paragraph_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
    
    def force_split_merged_paragraphs(html_content: str, original_lines: list) -> str:
        """
        如果 <p> 标签内容包含了多个原始行，强制拆分成多个 <p> 标签
        这是最后的保险措施，确保每个原始行都成为独立的段落
        """
        if len(original_lines) <= 1:
            # 如果原始内容只有一个段落，不需要拆分
            return html_content
        
        # 匹配所有 <p> 标签
        pattern = re_module.compile(r'<p([^>]*)>(.*?)</p>', re_module.DOTALL)
        
        def _replace(match):
            attrs = match.group(1)
            inner = match.group(2)
            
            # 移除 HTML 标签，获取纯文本内容（用于匹配）
            text_content = re_module.sub(r'<[^>]+>', '', inner).strip()
            
            # 检查这个段落是否包含了多个原始行的文本
            # 方法：检查原始行列表中，有多少行的文本出现在这个段落中
            matching_lines = []
            for orig_line in original_lines:
                orig_text = orig_line.strip()
                # 如果原始行的文本出现在段落中（作为子字符串，且长度足够）
                # 使用更严格的匹配：原始行文本必须完整出现在段落中，且长度至少15个字符
                if orig_text and len(orig_text) >= 15 and orig_text in text_content:
                    matching_lines.append(orig_text)
            
            # 如果匹配到多个原始行（2个或更多），尝试拆分
            if len(matching_lines) >= 2:
                # 按照原始行的顺序，在 HTML 中找到每个原始行的位置，然后拆分
                # 方法：找到每个原始行文本在 HTML 中的位置，然后在那里插入 </p><p> 标签
                parts = []
                remaining_html = inner
                remaining_text = text_content
                
                # 按照原始行的顺序，依次查找每个原始行的位置并拆分
                for i, orig_text in enumerate(matching_lines):
                    if i == len(matching_lines) - 1:
                        # 最后一个，直接添加剩余部分
                        parts.append(remaining_html)
                        break
                    
                    # 在剩余文本中查找当前原始行的位置
                    pos_in_text = remaining_text.find(orig_text)
                    if pos_in_text == -1:
                        # 如果找不到，跳过这个原始行
                        continue
                    
                    # 找到文本位置后，需要找到对应的 HTML 位置
                    # 方法：计算文本位置对应的 HTML 位置（考虑 HTML 标签）
                    html_pos = 0
                    text_pos = 0
                    for char in remaining_html:
                        if text_pos >= pos_in_text + len(orig_text):
                            break
                        if char == '<':
                            # 跳过 HTML 标签
                            while html_pos < len(remaining_html) and remaining_html[html_pos] != '>':
                                html_pos += 1
                            if html_pos < len(remaining_html):
                                html_pos += 1
                            continue
                        if text_pos < pos_in_text + len(orig_text):
                            html_pos += 1
                            text_pos += 1
                    
                    # 在找到的位置插入 </p><p> 标签
                    if html_pos > 0 and html_pos < len(remaining_html):
                        parts.append(remaining_html[:html_pos])
                        remaining_html = remaining_html[html_pos:]
                        remaining_text = remaining_text[pos_in_text + len(orig_text):]
                    else:
                        # 如果计算位置失败，尝试使用文本位置估算
                        # 简化方法：按照文本比例估算 HTML 位置
                        text_ratio = (pos_in_text + len(orig_text)) / len(remaining_text) if remaining_text else 0
                        html_split_pos = int(len(remaining_html) * text_ratio)
                        if html_split_pos > 0 and html_split_pos < len(remaining_html):
                            parts.append(remaining_html[:html_split_pos])
                            remaining_html = remaining_html[html_split_pos:]
                            remaining_text = remaining_text[pos_in_text + len(orig_text):]
                
                # 如果成功拆分成多个部分，重新组合成多个 <p> 标签
                if len(parts) >= 2:
                    return ''.join(f'<p{attrs}>{part}</p>' for part in parts if part.strip())
            
            return match.group(0)  # 保持原样
        
        return pattern.sub(_replace, html_content)
    
    # 启用强制拆分逻辑，作为最后的保险措施
    html = force_split_merged_paragraphs(html, original_paragraph_lines)
    
    # 后处理 - 为标题添加 class 和确保 ID 存在，为段落添加 class
    # 为 h1, h2, h3 添加 heading class 和 level class（如果还没有 class）
    def add_heading_class(match):
        level = match.group(1)  # 1, 2, 3 (数字字符串)
        attrs = match.group(2)  # 现有属性
        
        # 检查是否已有 class
        if 'class=' not in attrs:
            attrs = f'{attrs} class="heading level-{level}"'
        elif 'heading' not in attrs:
            # 如果已有 class 但没有 heading，则追加
            attrs = re_module.sub(
                r'class="([^"]*)"',
                rf'class="\1 heading level-{level}"',
                attrs
            )
        
        return f'<h{level}{attrs}>'
    
    html = re_module.sub(
        r'<h([123])([^>]*)>',
        add_heading_class,
        html
    )
    
    # 为段落添加 paragraph class（包括已有 class 的情况）
    def add_paragraph_class(match):
        attrs = match.group(1)
        if 'class=' not in attrs:
            attrs = f'{attrs} class="paragraph"'
        elif 'paragraph' not in attrs:
            # 如果已有 class 但没有 paragraph，则追加
            attrs = re_module.sub(
                r'class="([^"]*)"',
                r'class="\1 paragraph"',
                attrs
            )
        return f'<p{attrs}>'
    
    html = re_module.sub(
        r'<p([^>]*)>',
        add_paragraph_class,
        html
    )
    
    # 确保所有标题都有 ID（如果 toc 扩展没有生成，则使用 section-N 格式）
    header_index = [0]  # 使用列表以便在闭包中修改
    
    def ensure_all_headings_have_id(html_content):
        nonlocal header_index
        
        # 匹配所有 h1, h2, h3 标签（包括开始和结束标签）
        # 使用非贪婪匹配来处理标题内容可能包含 HTML 的情况
        pattern = r'<h([123])([^>]*)>(.*?)</h\1>'
        
        def replace_heading(match):
            nonlocal header_index
            level = match.group(1)
            attrs = match.group(2)
            content = match.group(3)
            
            # 检查是否已有 id
            if 'id=' not in attrs:
                header_index[0] += 1
                heading_id = f"section-{header_index[0]}"
                attrs = f'{attrs} id="{heading_id}"'
            
            return f'<h{level}{attrs}>{content}</h{level}>'
        
        return re_module.sub(pattern, replace_heading, html_content, flags=re_module.DOTALL)
    
    html = ensure_all_headings_have_id(html)
    
    # 第五步：清除空段落标签（禁止空行渲染）
    # 移除所有空的 <p></p>、<p> </p>、<p>&nbsp;</p> 等空段落标签
    def remove_empty_paragraphs(html_content: str) -> str:
        """
        移除所有空段落标签，避免产生额外的、不可控的垂直间距
        - <p></p>
        - <p> </p>（仅包含空白字符）
        - <p>&nbsp;</p>（包含不间断空格）
        - <p>\u00A0</p>（包含不间断空格）
        - <p>\u3000</p>（包含全角空格）
        
        注意：包含 <img> 等自闭合媒体标签的段落**必须保留**，不能误判为空段落。
        """
        # 匹配所有 <p> 标签及其内容
        pattern = re_module.compile(r'<p([^>]*)>(.*?)</p>', re_module.DOTALL)
        
        def _replace(match):
            attrs = match.group(1)
            inner = match.group(2)
            
            # ★ 关键保护：如果段落内包含 <img 标签，绝对不能删除
            #   Markdown 渲染 ![alt](url) 后生成 <p><img ...></p>
            #   这种段落的纯文本为空，但图片就在里面，不能误杀
            if re_module.search(r'<img\b', inner, re_module.IGNORECASE):
                return match.group(0)
            
            # 移除所有 HTML 标签，获取纯文本内容
            text_content = re_module.sub(r'<[^>]+>', '', inner)
            # 移除所有空白字符（包括空格、制表符、换行符、不间断空格、全角空格等）
            text_content = re_module.sub(r'[\s\u00A0\u3000]+', '', text_content)
            
            # 如果纯文本内容为空，则移除这个段落标签
            if not text_content.strip():
                return ''
            
            # 否则保持原样
            return match.group(0)
        
        html_content = pattern.sub(_replace, html_content)
        
        # 清理可能产生的连续空行（多个空段落被移除后可能留下的）
        html_content = re_module.sub(r'\n\s*\n\s*\n+', '\n\n', html_content)
        
        return html_content
    
    html = remove_empty_paragraphs(html)

    # 第六步：安全清洗 HTML，严格基于白名单放行（允许 img 与必要属性）
    # 顺序要求：Markdown -> 段落/标题后处理 -> remove_empty_paragraphs -> bleach.clean -> 懒加载替换
    html = bleach.clean(
        html,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRIBUTES,
        strip=True,
    )
    
    # 第七步：将正文中的 <img> 转换为懒加载格式
    # 目标格式示例（与 lazysizes 官方推荐格式保持一致）：
    #   <img
    #       class="lazyload"
    #       data-src="/static/uploads/xxx.png"
    #       src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="
    #       alt="图片描述"
    #   >
    # 注意：必须保留一个 1x1 的透明占位图到 src 上，否则部分浏览器可能不会渲染元素或出现异常请求
    def apply_lazyload_to_images(html_content: str) -> str:
        img_pattern = re_module.compile(r'<img([^>]*?)src="([^"]+)"([^>]*)>', re_module.IGNORECASE)

        def _img_repl(match):
            before = match.group(1) or ""
            src_url = match.group(2) or ""
            after = match.group(3) or ""
            attrs = f"{before}{after}"

            # 如果已经有 data-src，则认为已经处理过
            if "data-src" in attrs:
                return match.group(0)

            # 追加或注入 lazyload class
            if "class=" in attrs:
                attrs = re_module.sub(
                    r'class="([^"]*)"',
                    lambda m: f'class="{m.group(1)} lazyload"',
                    attrs,
                    count=1,
                )
            else:
                attrs = f'{attrs} class="lazyload"'

            # 去掉多余空白
            attrs = re_module.sub(r"\s+", " ", attrs).strip()

            # 透明 1x1 GIF 占位符，防止空 src 带来的兼容性问题
            placeholder = "data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="

            return f'<img {attrs} src="{placeholder}" data-src="{src_url}">'

        return img_pattern.sub(_img_repl, html_content)

    html = apply_lazyload_to_images(html)
    
    # 根据参数决定返回值
    if return_toc:
        return Markup(html), toc_html
    return Markup(html)


@app.context_processor
def inject_helpers():
    # 让模板里可以直接使用 render_content
    return {"render_content": render_content}


@app.route("/")
def index():
    """门户主页：展示 Logo 和入口卡片"""
    return render_template("portal.html")


@app.route("/notes")
def notes():
    """笔记列表页：扁平化列表，按创建日期分组展示，支持分类过滤和搜索"""
    try:
        # 获取查询参数（Flask 自动解码 URL 编码的中文参数）
        main_category = request.args.get("mainCategory", "").strip()
        sub_category = request.args.get("subCategory", "").strip()
        tag_filter = request.args.get("tag", "").strip()
        search_query = request.args.get("q", "").strip()
        global_search = request.args.get("global", "false").lower() == "true"

        # 构建查询
        query = Note.query

        # 时间过滤：支持按具体日期(day)或按年月(month)过滤
        day_str = request.args.get("day", "").strip()
        month_str = request.args.get("month", "").strip()
        day_filter = None
        month_filter_start = None
        month_filter_end = None

        if day_str:
            try:
                day_filter = datetime.strptime(day_str, "%Y-%m-%d").date()
                start_dt = datetime.combine(day_filter, datetime.min.time())
                end_dt = datetime.combine(day_filter, datetime.max.time())
                query = query.filter(Note.created_at >= start_dt, Note.created_at <= end_dt)
            except Exception:
                day_filter = None

        if month_str and not day_filter:
            try:
                # 解析 YYYY-MM
                ym = datetime.strptime(month_str, "%Y-%m")
                month_filter_start = datetime(ym.year, ym.month, 1)
                if ym.month == 12:
                    month_filter_end = datetime(ym.year + 1, 1, 1)
                else:
                    month_filter_end = datetime(ym.year, ym.month + 1, 1)
                query = query.filter(Note.created_at >= month_filter_start, Note.created_at < month_filter_end)
            except Exception:
                month_str = ""

        # 一级分类过滤
        if main_category:
            query = query.filter(Note.mainCategory == main_category)

        # 二级分类过滤
        if sub_category:
            query = query.filter(Note.subCategory == sub_category)

        # 三级标签过滤：同时匹配 subCategory（二级分类）和 tags_json（三级标签）
        # 支持模糊匹配，处理 JSON 格式和空格问题
        if tag_filter:
            # 清理标签参数：去除前后空格
            tag_filter_clean = tag_filter.strip()
            # 同时匹配 subCategory 字段和 tags_json JSON 数组
            # tags_json 格式：["标签1", "标签2"]，使用 LIKE 匹配 JSON 字符串中的标签
            query = query.filter(
                db.or_(
                    Note.subCategory == tag_filter_clean,  # 精确匹配二级分类
                    Note.subCategory.like(f'%{tag_filter_clean}%'),  # 模糊匹配二级分类
                    Note.tags_json.like(f'%\"{tag_filter_clean}\"%'),  # 匹配 JSON 数组中的标签（带引号）
                    Note.tags_json.like(f'%{tag_filter_clean}%')  # 模糊匹配 JSON 中的标签（兼容其他格式）
                )
            )

        # 搜索：如果不在全局搜索模式，且已选择二级分类，则只在当前分类搜索
        if search_query:
            if not global_search and sub_category:
                # 分类内搜索：标题和内容
                query = query.filter(
                    db.or_(
                        Note.title.like(f'%{search_query}%'),
                        Note.content.like(f'%{search_query}%')
                    )
                )
            else:
                # 全局搜索：标题、内容、标签
                query = query.filter(
                    db.or_(
                        Note.title.like(f'%{search_query}%'),
                        Note.content.like(f'%{search_query}%'),
                        Note.tags.like(f'%{search_query}%'),
                        Note.tags_json.like(f'%{search_query}%')
                    )
                )

        # 结果排序策略：
        # - 默认：按 created_at 倒序（最新在前）
        # - 标签合集模式（tag_filter）：按“发布日期/时间戳”升序（最早在前），用于“从第一章到最后一章”的阅读顺序
        def _collection_sort_key(n: "Note"):
            # 1) 优先使用 publishDate（YYYY-MM-DD）；2) 否则回退 created_at
            if getattr(n, "publishDate", None):
                try:
                    pd = datetime.strptime(n.publishDate, "%Y-%m-%d")
                    # 用 created_at 做二级排序，避免同日乱序
                    return (0, pd, n.created_at or datetime.min, n.id)
                except Exception:
                    pass
            return (1, n.created_at or datetime.min, n.id)

        tag_collection_notes = []
        grouped_list = []

        if tag_filter:
            # 合集化：升序排列
            notes = query.all()
            notes.sort(key=_collection_sort_key)
            tag_collection_notes = notes
        else:
            # 默认列表：倒序排列并按天分组
            notes = query.order_by(Note.created_at.desc()).all()

            grouped_notes = {}
            for note in notes:
                date_key = note.created_at.date()
                if date_key not in grouped_notes:
                    grouped_notes[date_key] = []
                grouped_notes[date_key].append(note)

            grouped_list = sorted(grouped_notes.items(), key=lambda x: x[0], reverse=True)

        # 获取所有分类数据用于侧边栏
        all_notes = Note.query.all()
        main_categories = set()
        sub_categories = {}
        all_tags = set()

        for note in all_notes:
            if note.mainCategory:
                main_categories.add(note.mainCategory)
                if note.mainCategory not in sub_categories:
                    sub_categories[note.mainCategory] = set()
            if note.subCategory:
                if note.mainCategory:
                    sub_categories[note.mainCategory].add(note.subCategory)
            # 收集所有标签
            tags_list = note.get_tags_list()
            all_tags.update(tags_list)

        # 转换为排序列表
        main_categories = sorted(main_categories)
        for key in sub_categories:
            sub_categories[key] = sorted(sub_categories[key])
        all_tags = sorted(all_tags)

        # 每日金句：从有批注的文章中随机抽取一条高亮文本（仅展示纯文本，避免首页渲染 HTML）
        daily_quote = None
        try:
            annotated_notes = (
                Note.query
                .filter(Note.annotations.isnot(None), Note.annotations != "")
                .order_by(func.random())
                .limit(100)
                .all()
            )
            snippets = []
            for n in annotated_notes:
                try:
                    items = json.loads(n.annotations)
                    if isinstance(items, list):
                        for item in items:
                            text_val = (item.get("text") or "").strip()
                            if text_val:
                                snippets.append(text_val)
                except Exception:
                    continue
            if snippets:
                daily_quote = random.choice(snippets)
                # 去掉可能存在的 HTML 标签
                daily_quote = re.sub(r"<[^>]+>", "", daily_quote).strip()
                # 太长则截断，首页保持“金句”观感
                if len(daily_quote) > 100:
                    daily_quote = daily_quote[:100] + "..."
        except Exception:
            daily_quote = None

        # 贡献热力图数据：统计最近一年内每天创建的 Note 数量
        today = date.today()
        start_date = today - timedelta(days=364)
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(today, datetime.max.time())

        contrib_rows = (
            db.session.query(
                func.date(Note.created_at).label("day"),
                func.count(Note.id)
            )
            .filter(Note.created_at >= start_dt, Note.created_at <= end_dt)
            .group_by(func.date(Note.created_at))
            .all()
        )
        contribution_heatmap_data = {}
        for day_val, count_val in contrib_rows:
            # SQLite 的 func.date 返回 str 或 date，兼容处理
            if isinstance(day_val, datetime):
                day_obj = day_val.date()
            elif isinstance(day_val, date):
                day_obj = day_val
            else:
                try:
                    day_obj = datetime.strptime(str(day_val), "%Y-%m-%d").date()
                except Exception:
                    continue
            contribution_heatmap_data[day_obj.strftime("%Y-%m-%d")] = int(count_val or 0)

        # 历史时间轴：按年月聚合文章数量
        month_rows = (
            db.session.query(
                func.strftime("%Y-%m", Note.created_at).label("ym"),
                func.count(Note.id)
            )
            .group_by("ym")
            .order_by(text("ym DESC"))
            .all()
        )
        timeline_archives = []
        for ym_val, cnt in month_rows:
            if not ym_val:
                continue
            try:
                year_int, month_int = ym_val.split("-")
                year_int = int(year_int)
                month_int = int(month_int)
            except Exception:
                continue
            timeline_archives.append(
                {
                    "ym": ym_val,
                    "year": year_int,
                    "month": month_int,
                    "count": int(cnt or 0),
                }
            )

        return render_template(
            "index.html",
            grouped_notes=grouped_list,
            tag_collection_notes=tag_collection_notes,
            main_categories=main_categories,
            sub_categories=sub_categories,
            all_tags=all_tags,
            current_main_category=main_category,
            current_sub_category=sub_category,
            current_tag=tag_filter,
            search_query=search_query,
            global_search=global_search,
            daily_quote=daily_quote,
            contribution_heatmap_data=contribution_heatmap_data,
            contribution_start_date=start_date.strftime("%Y-%m-%d"),
            contribution_end_date=today.strftime("%Y-%m-%d"),
            timeline_archives=timeline_archives,
            current_month_filter=month_str,
            current_day_filter=day_str,
        )
    except Exception as e:
        # 将 /notes 的异常单独记录到 notes_error.log，便于快速定位
        try:
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes_error.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write("\n===== /notes Exception at {} =====\n".format(datetime.utcnow().isoformat()))
                f.write(f"Type: {type(e)}\n")
                f.write(f"Detail: {repr(e)}\n")
                f.write(traceback.format_exc())
                f.write("\n")
        except Exception:
            pass
        # 继续让全局 errorhandler / 默认机制处理该异常
        raise


@app.route("/memos")
def memos_page():
    """随心记页面：极简短信流式记忆，不干扰长文体系"""
    return render_template("memos.html")


@app.route("/my_quotes")
def my_quotes_page():
    """
    摘抄语录本：集中展示所有带批注的高亮句子，按“文章”分组。
    """
    article_groups = collect_quote_items()
    return render_template("my_quotes.html", article_groups=article_groups)


@app.route("/my_quotes/export")
def export_my_quotes():
    """
    将所有摘抄导出为 Word 文档（公文友好格式），按“文章”分组。
    """
    article_groups = collect_quote_items()

    if not Document:
        # 未安装 python-docx 时给出友好提示
        return (
            "当前环境未安装 python-docx，请先在服务器上执行 pip install python-docx 后重试导出。",
            500,
        )

    doc = Document()

    def _set_run_font(run, east_asia_name: str, latin_name: str = None, size_pt: int = None, bold: bool = None):
        if bold is not None:
            run.bold = bool(bold)
        if size_pt and Pt:
            run.font.size = Pt(size_pt)
        if latin_name:
            run.font.name = latin_name
        # 设置东亚字体（中文）
        if qn:
            r = run._element
            rPr = r.get_or_add_rPr()
            rFonts = rPr.get_or_add_rFonts()
            rFonts.set(qn("w:eastAsia"), east_asia_name)

    def _set_paragraph_format(p, line_spacing_pt: int = 28):
        if not p:
            return
        try:
            if WD_LINE_SPACING:
                p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
            if Pt:
                p.paragraph_format.line_spacing = Pt(line_spacing_pt)
        except Exception:
            pass

    # 全局正文：仿宋
    try:
        normal = doc.styles["Normal"]
        if Pt:
            normal.font.size = Pt(12)
        normal.font.name = "FangSong"
        if qn:
            normal._element.rPr.rFonts.set(qn("w:eastAsia"), "仿宋")
    except Exception:
        pass

    # 标题
    title_p = doc.add_paragraph()
    run = title_p.add_run("摘抄语录本")
    _set_run_font(run, east_asia_name="黑体", latin_name="SimHei", size_pt=16, bold=True)
    if WD_ALIGN_PARAGRAPH:
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_paragraph_format(title_p, 28)

    for group in article_groups:
        # 文章标题作为一级标题
        heading_p = doc.add_paragraph()
        heading_run = heading_p.add_run(str(group.get("note_title") or "未命名文章"))
        _set_run_font(heading_run, east_asia_name="黑体", latin_name="SimHei", size_pt=14, bold=True)
        _set_paragraph_format(heading_p, 28)

        items = group.get("items") or []
        for idx, q in enumerate(items, start=1):
            p = doc.add_paragraph()
            # 原文
            run_text_label = p.add_run(f"{idx}. 原文：")
            _set_run_font(run_text_label, east_asia_name="黑体", latin_name="SimHei", bold=True)
            # 去掉 HTML 标签，Word 里只保留纯文本
            quote_plain = re.sub(r"<[^>]+>", "", q.get("text") or "")
            run_text = p.add_run(quote_plain)
            _set_run_font(run_text, east_asia_name="仿宋", latin_name="FangSong")
            p.add_run("\n")
            # 批注
            if q.get("comment"):
                run_c_label = p.add_run("   批注：")
                _set_run_font(run_c_label, east_asia_name="黑体", latin_name="SimHei", bold=True)
                run_c = p.add_run(q["comment"])
                _set_run_font(run_c, east_asia_name="仿宋", latin_name="FangSong")
                p.add_run("\n")
            # 来源
            run_src_label = p.add_run("   来源：")
            _set_run_font(run_src_label, east_asia_name="黑体", latin_name="SimHei", bold=True)
            run_src = p.add_run(f"《{q['note_title']}》")
            _set_run_font(run_src, east_asia_name="仿宋", latin_name="FangSong")
            _set_paragraph_format(p, 28)

    # 输出为响应
    output_path = os.path.join(os.getcwd(), "my_quotes_export.docx")
    doc.save(output_path)

    with open(output_path, "rb") as f:
        data = f.read()

    response = make_response(data)
    response.headers[
        "Content-Type"
    ] = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    response.headers["Content-Disposition"] = "attachment; filename=my_quotes_export.docx"
    return response


@app.route("/api/activity_stats", methods=["GET"])
def api_activity_stats():
    """
    API：贡献热力图统计

    以「当前系统时间」为基准，统计最近一年内（含今天）每天创建的 Note 数量。

    返回结构：完整的 365 天时间序列（没有文章的日期返回 0），例如：
        {
            "2025-03-10": 3,
            "2025-03-11": 0,
            ...
        }

    说明：
    - 使用 Note.created_at 字段作为时间基准
    - 仅按天聚合，不区分具体时间
    - 始终覆盖从 (now - 364 天) 到 today 共 365 天，避免因为数据缺失导致前端“截断”
    """
    # 使用 datetime.now() 作为时间基准，确保以当前系统时间为参照
    now = datetime.now()
    today = now.date()
    start_date = today - timedelta(days=364)

    # 构造起止时间（天粒度）：含当天 00:00:00 ~ 23:59:59
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(today, datetime.max.time())

    # 查询最近一年的每天文章数量（只返回有数据的日期）
    rows = (
        db.session.query(
            func.date(Note.created_at).label("day"),
            func.count(Note.id),
        )
        .filter(Note.created_at >= start_dt, Note.created_at <= end_dt)
        .group_by(func.date(Note.created_at))
        .all()
    )

    # 先将真实有数据的日期映射出来
    raw_stats = {}
    for day_val, count_val in rows:
        if isinstance(day_val, datetime):
            day_obj = day_val.date()
        elif isinstance(day_val, date):
            day_obj = day_val
        else:
            try:
                day_obj = datetime.strptime(str(day_val), "%Y-%m-%d").date()
            except Exception:
                continue
        raw_stats[day_obj.strftime("%Y-%m-%d")] = int(count_val or 0)

    # 再根据「完整的 365 天序列」补齐没有文章的日期（填 0）
    full_stats = {}
    cursor = start_date
    while cursor <= today:
        key = cursor.strftime("%Y-%m-%d")
        full_stats[key] = raw_stats.get(key, 0)
        cursor += timedelta(days=1)

    response = jsonify(full_stats)
    # 禁止缓存，确保前端每次获取到最新统计
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/api/tag_collection", methods=["GET"])
def api_tag_collection():
    """API：获取某个标签下的合集目录（升序），用于详情页"上一篇/下一篇"导航"""
    tag = request.args.get("tag", "").strip()
    if not tag:
        response = jsonify({"tag": "", "notes": []})
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    # 清理标签参数：去除前后空格
    tag_clean = tag.strip()
    # 查询该标签下的所有笔记：同时匹配 subCategory（二级分类）和 tags_json（三级标签）
    # 支持模糊匹配，处理 JSON 格式和空格问题
    query = Note.query.filter(
        db.or_(
            Note.subCategory == tag_clean,  # 精确匹配二级分类
            Note.subCategory.like(f'%{tag_clean}%'),  # 模糊匹配二级分类
            Note.tags_json.like(f'%"{tag_clean}"%'),  # 匹配 JSON 数组中的标签（带引号）
            Note.tags_json.like(f'%{tag_clean}%')  # 模糊匹配 JSON 中的标签（兼容其他格式）
        )
    )

    def _collection_sort_key(n: "Note"):
        if getattr(n, "publishDate", None):
            try:
                pd = datetime.strptime(n.publishDate, "%Y-%m-%d")
                return (0, pd, n.created_at or datetime.min, n.id)
            except Exception:
                pass
        return (1, n.created_at or datetime.min, n.id)

    notes = query.all()
    notes.sort(key=_collection_sort_key)

    payload = []
    for n in notes:
        payload.append({
            "id": n.id,
            "title": n.title,
            "publishDate": n.publishDate or "",
            "created_at": n.created_at.isoformat() if n.created_at else ""
        })

    response = jsonify({"tag": tag, "notes": payload})
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route("/note/<int:note_id>")
def view_note(note_id: int):
    """阅读页：按照公文 A4 版式展示内容"""
    # 读取上下文参数：如果从“专题合集/标签”进入，URL 会携带 ?tag=xxx
    current_tag = request.args.get("tag", "").strip() or None

    # 强制数据透传：每次都从数据库直接读取最新数据，严禁使用任何中间缓存
    # 1. 先清除session中可能存在的该对象缓存（只清除当前note对象，不影响其他查询）
    try:
        # 尝试获取可能已存在的对象
        existing_note = db.session.get(Note, note_id)
        if existing_note:
            db.session.expire(existing_note)
    except Exception:
        pass
    
    # 2. 使用新的查询，确保从数据库读取最新数据
    note = db.session.query(Note).filter_by(id=note_id).first_or_404()
    
    # 3. 强制刷新对象，确保获取最新的数据库内容（重新从数据库加载所有字段）
    db.session.expire(note)
    db.session.refresh(note)
    
    # 渲染内容并提取 TOC（使用最新从数据库读取的content）
    content_html, toc_html = render_content(note.content, return_toc=True)
    # 计算当前篇目的字数（不影响渲染，只用于右侧展示）
    word_count = estimate_text_length(note.content or "")

    # 上一篇 / 下一篇导航（支持专题合集上下文）
    nav_prev = None
    nav_next = None

    def _collection_sort_key(n: "Note"):
        # 1) 优先使用 publishDate（YYYY-MM-DD）；2) 否则回退 created_at
        if getattr(n, "publishDate", None):
            try:
                pd = datetime.strptime(n.publishDate, "%Y-%m-%d")
                return (0, pd, n.created_at or datetime.min, n.id)
            except Exception:
                pass
        return (1, n.created_at or datetime.min, n.id)

    try:
        if current_tag:
            tag_clean = current_tag.strip()
            # 同时匹配 subCategory（二级分类）和 tags_json（三级标签）
            query = Note.query.filter(
                db.or_(
                    Note.subCategory == tag_clean,
                    Note.subCategory.like(f'%{tag_clean}%'),
                    Note.tags_json.like(f'%"{tag_clean}"%'),
                    Note.tags_json.like(f'%{tag_clean}%')
                )
            )
            notes = query.all()
            notes.sort(key=_collection_sort_key)
        else:
            # 非合集模式：沿用列表页排序（最新在前）
            notes = Note.query.order_by(Note.created_at.desc(), Note.id.desc()).all()

        if notes:
            idx = next((i for i, n in enumerate(notes) if n.id == note_id), None)
            if idx is not None:
                if idx > 0:
                    nav_prev = notes[idx - 1]
                if idx < len(notes) - 1:
                    nav_next = notes[idx + 1]
    except Exception as _e:
        # 导航计算失败不应影响阅读页正常渲染
        nav_prev = None
        nav_next = None

    # 调试输出：打印数据库内容和渲染后的HTML（前500字符），用于排查缓存问题
    try:
        print(f"\n====== DEBUG NOTE {note_id} CONTENT START ======")
        print(f"[DB Content] 前500字符: {note.content[:500]}")
        print(f"[Rendered HTML] 前500字符: {str(content_html)[:500]}")
        print(f"======= DEBUG NOTE {note_id} CONTENT END =======\n")
    except Exception as e:
        print(f"[WARN] Failed to print content for note {note_id}: {e}")

    # 调试输出：在终端打印后端生成的大纲 HTML，方便排查为什么前端没有展示
    try:
        print("\n====== DEBUG TOC_HTML START ======")
        if toc_html:
            # 为了避免一次性输出太长，只显示前 2000 个字符
            preview = toc_html[:2000]
            print(preview)
            if len(toc_html) > 2000:
                print(f"... (total length: {len(toc_html)} chars, only preview above)")
        else:
            print("toc_html is EMPTY or None")
        print("======= DEBUG TOC_HTML END =======\n")
    except Exception as e:
        # 即便调试输出失败，也不要影响正常请求
        print(f"[WARN] Failed to print toc_html for note {note_id}: {e}")
    
    response = make_response(
        render_template(
            "note.html",
            note=note,
            content_html=content_html,
            toc_html=toc_html,
            nav_prev=nav_prev,
            nav_next=nav_next,
            current_tag=current_tag,
            word_count=word_count,
        )
    )
    # 添加缓存控制头，防止浏览器缓存页面内容
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route("/api/note/<int:note_id>/annotations", methods=["GET", "POST"])
def note_annotations(note_id: int):
    """API：获取或保存笔记的批注数据"""
    note = Note.query.get_or_404(note_id)
    
    if request.method == "POST":
        data = request.get_json()
        annotations_json = json.dumps(data.get("annotations", []), ensure_ascii=False)
        note.annotations = annotations_json
        db.session.commit()
        response = jsonify({"success": True})
        # 添加no-cache头部，确保每次获取最新数据
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    # GET：返回批注数据
    if note.annotations:
        try:
            annotations = json.loads(note.annotations)
        except:
            annotations = []
    else:
        annotations = []
    
    response = jsonify({"annotations": annotations})
    # 添加no-cache头部，确保每次获取最新数据
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route("/api/note/<int:note_id>/detail", methods=["GET"])
def get_note_detail(note_id: int):
    """API：获取笔记详情（JSON格式），强制从数据库读取最新数据"""
    # 强制数据透传：每次都从数据库直接读取最新数据，严禁使用任何中间缓存
    # 1. 先清除session中可能存在的该对象缓存（只清除当前note对象，不影响其他查询）
    try:
        existing_note = db.session.get(Note, note_id)
        if existing_note:
            db.session.expire(existing_note)
    except Exception:
        pass
    
    # 2. 使用新的查询，确保从数据库读取最新数据
    note = db.session.query(Note).filter_by(id=note_id).first_or_404()
    
    # 3. 强制刷新对象，确保获取最新的数据库内容（重新从数据库加载所有字段）
    db.session.expire(note)
    db.session.refresh(note)
    
    # 渲染内容并提取 TOC
    content_html, toc_html = render_content(note.content, return_toc=True)
    
    response = jsonify({
        "id": note.id,
        "title": note.title,
        "content": note.content,  # 原始内容
        "content_html": content_html,  # 渲染后的HTML
        "toc_html": toc_html,
        "mainCategory": note.mainCategory,
        "subCategory": note.subCategory,
        "tags_list": note.get_tags_list(),
        "publishDate": note.publishDate,
        "sourceUrl": note.sourceUrl,
        "created_at": note.created_at.isoformat() if note.created_at else None,
        "updated_at": note.updated_at.isoformat() if note.updated_at else None
    })
    # 添加no-cache头部，确保每次获取最新数据
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route("/api/note/<int:note_id>/delete", methods=["DELETE"])
def delete_note(note_id: int):
    """API：删除文章"""
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    return jsonify({"success": True, "message": "文章已删除"})


@app.route("/api/note/<int:note_id>/related", methods=["GET"])
def get_related_notes(note_id: int):
    """API：获取关联文章（知识图谱）
    
    根据当前文章的 subCategory（二级分类）和 tags（三级标签）检索相似度最高的前5篇文章。
    逻辑权重：相同标签 > 相同二级分类。
    
    同时支持脉络识别：如果标题包含'方案'、'计划'或'行动'，自动检索标题中包含相同关键词的'总结'、'通报'或'调研报告'。
    """
    note = Note.query.get_or_404(note_id)
    
    # 获取当前文章的标签列表
    current_tags = note.get_tags_list()
    current_sub_category = note.subCategory
    current_title = note.title
    
    # 构建查询：排除当前文章
    query = Note.query.filter(Note.id != note_id)
    
    # 脉络识别：检测标题中的关键词
    task_chain_keywords = []
    task_chain_types = []
    
    # 检测标题中是否包含"方案"、"计划"或"行动"
    trigger_keywords = ['方案', '计划', '行动']
    found_trigger = None
    
    for keyword in trigger_keywords:
        if keyword in current_title:
            found_trigger = keyword
            task_chain_keywords.append(keyword)
            break
    
    # 如果检测到触发关键词，设置要检索的类型
    if found_trigger:
        task_chain_types = ['总结', '通报', '调研报告']
    
    # 如果检测到任务链，优先检索任务链相关文章
    task_chain_notes = []
    if task_chain_keywords and task_chain_types:
        # 检索标题中包含触发关键词（如"方案"）且包含类型关键词（如"总结"、"通报"、"调研报告"）的文章
        task_query = Note.query.filter(Note.id != note_id)
        
        # 构建标题匹配条件：必须包含触发关键词（如"方案"）
        trigger_conditions = []
        for keyword in task_chain_keywords:
            trigger_conditions.append(Note.title.like(f'%{keyword}%'))
        
        # 构建类型匹配条件：标题中包含类型关键词（"总结"、"通报"、"调研报告"）
        type_conditions = []
        for doc_type in task_chain_types:
            type_conditions.append(Note.title.like(f'%{doc_type}%'))
        
        if trigger_conditions and type_conditions:
            # 必须同时满足：包含触发关键词 AND 包含类型关键词
            task_query = task_query.filter(
                db.or_(*trigger_conditions)
            ).filter(
                db.or_(*type_conditions)
            )
        
        task_chain_notes = task_query.order_by(Note.created_at.desc()).limit(5).all()
    
    # 计算相似度并排序
    related_notes = []
    
    # 获取所有其他文章
    all_notes = query.all()
    
    for other_note in all_notes:
        score = 0
        other_tags = other_note.get_tags_list()
        
        # 计算标签匹配分数（权重更高）
        if current_tags and other_tags:
            common_tags = set(current_tags) & set(other_tags)
            score += len(common_tags) * 10  # 每个相同标签 +10 分
        
        # 计算二级分类匹配分数（权重较低）
        if current_sub_category and other_note.subCategory == current_sub_category:
            score += 5  # 相同二级分类 +5 分
        
        if score > 0:
            related_notes.append({
                'note': other_note,
                'score': score
            })
    
    # 按分数降序排序，取前5个
    related_notes.sort(key=lambda x: x['score'], reverse=True)
    related_notes = related_notes[:5]
    
    # 构建返回结果
    result = {
        'related': [],
        'task_chain': {
            'detected': len(task_chain_notes) > 0,
            'keywords': task_chain_keywords,
            'notes': []
        }
    }
    
    # 格式化关联文章
    for item in related_notes:
        note_obj = item['note']
        result['related'].append({
            'id': note_obj.id,
            'title': note_obj.title,
            'subCategory': note_obj.subCategory or '',
            'publishDate': note_obj.publishDate or '',
            'score': item['score']
        })
    
    # 格式化任务链文章
    for task_note in task_chain_notes:
        result['task_chain']['notes'].append({
            'id': task_note.id,
            'title': task_note.title,
            'subCategory': task_note.subCategory or '',
            'publishDate': task_note.publishDate or ''
        })
    
    response = jsonify(result)
    # 添加no-cache头部，确保每次获取最新数据
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route("/api/note/<int:note_id>/global-thought", methods=["GET", "POST", "DELETE"])
def note_global_thought(note_id: int):
    """API：获取或保存笔记的深度思考内容（块状化存储）"""
    note = Note.query.get_or_404(note_id)
    
    if request.method == "POST":
        data = request.get_json()
        # 块状化存储：每个笔记块作为独立记录
        thought_data = {
            "id": data.get("id") or f"thought_{datetime.utcnow().timestamp()}_{note_id}",
            "content": data.get("content", ""),
            "created_at": data.get("created_at") or datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # 解析现有的笔记块列表
        if note.global_thought:
            try:
                thoughts = json.loads(note.global_thought)
                if not isinstance(thoughts, list):
                    thoughts = []
            except:
                thoughts = []
        else:
            thoughts = []
        
        # 更新或添加笔记块
        existing_index = next((i for i, t in enumerate(thoughts) if t.get("id") == thought_data["id"]), None)
        if existing_index is not None:
            thoughts[existing_index] = thought_data
        else:
            thoughts.append(thought_data)
        
        note.global_thought = json.dumps(thoughts, ensure_ascii=False)
        db.session.commit()
        response = jsonify({"success": True, "thought": thought_data})
        # 添加no-cache头部，确保每次获取最新数据
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    if request.method == "DELETE":
        data = request.get_json()
        thought_id = data.get("id")
        
        if note.global_thought and thought_id:
            try:
                thoughts = json.loads(note.global_thought)
                if isinstance(thoughts, list):
                    thoughts = [t for t in thoughts if t.get("id") != thought_id]
                    note.global_thought = json.dumps(thoughts, ensure_ascii=False) if thoughts else None
                    db.session.commit()
            except:
                pass
        
        response = jsonify({"success": True})
        # 添加no-cache头部，确保每次获取最新数据
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    # GET：返回所有笔记块
    if note.global_thought:
        try:
            thoughts = json.loads(note.global_thought)
            if not isinstance(thoughts, list):
                thoughts = []
        except:
            thoughts = []
    else:
        thoughts = []
    
    response = jsonify({"thoughts": thoughts})
    # 添加no-cache头部，确保每次获取最新数据
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route("/new", methods=["GET", "POST"])
def new_note():
    """
    简单的新建素材页面：
    - 标题
    - 一级分类（全文、框架、短文摘要）
    - 二级分类（讲话精神、调研报告等）
    - 三级标签（数组形式）
    - 内容（支持 # / ## / ### 作为标题）
    先保证可以录入素材，再优化编辑体验。
    """
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        mainCategory = request.form.get("mainCategory", "").strip() or None
        subCategory = request.form.get("subCategory", "").strip() or None
        tags_input = request.form.get("tags", "").strip()  # 旧字段兼容
        tags_json_input = request.form.get("tags_json", "").strip()  # 新字段：JSON 数组或逗号分隔
        publishDate = request.form.get("publishDate", "").strip() or None
        sourceUrl = request.form.get("sourceUrl", "").strip() or None
        raw_content = request.form.get("content", "")
        
        # 先按讲话稿规则做一次轻量级结构化（自动识别“一、二、三、”“一是”“第一阶段”等）
        structured_raw = auto_structure_speech_markdown(raw_content)
        # 再执行深度格式清洗：去除行首空格，规范化换行
        content = deep_clean_content(structured_raw)

        # 校验时再使用 strip 判断是否为空，避免误删有效换行
        if not title or not content.strip():
            # 支持 AJAX 请求的 JSON 错误返回
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify(
                    {"success": False, "message": "标题和内容不能为空"}
                ), 400

            return render_template(
                "new.html",
                error="标题和内容不能为空",
                title=title,
                mainCategory=mainCategory,
                subCategory=subCategory,
                tags=tags_input,
                tags_json=tags_json_input,
                publishDate=publishDate or "",
                sourceUrl=sourceUrl or "",
                content=content,
            )

        # 处理三级标签（tags_json）- 现在从隐藏输入框获取 JSON 数组
        tags_list = []
        if tags_json_input:
            try:
                # 尝试解析 JSON 数组
                tags_list = json.loads(tags_json_input)
            except Exception:
                # 兼容旧格式：逗号分隔字符串
                tags_list = [tag.strip() for tag in tags_json_input.split(",") if tag.strip()]

        # 如果二级分类是新的，自动添加到数据库
        if subCategory:
            existing = CustomCategory.query.filter_by(name=subCategory).first()
            if not existing:
                new_category = CustomCategory(name=subCategory, main_category=mainCategory)
                db.session.add(new_category)

        note = Note(
            title=title,
            tags=tags_input,  # 保留旧字段兼容
            content=content,
            mainCategory=mainCategory,
            subCategory=subCategory,
            publishDate=publishDate,
            sourceUrl=sourceUrl,
        )
        note.set_tags_list(tags_list)
        
        db.session.add(note)
        db.session.commit()

        # 支持异步创建时返回 JSON，前端可获得详情页跳转地址
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(
                {
                    "success": True,
                    "message": "创建成功",
                    "note_id": note.id,
                    "redirect_url": url_for("view_note", note_id=note.id),
                }
            ), 200

        return redirect(url_for("view_note", note_id=note.id))

    # GET 请求：传递预置分类和标签数据
    all_categories = CustomCategory.query.order_by(CustomCategory.name).all()
    categories_by_main = {}
    for cat in all_categories:
        main = cat.main_category or "其他"
        if main not in categories_by_main:
            categories_by_main[main] = []
        categories_by_main[main].append(cat.name)
    
    # 默认发布日期：当天日期
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    return render_template(
        "new.html",
                         preset_categories=PRESET_CATEGORIES,
                         categories_by_main=categories_by_main,
        preset_tags=PRESET_TAGS,
        current_date=today_str,
        # 默认值：新建时一级分类默认选中“全文”
        mainCategory="全文",
    )


# 兼容：部分模板/前端可能仍使用 /add
@app.route("/add", methods=["GET", "POST"])
def add_note():
    return new_note()


@app.route("/edit/<int:note_id>", methods=["GET", "POST"])
def edit_note(note_id: int):
    """
    二次加工 / 修改已有素材：
    - GET: 回填已有 title / tags / content / 分类 到纯净编辑表单
    - POST: 保存用户修改，更新 updated_at，保持用户的 # / ## 标记与换行结构
    """
    note = Note.query.get_or_404(note_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        mainCategory = request.form.get("mainCategory", "").strip() or None
        subCategory = request.form.get("subCategory", "").strip() or None
        tags = request.form.get("tags", "").strip()  # 旧字段兼容
        tags_json_input = request.form.get("tags_json", "").strip()  # 新字段
        publishDate = request.form.get("publishDate", "").strip() or None
        sourceUrl = request.form.get("sourceUrl", "").strip() or None
        raw_content = request.form.get("content", "")

        # 与新建逻辑保持一致：先结构化讲话稿，再做深度清洗
        structured_raw = auto_structure_speech_markdown(raw_content)
        # 执行深度格式清洗：去除行首空格，规范化换行（与新建时保持一致）
        content = deep_clean_content(structured_raw)

        if not title or not content.strip():
            return render_template(
                "edit.html",
                error="标题和内容不能为空",
                note=note,
                title=title,
                mainCategory=mainCategory,
                subCategory=subCategory,
                tags=tags,
                tags_json=tags_json_input,
                publishDate=publishDate or "",
                sourceUrl=sourceUrl or "",
                content=content,
            )

        # 处理三级标签（tags_json）- 现在从隐藏输入框获取 JSON 数组
        tags_list = []
        if tags_json_input:
            try:
                # 尝试解析 JSON 数组
                tags_list = json.loads(tags_json_input)
            except:
                # 兼容旧格式：逗号分隔字符串
                tags_list = [tag.strip() for tag in tags_json_input.split(",") if tag.strip()]

        # 如果二级分类是新的，自动添加到数据库
        if subCategory:
            existing = CustomCategory.query.filter_by(name=subCategory).first()
            if not existing:
                new_category = CustomCategory(name=subCategory, main_category=mainCategory)
                db.session.add(new_category)

        note.title = title
        note.tags = tags  # 保留旧字段兼容
        note.content = content
        note.mainCategory = mainCategory
        note.subCategory = subCategory
        note.publishDate = publishDate
        note.sourceUrl = sourceUrl
        note.set_tags_list(tags_list)
        note.updated_at = datetime.utcnow()

        # 提交数据库事务，确保数据写入成功
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    "success": False,
                    "message": f"数据库写入失败: {str(e)}"
                }), 500
            return render_template(
                "edit.html",
                error=f"保存失败: {str(e)}",
                note=note,
                title=title,
                mainCategory=mainCategory,
                subCategory=subCategory,
                tags=tags,
                tags_json=tags_json_input,
                publishDate=publishDate or "",
                sourceUrl=sourceUrl or "",
                content=content,
            )
        
        # 确保数据已刷新：从数据库重新加载对象，避免缓存问题
        # 强制刷新对象，确保获取最新的数据库内容
        db.session.expire(note)
        db.session.refresh(note)
        
        # 验证数据确实已写入：重新查询数据库确认
        verify_note = db.session.query(Note).filter_by(id=note.id).first()
        if not verify_note or verify_note.content != content:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    "success": False,
                    "message": "数据验证失败，请重试"
                }), 500
            return render_template(
                "edit.html",
                error="数据验证失败，请重试",
                note=note,
                title=title,
                mainCategory=mainCategory,
                subCategory=subCategory,
                tags=tags,
                tags_json=tags_json_input,
                publishDate=publishDate or "",
                sourceUrl=sourceUrl or "",
                content=content,
            )

        # 如果是异步请求（AJAX），返回JSON响应
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "success": True,
                "message": "保存成功",
                "note_id": note.id,
                "redirect_url": url_for("view_note", note_id=note.id)
            }), 200

        return redirect(url_for("view_note", note_id=note.id))

    # GET：回填原始内容，保留用户的 # / ## / ### 与所有手动换行
    tags_list = note.get_tags_list()
    
    # 传递预置分类和标签数据
    all_categories = CustomCategory.query.order_by(CustomCategory.name).all()
    categories_by_main = {}
    for cat in all_categories:
        main = cat.main_category or "其他"
        if main not in categories_by_main:
            categories_by_main[main] = []
        categories_by_main[main].append(cat.name)
    
    return render_template(
        "edit.html",
        note=note,
        title=note.title,
        tags=note.tags or "",
        tags_json=json.dumps(tags_list, ensure_ascii=False) if tags_list else "[]",
        mainCategory=note.mainCategory or "",
        subCategory=note.subCategory or "",
        publishDate=note.publishDate or "",
        sourceUrl=note.sourceUrl or "",
        content=note.content,
        preset_categories=PRESET_CATEGORIES,
        categories_by_main=categories_by_main,
        preset_tags=PRESET_TAGS,
    )


@app.route("/api/categories", methods=["GET"])
def get_categories():
    """获取所有二级分类（按一级分类分组）
    返回：系统预置分类 + CustomCategory 表中的分类 + notes 表中已存在的所有分类（DISTINCT）
    强制从数据库查询最新数据，禁止缓存
    """
    main_category = request.args.get("mainCategory", "").strip()
    
    # 1. 从 CustomCategory 表获取分类
    if main_category:
        # 如果指定了一级分类，优先返回相关的二级分类
        categories = CustomCategory.query.filter_by(main_category=main_category).order_by(CustomCategory.name).all()
        other_categories = CustomCategory.query.filter(CustomCategory.main_category != main_category).order_by(CustomCategory.name).all()
        category_set = {cat.name for cat in categories} | {cat.name for cat in other_categories}
    else:
        # 返回所有分类
        categories = CustomCategory.query.order_by(CustomCategory.name).all()
        category_set = {cat.name for cat in categories}
    
    # 2. 从 notes 表的 subCategory 字段 DISTINCT 查询所有已存在的分类
    # 使用 SQLAlchemy 的 distinct() 方法，强制从数据库查询最新数据
    existing_subcategories = db.session.query(distinct(Note.subCategory)).filter(
        Note.subCategory.isnot(None),
        Note.subCategory != ""
    ).all()
    
    # 将查询结果添加到集合中（去重）
    for (subcat,) in existing_subcategories:
        if subcat:
            category_set.add(subcat.strip())
    
    # 3. 合并预置分类（从 PRESET_CATEGORIES）
    for main_cat, sub_cats in PRESET_CATEGORIES.items():
        for sub_cat in sub_cats:
            category_set.add(sub_cat)
    
    # 转换为排序列表
    result = sorted(list(category_set))
    
    response = jsonify({"categories": result})
    # 添加 no-cache 头部，确保每次获取最新数据
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route("/api/tags", methods=["GET"])
def get_tags():
    """获取所有三级标签
    返回：系统预置标签 + notes 表中已存在的所有标签（从 tags_json 字段解析，DISTINCT）
    强制从数据库查询最新数据，禁止缓存
    """
    # 1. 从预置标签开始
    tag_set = set(PRESET_TAGS)
    
    # 2. 从 notes 表的 tags_json 字段解析并 DISTINCT 查询所有已存在的标签
    # 强制从数据库查询最新数据，不使用任何缓存
    notes_with_tags = db.session.query(Note).filter(
        Note.tags_json.isnot(None),
        Note.tags_json != ""
    ).all()
    
    for note in notes_with_tags:
        tags_list = note.get_tags_list()
        for tag in tags_list:
            if tag and tag.strip():
                tag_set.add(tag.strip())
    
    # 转换为排序列表
    result = sorted(list(tag_set))
    
    response = jsonify({"tags": result})
    # 添加 no-cache 头部，确保每次获取最新数据
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route("/api/search", methods=["GET"])
def search_notes():
    """搜索API：长文 Note + 随心记 Memo 双轨制搜索

    返回结构：
    {
        "articles": [...],  # 长文结果
        "memos": [...],     # 随心记结果
    }
    """
    search_query = request.args.get("q", "").strip()
    
    if not search_query:
        return jsonify({"articles": [], "memos": []})
    
    # 1）长文搜索：标题、内容、标签
    article_query = Note.query.filter(
        db.or_(
            Note.title.like(f'%{search_query}%'),
            Note.content.like(f'%{search_query}%'),
            Note.tags.like(f'%{search_query}%'),
            Note.tags_json.like(f'%{search_query}%')
        )
    ).order_by(Note.created_at.desc())
    
    notes = article_query.all()
    article_results = []
    
    for note in notes:
        # 提取匹配的片段
        snippets = []
        
        # 检查标题匹配
        if search_query.lower() in note.title.lower():
            snippets.append({
                "text": note.title,
                "type": "title"
            })
        
        # 检查内容匹配
        if note.content:
            content_lower = note.content.lower()
            query_lower = search_query.lower()
            
            # 找到所有匹配位置
            start_pos = 0
            while True:
                pos = content_lower.find(query_lower, start_pos)
                if pos == -1:
                    break
                
                # 提取前后50字的上下文
                context_start = max(0, pos - 50)
                context_end = min(len(note.content), pos + len(search_query) + 50)
                snippet_text = note.content[context_start:context_end]
                
                # 如果不在开头，添加省略号
                if context_start > 0:
                    snippet_text = "..." + snippet_text
                if context_end < len(note.content):
                    snippet_text = snippet_text + "..."
                
                snippets.append({
                    "text": snippet_text,
                    "type": "content",
                    "position": pos
                })
                
                start_pos = pos + 1
        
        # 如果没有找到匹配片段，使用标题和内容开头
        if not snippets:
            content_preview = note.content[:100] + "..." if note.content and len(note.content) > 100 else (note.content or "")
            snippets.append({
                "text": note.title + (f" - {content_preview}" if content_preview else ""),
                "type": "preview"
            })
        
        # 使用第一个匹配的片段，优先使用内容匹配
        content_snippets = [s for s in snippets if s.get("type") == "content"]
        if content_snippets:
            snippet = content_snippets[0]["text"]
        else:
            snippet = snippets[0]["text"] if snippets else note.title
        
        article_results.append({
            "note_id": note.id,
            "title": note.title,
            "snippet": snippet,
            "mainCategory": note.mainCategory,
            "subCategory": note.subCategory,
            "date": note.created_at.strftime("%Y年%m月%d日")
        })
    
    # 2）随心记搜索：正文与标签
    memo_query = Memo.query.filter(
        db.or_(
            Memo.content.like(f"%{search_query}%"),
            Memo.tags.like(f"%{search_query}%"),
        )
    ).order_by(Memo.created_at.desc())

    memos = memo_query.all()
    memo_results = []
    for memo in memos:
        content = memo.content or ""
        content_lower = content.lower()
        query_lower = search_query.lower()

        snippet = content[:120] + ("..." if len(content) > 120 else "")
        pos = content_lower.find(query_lower)
        if pos != -1:
            start = max(0, pos - 40)
            end = min(len(content), pos + len(search_query) + 40)
            snippet = content[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(content):
                snippet = snippet + "..."

        # 标签拆分
        tags_list = []
        if memo.tags:
            tags_list = [t for t in (s.strip() for s in memo.tags.split(",")) if t]

        memo_results.append(
            {
                "id": memo.id,
                "content": memo.content,
                "snippet": snippet,
                "tags": tags_list,
                "date": memo.created_at.strftime("%Y年%m月%d日")
                if memo.created_at
                else "",
            }
        )

    return jsonify({"articles": article_results, "memos": memo_results})


@app.route("/api/format_markdown", methods=["POST"])
def api_format_markdown():
    """
    在线格式整理 API：
    - 仅对传入的 Markdown 文本执行 auto_structure_speech_markdown + deep_clean_content
    - 不做数据库写入，只返回整理后的内容，供前端在编辑页原地替换
    """
    data = request.get_json(silent=True) or {}
    raw_content = data.get("content", "")

    try:
        structured_raw = auto_structure_speech_markdown(raw_content)
        cleaned = deep_clean_content(structured_raw)
    except Exception as e:
        return jsonify(
            {
                "success": False,
                "message": f"格式整理失败: {str(e)}",
            }
        ), 500

    return jsonify(
        {
            "success": True,
            "content": cleaned,
        }
    )


@app.route("/api/scrape", methods=["POST"])
def api_scrape():
    """
    API：素材智能抓取

    请求体（JSON 或表单）：
        { "url": "https://mp.weixin.qq.com/..." }

    返回：
        {
            "status": "success" / "error",
            "message": "...",
            "title": "...",
            "content": "..."
        }
    """
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or request.form.get("url") or "").strip()

    if not url:
        return jsonify(
            {
                "status": "error",
                "message": "请输入要抓取的链接",
            }
        ), 400

    try:
        result = scrape_manager.fetch(url)
        # 开发调试：在终端打印抓取结果，方便排查“没有正文”等问题
        if result is not None:
            try:
                print("\n==== [SCRAPE DEBUG] 抓取结果 ====")
                print(f"URL: {url}")
                print(f"标题: {result.title!r}")
                print(f"正文长度: {len(result.content) if result.content is not None else 0}")
                # 只打印前 800 字，避免终端刷屏
                preview = (result.content or "")[:800]
                print("正文预览:")
                print(preview)
                print("==== [SCRAPE DEBUG END] ====\n")
            except Exception as _e:
                # 调试日志失败不影响接口返回
                print(f"[SCRAPE DEBUG] 打印结果时出错: {_e}")
    except Exception as e:
        # 捕获任何底层异常，统一返回友好提示
        return jsonify(
            {
                "status": "error",
                "message": f"抓取失败：{str(e)}",
            }
        ), 500

    if not result:
        return jsonify(
            {
                "status": "error",
                "message": "当前暂不支持该链接来源，请确认是否为公众号文章",
            }
        ), 400

    return jsonify(
        {
            "status": "success",
            "title": result.title,
            "content": result.content,
        }
    )

@app.route("/api/memos", methods=["GET", "POST"])
def api_memos():
    """随心记 API：
    - POST /api/memos  新建一条随心记
    - GET  /api/memos  获取按时间倒序排列的列表
    """
    if request.method == "POST":
        # 支持 JSON 与表单两种提交方式
        data = request.get_json(silent=True) or {}
        content = (data.get("content") or request.form.get("content") or "").strip()
        if not content:
            return jsonify({"success": False, "message": "内容不能为空"}), 400

        memo = Memo(content=content)
        tags = memo.extract_tags()
        if tags:
            memo.tags = ",".join(tags)

        db.session.add(memo)
        db.session.commit()

        return jsonify({"success": True, "memo": memo.to_dict()}), 201

    # GET：列表
    # - 置顶优先（按 pinned_at 倒序）
    # - 其余按创建时间倒序
    memos = (
        Memo.query.order_by(
            Memo.is_pinned.desc(),
            Memo.pinned_at.desc(),
            Memo.created_at.desc(),
            Memo.id.desc(),
        )
        .limit(200)
        .all()
    )
    return jsonify({"memos": [m.to_dict() for m in memos]})


@app.route("/api/memos/<int:memo_id>/pin", methods=["PUT"])
def api_memo_pin(memo_id: int):
    """随心记：置顶/取消置顶"""
    memo = Memo.query.get_or_404(memo_id)
    data = request.get_json(silent=True) or {}
    pinned = data.get("pinned", None)

    # pinned 未传则执行 toggle
    if pinned is None:
        pinned = not bool(memo.is_pinned)
    else:
        pinned = bool(pinned)

    memo.is_pinned = pinned
    memo.pinned_at = datetime.utcnow() if pinned else None
    db.session.commit()
    return jsonify({"success": True, "memo": memo.to_dict()}), 200


@app.route("/api/memos/<int:memo_id>/star", methods=["PUT"])
def api_memo_star(memo_id: int):
    """随心记：星标/取消星标"""
    memo = Memo.query.get_or_404(memo_id)
    data = request.get_json(silent=True) or {}
    starred = data.get("starred", None)

    # starred 未传则执行 toggle
    if starred is None:
        starred = not bool(memo.is_starred)
    else:
        starred = bool(starred)

    memo.is_starred = starred
    memo.starred_at = datetime.utcnow() if starred else None
    db.session.commit()
    return jsonify({"success": True, "memo": memo.to_dict()}), 200


@app.route("/api/memos/<int:memo_id>", methods=["PUT", "DELETE"])
def api_memo_detail(memo_id: int):
    """随心记单条记录 API：
    - PUT    /api/memos/<id>  修改内容并重新提取标签
    - DELETE /api/memos/<id>  删除该随心记
    """
    memo = Memo.query.get_or_404(memo_id)

    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        content = (data.get("content") or "").strip()
        if not content:
            return jsonify({"success": False, "message": "内容不能为空"}), 400

        memo.content = content
        tags = memo.extract_tags()
        memo.tags = ",".join(tags) if tags else None
        db.session.commit()

        return jsonify({"success": True, "memo": memo.to_dict()}), 200

    # DELETE
    db.session.delete(memo)
    db.session.commit()
    return jsonify({"success": True, "message": "随心记已删除"}), 200


@app.route("/guide")
def guide():
    """功能指南页面：展示所有功能点的交互式演示"""
    return render_template("guide.html")


@app.route("/search")
def search_page():
    """全量搜索结果页：长文 + 随心记 双 Tab 展示"""
    q = request.args.get("q", "").strip()
    return render_template("search.html", q=q)


@app.route("/favicon.ico")
def favicon():
    """
    兼容浏览器默认请求 /favicon.ico：
    - 不再因为缺失 favicon 造成 404/日志噪音（更不会被误判成 500）
    """
    resp = make_response("", 204)
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


# 简单的图片上传配置与工具函数
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_image(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


@app.route("/api/upload_image", methods=["POST"])
def upload_image():
    """
    通用编辑器图片“即粘即传”接口（长文 Note 使用）：
    - 接收前端粘贴的图片文件（field 名称为 image）
    - 保存到 /static/uploads/ 目录下
    - 返回可直接用于 Markdown 的访问 URL
    """
    if "image" not in request.files:
        return jsonify({"success": False, "message": "未收到图片文件"}), 400

    file = request.files["image"]

    if not file or file.filename == "":
        return jsonify({"success": False, "message": "文件名为空"}), 400

    if not allowed_image(file.filename):
        return jsonify({"success": False, "message": "不支持的图片格式"}), 400

    # 生成安全文件名 + 随机前缀，避免覆盖
    original_name = secure_filename(file.filename)
    ext = original_name.rsplit(".", 1)[1].lower()
    random_name = f"{uuid4().hex}.{ext}"

    upload_dir = os.path.join(app.root_path, "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    save_path = os.path.join(upload_dir, random_name)
    file.save(save_path)

    # 生成可访问的 URL（供 Markdown 使用）
    file_url = url_for("static", filename=f"uploads/{random_name}")

    return jsonify(
        {
            "success": True,
            "url": file_url,
            "filename": random_name,
        }
    )


@app.route("/api/memo/upload_image", methods=["POST"])
def memo_upload_image():
    """
    随心记 Memo 专用图片上传接口：
    - 支持剪贴板粘贴、拖拽上传图片
    - 图片保存到 /static/uploads/memos/ 目录
    - 如安装 Pillow，则自动将宽度压缩到不超过 1200px（等比例缩放）
    - 返回可直接用于 Markdown 的访问 URL
    """
    if "image" not in request.files:
        return jsonify({"success": False, "message": "未收到图片文件"}), 400

    file = request.files["image"]

    if not file or file.filename == "":
        return jsonify({"success": False, "message": "文件名为空"}), 400

    if not allowed_image(file.filename):
        return jsonify({"success": False, "message": "不支持的图片格式"}), 400

    # 生成安全文件名 + 随机前缀，避免覆盖
    original_name = secure_filename(file.filename)
    ext = original_name.rsplit(".", 1)[1].lower()
    random_name = f"{uuid4().hex}.{ext}"

    upload_dir = os.path.join(app.root_path, "static", "uploads", "memos")
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, random_name)

    # 如果安装了 Pillow，则先用 Pillow 进行等比例缩放后再保存
    if Image is not None:
        try:
            # 直接从上传流读取图片
            img = Image.open(file.stream)
            img = img.convert("RGB") if img.mode in ("P", "RGBA") else img

            max_width = 1200
            if img.width > max_width:
                # 等比例缩放
                new_height = int(img.height * max_width / img.width)
                img = img.resize((max_width, new_height), Image.LANCZOS)

            img.save(save_path, quality=85, optimize=True)
        except Exception as e:
            # 如果压缩失败，为了不影响使用，退回到原始文件保存逻辑
            try:
                file.stream.seek(0)
            except Exception:
                pass
            file.save(save_path)
    else:
        # 未安装 Pillow，直接保存原图
        file.save(save_path)

    file_url = url_for("static", filename=f"uploads/memos/{random_name}")

    return jsonify(
        {
            "success": True,
            "url": file_url,
            "filename": random_name,
        }
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        ensure_schema()
    # 生产环境配置：关闭 debug 模式，限制线程和进程数以节省资源
    # 针对 2核2G 服务器，使用单线程模式避免资源竞争
    app.run(
        debug=False,  # 生产环境关闭 debug，配合全局 errorhandler 写入 error.log
        host="0.0.0.0",
        port=5000,
        threaded=True,  # 启用多线程（Flask 默认）
        processes=1  # 单进程模式，避免多进程占用过多内存
    )


