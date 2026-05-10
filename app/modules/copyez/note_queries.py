"""
Note query API module.

Read-only query APIs for notes: pagination list, full-text search.
"""

from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models.note import Note
from app.models.memo import Memo

note_queries_bp = Blueprint("note_queries", __name__)


@note_queries_bp.route("/api/notes", methods=["GET"])
def get_notes():
    """分页获取笔记列表API

    参数：
    - limit: 每页数量，默认20
    - offset: 跳过数量，默认0
    - mainCategory: 一级分类过滤
    - subCategory: 二级分类过滤
    - tag: 标签过滤
    - day: 日期过滤 (YYYY-MM-DD)
    - month: 月份过滤 (YYYY-MM)

    返回：
    {
        "notes": [...],      # 笔记列表
        "hasMore": true/false,  # 是否还有更多
        "total": 100,       # 总数
        "offset": 20         # 当前偏移量
    }
    """
    try:
        limit = request.args.get("limit", 20, type=int)
        offset = request.args.get("offset", 0, type=int)
        limit = min(limit, 100)

        main_category = request.args.get("mainCategory", "").strip()
        sub_category = request.args.get("subCategory", "").strip()
        tag_filter = request.args.get("tag", "").strip()
        day_str = request.args.get("day", "").strip()
        month_str = request.args.get("month", "").strip()

        query = Note.query

        if day_str:
            try:
                from datetime import datetime as dt, date as d
                day_filter = dt.strptime(day_str, "%Y-%m-%d").date()
                start_dt = dt.combine(day_filter, dt.min.time())
                end_dt = dt.combine(day_filter, dt.max.time())
                query = query.filter(Note.created_at >= start_dt, Note.created_at <= end_dt)
            except Exception:
                pass

        if month_str:
            try:
                from datetime import datetime as dt
                ym = dt.strptime(month_str, "%Y-%m")
                month_filter_start = dt(ym.year, ym.month, 1)
                if ym.month == 12:
                    month_filter_end = dt(ym.year + 1, 1, 1)
                else:
                    month_filter_end = dt(ym.year, ym.month + 1, 1)
                query = query.filter(Note.created_at >= month_filter_start, Note.created_at < month_filter_end)
            except Exception:
                pass

        if main_category:
            query = query.filter(Note.mainCategory == main_category)

        if sub_category:
            query = query.filter(Note.subCategory == sub_category)

        if tag_filter:
            tag_filter_clean = tag_filter.strip()
            query = query.filter(
                db.or_(
                    Note.subCategory == tag_filter_clean,
                    Note.subCategory.like(f'%{tag_filter_clean}%'),
                    Note.tags_json.like(f'%"{tag_filter_clean}"%'),
                    Note.tags_json.like(f'%{tag_filter_clean}%')
                )
            )

        total = query.count()
        notes = query.order_by(Note.created_at.desc()).offset(offset).limit(limit).all()

        notes_data = []
        for note in notes:
            tags_list = note.get_tags_list()
            notes_data.append({
                "id": note.id,
                "title": note.title,
                "created_at": note.created_at.strftime("%Y-%m-%d %H:%M"),
                "mainCategory": note.mainCategory,
                "subCategory": note.subCategory,
                "tags": tags_list
            })

        has_more = (offset + len(notes_data)) < total

        response = jsonify({
            "notes": notes_data,
            "hasMore": has_more,
            "total": total,
            "offset": offset + len(notes_data)
        })
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@note_queries_bp.route("/api/search", methods=["GET"])
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
        snippets = []

        if search_query.lower() in note.title.lower():
            snippets.append({
                "text": note.title,
                "type": "title"
            })

        if note.content:
            content_lower = note.content.lower()
            query_lower = search_query.lower()

            start_pos = 0
            while True:
                pos = content_lower.find(query_lower, start_pos)
                if pos == -1:
                    break

                context_start = max(0, pos - 50)
                context_end = min(len(note.content), pos + len(search_query) + 50)
                snippet_text = note.content[context_start:context_end]

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

        if not snippets:
            content_preview = note.content[:100] + "..." if note.content and len(note.content) > 100 else (note.content or "")
            snippets.append({
                "text": note.title + (f" - {content_preview}" if content_preview else ""),
                "type": "preview"
            })

        content_snippets = [s for s in snippets if s.get("type") == "content"]
        if content_snippets:
            snippet = content_snippets[0]["text"]
        else:
            snippet = snippets[0]["text"] if snippets else note.title

        tags_list = note.get_tags_list()

        article_results.append({
            "note_id": note.id,
            "title": note.title,
            "snippet": snippet,
            "mainCategory": note.mainCategory,
            "subCategory": note.subCategory,
            "tags": tags_list,
            "date": note.created_at.strftime("%Y年%m月%d日")
        })

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
