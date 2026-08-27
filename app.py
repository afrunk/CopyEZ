from datetime import datetime, timedelta, date, timezone, tzinfo
import os
import re
import traceback
import random
import base64
from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
from sqlalchemy import inspect, text, distinct, func
from markupsafe import Markup
import json
import markdown
import bleach

# ── 北京时间（UTC+8）工具函数 ──────────────────────────────────────────────
from app.utils.datetime_utils import now_bj, BJ_TZ

from werkzeug.utils import secure_filename
from uuid import uuid4
from werkzeug.exceptions import HTTPException
from urllib.parse import quote
from app.utils.scraper.manager import scrape_manager
from app.modules.copyez.upload_utils import allowed_image
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

# 从 config.py 加载配置
from config import Config
app.config.from_object(Config)

# 从 app/extensions.py 导入统一的 db 实例
from app.extensions import db
db.init_app(app)

# 从 app/models 导入模型类
from app.models import Note, Memo, CustomCategory
from app.models.wechat import WeChatUser, WeChatMessage  # noqa: F401

# 从 app/routes 导入已迁移的路由和 Blueprint
from app.routes import portal_index, guide_page, orc_documents_page, ledger_bp, search_page
from app.modules.ledger.api import ledger_api_bp
# 从 note_pages 单独导入 standalone 函数用于 add_url_rule
from app.modules.copyez.note_pages import notes_page

# 从 app/modules/copyez 导入已迁移的 Memo API
from app.modules.copyez import (
    api_memos, api_memo_pin, api_memo_star, api_memo_detail, memo_upload_image,
    get_categories, get_tags,
    api_activity_stats, api_tag_collection,
    api_format_markdown,
    upload_image,
    collect_quote_items,
    memos_bp,
    quotes_bp,
    scrape_bp,
    note_api_bp,
    note_queries_bp,
    note_meta_bp,
    note_relations_bp,
    note_pages_bp,
)
from app.modules.renovamate import renovamate_bp

# ── 路由注册区 ──────────────────────────────────────────────────────────────
# 低风险页面路由（通过 add_url_rule 保持原 endpoint 不变）
app.add_url_rule("/", endpoint="index", view_func=portal_index)
app.add_url_rule("/guide", endpoint="guide", view_func=guide_page)
app.add_url_rule("/ORC_documents", endpoint="orc_documents", view_func=orc_documents_page)
app.add_url_rule("/search", endpoint="search_page", view_func=search_page)

# Memo API（随心记）
app.add_url_rule("/api/memos", endpoint="api_memos", view_func=api_memos, methods=["GET", "POST"])
app.add_url_rule("/api/memos/<int:memo_id>/pin", endpoint="api_memo_pin", view_func=api_memo_pin, methods=["PUT"])
app.add_url_rule("/api/memos/<int:memo_id>/star", endpoint="api_memo_star", view_func=api_memo_star, methods=["PUT"])
app.add_url_rule("/api/memos/<int:memo_id>", endpoint="api_memo_detail", view_func=api_memo_detail, methods=["PUT", "DELETE"])
app.add_url_rule("/api/memo/upload_image", endpoint="memo_upload_image", view_func=memo_upload_image, methods=["POST"])

# Category / Tags API
app.add_url_rule("/api/categories", endpoint="get_categories", view_func=get_categories, methods=["GET"])
app.add_url_rule("/api/tags", endpoint="get_tags", view_func=get_tags, methods=["GET"])

# Dashboard / Activity Stats API
app.add_url_rule("/api/activity_stats", endpoint="api_activity_stats", view_func=api_activity_stats, methods=["GET"])
app.add_url_rule("/api/tag_collection", endpoint="api_tag_collection", view_func=api_tag_collection, methods=["GET"])

# Formatting API
app.add_url_rule("/api/format_markdown", endpoint="api_format_markdown", view_func=api_format_markdown, methods=["POST"])

# Upload API
app.add_url_rule("/api/upload_image", endpoint="upload_image", view_func=upload_image, methods=["POST"])

# Decoration Image Upload API (装修手册专用)
@app.route("/decoration/api/upload/image", methods=["POST"])
def decoration_upload_image():
    """
    装修手册图片上传接口
    """
    from flask import current_app
    from app.utils.presets import ALLOWED_IMAGE_EXTENSIONS
    from uuid import uuid4

    if "image" not in request.files:
        return jsonify({"success": False, "message": "未收到图片文件"}), 400

    file = request.files["image"]

    if not file or file.filename == "":
        return jsonify({"success": False, "message": "文件名为空"}), 400

    # 从原始文件名提取扩展名（避免 secure_filename 在 Windows 下丢失扩展名）
    original_filename = file.filename
    ext = ""
    if "." in original_filename:
        ext = original_filename.rsplit(".", 1)[1].lower()
    
    if not ext or ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"success": False, "message": f"不支持的图片格式，支持: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"}), 400

    random_name = f"{uuid4().hex}.{ext}"
    upload_dir = os.path.join(current_app.root_path, "static", "uploads", "decoration")
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, random_name)
    file.save(save_path)

    file_url = url_for("static", filename=f"uploads/decoration/{random_name}")
    return jsonify({"success": True, "url": file_url, "filename": random_name})

# LedgerEZ Blueprint
from app.modules.ledger.auth import auth_bp
app.register_blueprint(ledger_bp)
app.register_blueprint(ledger_api_bp)
app.register_blueprint(auth_bp)

# Memos Blueprint
app.register_blueprint(memos_bp)

# Quotes Blueprint
app.register_blueprint(quotes_bp)

# Scrape Blueprint
app.register_blueprint(scrape_bp)

# Note API Blueprint
app.register_blueprint(note_api_bp)

# Note Queries Blueprint
app.register_blueprint(note_queries_bp)

# Note Meta Blueprint
app.register_blueprint(note_meta_bp)

# Note Relations Blueprint
app.register_blueprint(note_relations_bp)

# Note Pages Blueprint
# 注册 /notes 为 standalone（bare endpoint name，供 templates 的 url_for 使用）
app.add_url_rule("/notes", endpoint="notes", view_func=notes_page)
app.register_blueprint(note_pages_bp)

# RenovaMate Blueprint
app.register_blueprint(renovamate_bp)

# BondageDiary Blueprint (Phase 7)
from app.modules.bondage_diary import (
    diary_auth_bp,
    diary_entries_bp,
    diary_comments_bp,
    diary_access_bp,
    diary_upload_bp,
    diary_pages_bp,
    diary_dashboard_bp,
    diary_notifications_bp,
)
app.register_blueprint(diary_auth_bp)
app.register_blueprint(diary_entries_bp)
app.register_blueprint(diary_comments_bp)
app.register_blueprint(diary_access_bp)
app.register_blueprint(diary_upload_bp)
app.register_blueprint(diary_pages_bp)
app.register_blueprint(diary_dashboard_bp)
app.register_blueprint(diary_notifications_bp)

# WeChat Blueprint (私密聊天)
from app.modules.wechat import wechat_auth_bp, wechat_chat_bp, wechat_upload_bp, avatar_bp, wechat_settings_bp, me_bp
app.register_blueprint(wechat_auth_bp)
app.register_blueprint(wechat_chat_bp)
app.register_blueprint(wechat_upload_bp)
app.register_blueprint(avatar_bp)
app.register_blueprint(wechat_settings_bp)
app.register_blueprint(me_bp)

# ── 模板过滤器 ───────────────────────────────────────────────────────────────
from app.utils.filters import register_filters, urlquote_filter
register_filters(app)

# ── 文本处理工具 ─────────────────────────────────────────────────────────────
from app.utils.text_utils import estimate_text_length
from app.utils.content_utils import (
    clean_word_formatting,
    deep_clean_content,
    auto_structure_speech_markdown,
    render_content,
    ALLOWED_HTML_TAGS,
    ALLOWED_HTML_ATTRIBUTES,
)
from app.utils.presets import PRESET_CATEGORIES, PRESET_TAGS

@app.errorhandler(Exception)
def handle_unexpected_error(e):
    """捕获所有未处理异常：页面展示 traceback，同时写日志方便服务端排查。"""
    # 重要：不要把 404/400 等 HTTP 异常强行变成 500
    if isinstance(e, HTTPException):
        return e
    # 写一份到日志（部署机用得上）
    import logging
    logging.getLogger("werkzeug").exception("Unhandled exception: %s", e)
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

    # === WeChat messages 表的自修复迁移 ===
    # 兼容老库：wechat_messages 表历史上经历过 schema 变更
    # 旧 schema: sender_id, content, message_type, created_at, is_deleted, recalled_at, read_at
    # 新 schema: + receiver_id, msg_type, image_urls, recalled, is_read
    # 旧列上 NOT NULL 约束会导致 SQLAlchemy INSERT 新 schema 时报 IntegrityError，
    # 因为模型里没有旧列，但表上旧列 NOT NULL。
    if "wechat_messages" in table_names:
        wechat_cols_raw = insp.get_columns("wechat_messages")
        wechat_col_names = {c["name"] for c in wechat_cols_raw}
        wechat_col_nullable = {c["name"]: c.get("nullable", True) for c in wechat_cols_raw}

        # 1) 添加缺失的新列
        with engine.begin() as conn:
            if "receiver_id" not in wechat_col_names:
                conn.execute(text("ALTER TABLE wechat_messages ADD COLUMN receiver_id INTEGER"))
            if "msg_type" not in wechat_col_names:
                conn.execute(text("ALTER TABLE wechat_messages ADD COLUMN msg_type VARCHAR(20)"))
            if "image_urls" not in wechat_col_names:
                conn.execute(text("ALTER TABLE wechat_messages ADD COLUMN image_urls JSON"))
            if "recalled" not in wechat_col_names:
                conn.execute(text("ALTER TABLE wechat_messages ADD COLUMN recalled BOOLEAN DEFAULT 0"))
            if "is_read" not in wechat_col_names:
                conn.execute(text("ALTER TABLE wechat_messages ADD COLUMN is_read BOOLEAN DEFAULT 0"))

        # 2) 回填历史数据（仅在缺新数据时执行，避免每次启动都跑）
        with engine.begin() as conn:
            null_msg_type = conn.execute(text(
                "SELECT COUNT(*) FROM wechat_messages WHERE msg_type IS NULL OR msg_type = ''"
            )).scalar()
            if null_msg_type and null_msg_type > 0:
                # 映射旧 message_type → 新 msg_type
                conn.execute(text("""
                    UPDATE wechat_messages
                    SET msg_type = CASE
                        WHEN message_type IN ('text', 'image') THEN message_type
                        ELSE 'text'
                    END
                    WHERE msg_type IS NULL OR msg_type = ''
                """))

                # is_read ← read_at NOT NULL
                conn.execute(text("""
                    UPDATE wechat_messages
                    SET is_read = CASE WHEN read_at IS NOT NULL THEN 1 ELSE 0 END
                    WHERE is_read = 0 OR is_read IS NULL
                """))

                # recalled ← is_deleted=1 OR recalled_at NOT NULL
                conn.execute(text("""
                    UPDATE wechat_messages
                    SET recalled = CASE
                        WHEN is_deleted = 1 OR recalled_at IS NOT NULL THEN 1
                        ELSE 0
                    END
                    WHERE recalled = 0 OR recalled IS NULL
                """))

                # receiver_id 推断：sender_id=1→2，sender_id=2→1
                conn.execute(text("""
                    UPDATE wechat_messages
                    SET receiver_id = CASE sender_id
                        WHEN 1 THEN 2
                        WHEN 2 THEN 1
                        ELSE receiver_id
                    END
                    WHERE receiver_id IS NULL
                """))

                # image_msgs 的 image_urls 从 content 反推
                conn.execute(text("""
                    UPDATE wechat_messages
                    SET image_urls = json_array(content)
                    WHERE (msg_type = 'image' OR message_type = 'image'
                           OR message_type IN ('burn_image','flash_image'))
                      AND (image_urls IS NULL OR image_urls = '' OR image_urls = '[]')
                      AND content IS NOT NULL AND content != ''
                """))

        # 3) 旧 NOT NULL 列需要放宽（SQLite 重建表方案）
        legacy_notnull_cols = []
        if "message_type" in wechat_col_names and wechat_col_nullable.get("message_type") is False:
            legacy_notnull_cols.append("message_type")
        if "is_deleted" in wechat_col_names and wechat_col_nullable.get("is_deleted") is False:
            legacy_notnull_cols.append("is_deleted")

        if legacy_notnull_cols:
            import logging
            logging.getLogger("wechat_migrate").warning(
                "[wechat_migrate] 检测到旧 NOT NULL 列 %s，正在重建表以放宽约束...",
                legacy_notnull_cols,
            )

            with engine.begin() as conn:
                all_cols_info = conn.execute(text("PRAGMA table_info(wechat_messages)")).fetchall()
                all_col_names = {row[1] for row in all_cols_info}

                # 建新表（所有列 nullable）
                conn.execute(text("""
                    CREATE TABLE wechat_messages_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender_id INTEGER,
                        receiver_id INTEGER,
                        content TEXT,
                        message_type VARCHAR(20),
                        msg_type VARCHAR(20),
                        image_urls JSON,
                        recalled BOOLEAN DEFAULT 0,
                        is_read BOOLEAN DEFAULT 0,
                        is_deleted BOOLEAN DEFAULT 0,
                        recalled_at DATETIME,
                        read_at TIMESTAMP,
                        created_at DATETIME
                    )
                """))

                target_cols = ["sender_id", "receiver_id", "content", "message_type",
                               "msg_type", "image_urls", "recalled", "is_read",
                               "is_deleted", "recalled_at", "read_at", "created_at"]
                select_parts = [
                    f'"{tc}"' if tc in all_col_names else "NULL"
                    for tc in target_cols
                ]
                conn.execute(text(f"""
                    INSERT INTO wechat_messages_new
                        (sender_id, receiver_id, content, message_type,
                         msg_type, image_urls, recalled, is_read,
                         is_deleted, recalled_at, read_at, created_at)
                    SELECT {", ".join(select_parts)}
                    FROM wechat_messages
                """))

                conn.execute(text("DROP TABLE wechat_messages"))
                conn.execute(text("ALTER TABLE wechat_messages_new RENAME TO wechat_messages"))

            logging.getLogger("wechat_migrate").warning(
                "[wechat_migrate] 表重建完成，所有历史数据已迁移。"
            )

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
        # Categories initialized via API on first use

    # 创建 decoration_projects 表（如果不存在）
    if "decoration_projects" not in insp.get_table_names():
        # 导入模型，使 SQLAlchemy 知道要创建哪些表
        from app.models.renovamate import DecorationProject  # noqa: F401
        db.create_all()

    # 创建 decoration_category_groups 表（如果不存在）
    if "decoration_category_groups" not in insp.get_table_names():
        # 导入模型，使 SQLAlchemy 知道要创建哪些表
        from app.models.renovamate import DecorationCategoryGroup  # noqa: F401
        db.create_all()

    # 创建 decoration_categories 表（如果不存在）
    if "decoration_categories" not in insp.get_table_names():
        # 导入模型，使 SQLAlchemy 知道要创建哪些表
        from app.models.renovamate import DecorationCategory  # noqa: F401
        db.create_all()
    else:
        # 迁移：添加 selected_plan_id 字段（CompareItem 方案引用）
        cat_cols = [c["name"] for c in insp.get_columns("decoration_categories")]
        if "selected_plan_id" not in cat_cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE decoration_categories ADD COLUMN selected_plan_id INTEGER"))

    # 创建 renovamate_compare_items 表（如果不存在）
    if "renovamate_compare_items" not in insp.get_table_names():
        from app.models.renovamate import CompareItem  # noqa: F401
        db.create_all()

    # 创建 renovamate_expenses 表（如果不存在）
    if "renovamate_expenses" not in insp.get_table_names():
        from app.models.renovamate import Expense  # noqa: F401
        db.create_all()

    # 创建 renovamate_progress_tasks 表（如果不存在）
    if "renovamate_progress_tasks" not in insp.get_table_names():
        from app.models.renovamate import ProgressTask  # noqa: F401
        db.create_all()

    # 创建 renovamate_notes 表（如果不存在）
    if "renovamate_notes" not in insp.get_table_names():
        from app.models.renovamate import DecorationNote  # noqa: F401
        db.create_all()

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

    # === LedgerEZ 表的自修复迁移 ===
    # 兼容老库：为 ledger_transactions 表补充 owner_id 字段
    if "ledger_transactions" in table_names:
        tx_cols = [c["name"] for c in insp.get_columns("ledger_transactions")]

        if "owner_id" not in tx_cols:
            with engine.begin() as conn:
                # 添加 owner_id 列，默认值为 1（第一个用户）
                conn.execute(text("ALTER TABLE ledger_transactions ADD COLUMN owner_id INTEGER REFERENCES ledger_users(id)"))
                # 给现有记录设置默认值
                conn.execute(text("UPDATE ledger_transactions SET owner_id = 1 WHERE owner_id IS NULL"))

        if "remark" not in tx_cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE ledger_transactions ADD COLUMN remark VARCHAR(200) DEFAULT ''"))

    # 兼容老库：为 ledger_accounts 表补充 owner_id 字段
    if "ledger_accounts" in table_names:
        acc_cols = [c["name"] for c in insp.get_columns("ledger_accounts")]

        if "owner_id" not in acc_cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE ledger_accounts ADD COLUMN owner_id INTEGER REFERENCES ledger_users(id)"))
                conn.execute(text("UPDATE ledger_accounts SET owner_id = 1 WHERE owner_id IS NULL"))

    # === BondageDiary 表的自修复迁移 ===
    # 首次启动时：依次创建 7 张表（diary_users / diary_entries / diary_images /
    #  diary_comments / diary_entry_revisions / diary_access_logs / diary_login_attempts）
    diary_tables = [
        ("diary_users", "DiaryUser"),
        ("diary_entries", "DiaryEntry"),
        ("diary_images", "DiaryImage"),
        ("diary_comments", "DiaryComment"),
        ("diary_entry_revisions", "DiaryEntryRevision"),
        ("diary_access_logs", "DiaryAccessLog"),
        ("diary_login_attempts", "DiaryLoginAttempt"),
    ]

    for table_name, model_name in diary_tables:
        if table_name not in table_names:
            # 强制导入模型，使 SQLAlchemy 知道要创建的表结构
            from app.models.bondage_diary import (
                DiaryUser,
                DiaryEntry,
                DiaryImage,
                DiaryComment,
                DiaryEntryRevision,
                DiaryAccessLog,
                DiaryLoginAttempt,
            )  # noqa: F401
            db.create_all()
            break  # create_all 一次性建完所有已注册的表，跳出循环

_schema_ensured = False

@app.before_request
def _ensure_schema_once():
    """首次请求时确保 visit_log 等表已创建（兼容 flask run 未执行 ensure_schema 的情况）"""
    global _schema_ensured
    if _schema_ensured:
        return
    try:
        ensure_schema()
        _schema_ensured = True
    except Exception:
        pass



@app.context_processor
def inject_helpers():
    # 让模板里可以直接使用 render_content
    return {"render_content": render_content}


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        ensure_schema()
    app.run(
        debug=False,
        host="0.0.0.0",
        port=5000,
        threaded=True,
        processes=1
    )