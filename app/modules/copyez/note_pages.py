"""
Note page module.

Page routes for notes: list, view, create, edit.
Endpoint names are preserved to match existing templates (url_for uses bare names).
"""

import re
import random
import json
import traceback
from datetime import datetime, date, timedelta

from flask import Blueprint, request, render_template, make_response, jsonify, url_for, redirect
from sqlalchemy import func, text

from app.extensions import db
from app.models.note import Note
from app.models.category import CustomCategory
from app.utils.content_utils import (
    render_content,
    deep_clean_content, auto_structure_speech_markdown,
)
from app.utils.text_utils import estimate_text_length
from app.utils.presets import PRESET_CATEGORIES, PRESET_TAGS
from app.utils import now_bj, write_log

note_pages_bp = Blueprint("note_pages", __name__)


# ── Standalone view functions for add_url_rule (bare endpoint names) ────────────

def notes_page():
    """笔记列表页：扁平化列表，按创建日期分组展示，支持分类过滤和搜索"""
    return _notes_page_impl()


def _notes_page_impl():
    """Implementation of notes_page (called by both the wrapper and blueprint route)."""
    try:
        main_category = request.args.get("mainCategory", "").strip()
        sub_category = request.args.get("subCategory", "").strip()
        tag_filter = request.args.get("tag", "").strip()
        search_query = request.args.get("q", "").strip()
        global_search = request.args.get("global", "false").lower() == "true"

        query = Note.query

        day_str = request.args.get("day", "").strip()
        month_str = request.args.get("month", "").strip()

        if day_str:
            try:
                day_filter = datetime.strptime(day_str, "%Y-%m-%d").date()
                start_dt = datetime.combine(day_filter, datetime.min.time())
                end_dt = datetime.combine(day_filter, datetime.max.time())
                query = query.filter(Note.created_at >= start_dt, Note.created_at <= end_dt)
            except Exception:
                pass

        if month_str and not day_str:
            try:
                ym = datetime.strptime(month_str, "%Y-%m")
                month_filter_start = datetime(ym.year, ym.month, 1)
                if ym.month == 12:
                    month_filter_end = datetime(ym.year + 1, 1, 1)
                else:
                    month_filter_end = datetime(ym.year, ym.month + 1, 1)
                query = query.filter(Note.created_at >= month_filter_start, Note.created_at < month_filter_end)
            except Exception:
                month_str = ""

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

        if search_query:
            if not global_search and sub_category:
                query = query.filter(
                    db.or_(
                        Note.title.like(f'%{search_query}%'),
                        Note.content.like(f'%{search_query}%')
                    )
                )
            else:
                query = query.filter(
                    db.or_(
                        Note.title.like(f'%{search_query}%'),
                        Note.content.like(f'%{search_query}%'),
                        Note.tags.like(f'%{search_query}%'),
                        Note.tags_json.like(f'%{search_query}%')
                    )
                )

        def _collection_sort_key(n):
            if getattr(n, "publishDate", None):
                try:
                    pd = datetime.strptime(n.publishDate, "%Y-%m-%d")
                    return (0, pd, n.created_at or datetime.min, n.id)
                except Exception:
                    pass
            return (1, n.created_at or datetime.min, n.id)

        tag_collection_notes = []
        grouped_list = []

        if tag_filter:
            notes = query.all()
            notes.sort(key=_collection_sort_key)
            tag_collection_notes = notes
        else:
            notes = query.order_by(Note.created_at.desc()).all()
            grouped_notes = {}
            for note in notes:
                date_key = note.created_at.date()
                if date_key not in grouped_notes:
                    grouped_notes[date_key] = []
                grouped_notes[date_key].append(note)
            grouped_list = sorted(grouped_notes.items(), key=lambda x: x[0], reverse=True)

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
            all_tags.update(note.get_tags_list())

        main_categories = sorted(main_categories)
        for key in sub_categories:
            sub_categories[key] = sorted(sub_categories[key])
        all_tags = sorted(all_tags)

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
                daily_quote = re.sub(r"<[^>]+>", "", daily_quote).strip()
                if len(daily_quote) > 100:
                    daily_quote = daily_quote[:100] + "..."
        except Exception:
            daily_quote = None

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
            timeline_archives.append({
                "ym": ym_val,
                "year": year_int,
                "month": month_int,
                "count": int(cnt or 0),
            })

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
        try:
            write_log("notes_error.log",
                f"\n===== /notes Exception at {now_bj().isoformat()} =====\n"
                f"Type: {type(e)}\nDetail: {repr(e)}\n{traceback.format_exc()}\n"
            )
        except Exception:
            pass
        raise


# ── Blueprint routes (with blueprint prefix) ───────────────────────────────────────

# NOTE: /notes is registered as a standalone route via add_url_rule (in app.py)
# for backward compatibility with templates using url_for('notes').
# Other routes below use the blueprint prefix (note_pages.xxx).



# ── /note/<id> ────────────────────────────────────────────────────────────────

@note_pages_bp.route("/note/<int:note_id>", endpoint="view_note")
def view_note_page(note_id: int):
    """阅读页：按照公文 A4 版式展示内容"""
    current_tag = request.args.get("tag", "").strip() or None

    try:
        existing_note = db.session.get(Note, note_id)
        if existing_note:
            db.session.expire(existing_note)
    except Exception:
        pass

    note = db.session.query(Note).filter_by(id=note_id).first_or_404()
    db.session.expire(note)
    db.session.refresh(note)

    content_html, toc_html = render_content(note.content, return_toc=True)
    word_count = estimate_text_length(note.content or "")

    nav_prev = None
    nav_next = None

    def _collection_sort_key(n):
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
            notes = Note.query.order_by(Note.created_at.desc(), Note.id.desc()).all()

        if notes:
            idx = next((i for i, n in enumerate(notes) if n.id == note_id), None)
            if idx is not None:
                if idx > 0:
                    nav_prev = notes[idx - 1]
                if idx < len(notes) - 1:
                    nav_next = notes[idx + 1]
    except Exception:
        nav_prev = None
        nav_next = None

    try:
        print(f"\n====== DEBUG NOTE {note_id} CONTENT START ======")
        print(f"[DB Content] 前500字符: {note.content[:500]}")
        print(f"[Rendered HTML] 前500字符: {str(content_html)[:500]}")
        print(f"======= DEBUG NOTE {note_id} CONTENT END =======\n")
    except Exception as e:
        print(f"[WARN] Failed to print content for note {note_id}: {e}")

    try:
        print("\n====== DEBUG TOC_HTML START ======")
        if toc_html:
            preview = toc_html[:2000]
            print(preview)
            if len(toc_html) > 2000:
                print(f"... (total length: {len(toc_html)} chars, only preview above)")
        else:
            print("toc_html is EMPTY or None")
        print("======= DEBUG TOC_HTML END =======\n")
    except Exception as e:
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
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


# ── /new ─────────────────────────────────────────────────────────────────────

@note_pages_bp.route("/new", methods=["GET", "POST"], endpoint="new_note")
def new_note_page():
    """新建素材页面"""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        mainCategory = request.form.get("mainCategory", "").strip() or None
        subCategory = request.form.get("subCategory", "").strip() or None
        tags_input = request.form.get("tags", "").strip()
        tags_json_input = request.form.get("tags_json", "").strip()
        publishDate = request.form.get("publishDate", "").strip() or None
        sourceUrl = request.form.get("sourceUrl", "").strip() or None
        raw_content = request.form.get("content", "")

        structured_raw = auto_structure_speech_markdown(raw_content)
        content = deep_clean_content(structured_raw)

        if not title or not content.strip():
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": False, "message": "标题和内容不能为空"}), 400

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

        tags_list = []
        if tags_json_input:
            try:
                tags_list = json.loads(tags_json_input)
            except Exception:
                tags_list = [tag.strip() for tag in tags_json_input.split(",") if tag.strip()]

        if subCategory:
            existing = CustomCategory.query.filter_by(name=subCategory).first()
            if not existing:
                new_category = CustomCategory(name=subCategory, main_category=mainCategory)
                db.session.add(new_category)

        note = Note(
            title=title,
            tags=tags_input,
            content=content,
            mainCategory=mainCategory,
            subCategory=subCategory,
            publishDate=publishDate,
            sourceUrl=sourceUrl,
        )
        note.set_tags_list(tags_list)

        db.session.add(note)
        db.session.commit()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({
                "success": True,
                "message": "创建成功",
                "note_id": note.id,
                "redirect_url": url_for("view_note", note_id=note.id),
            }), 200

        return redirect(url_for("view_note", note_id=note.id))

    all_categories = CustomCategory.query.order_by(CustomCategory.name).all()
    categories_by_main = {}
    for cat in all_categories:
        main = cat.main_category or "其他"
        if main not in categories_by_main:
            categories_by_main[main] = []
        categories_by_main[main].append(cat.name)

    today_str = now_bj().strftime("%Y-%m-%d")

    return render_template(
        "new.html",
        preset_categories=PRESET_CATEGORIES,
        categories_by_main=categories_by_main,
        preset_tags=PRESET_TAGS,
        current_date=today_str,
        mainCategory="全文",
    )


# ── /add (alias of /new) ────────────────────────────────────────────────────

@note_pages_bp.route("/add", methods=["GET", "POST"], endpoint="add_note")
def add_note_page():
    return new_note_page()


# ── /edit/<id> ──────────────────────────────────────────────────────────────

@note_pages_bp.route("/edit/<int:note_id>", methods=["GET", "POST"], endpoint="edit_note")
def edit_note_page(note_id: int):
    """二次加工 / 修改已有素材"""
    note = Note.query.get_or_404(note_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        mainCategory = request.form.get("mainCategory", "").strip() or None
        subCategory = request.form.get("subCategory", "").strip() or None
        tags = request.form.get("tags", "").strip()
        tags_json_input = request.form.get("tags_json", "").strip()
        publishDate = request.form.get("publishDate", "").strip() or None
        sourceUrl = request.form.get("sourceUrl", "").strip() or None
        raw_content = request.form.get("content", "")

        structured_raw = auto_structure_speech_markdown(raw_content)
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

        tags_list = []
        if tags_json_input:
            try:
                tags_list = json.loads(tags_json_input)
            except Exception:
                tags_list = [tag.strip() for tag in tags_json_input.split(",") if tag.strip()]

        if subCategory:
            existing = CustomCategory.query.filter_by(name=subCategory).first()
            if not existing:
                new_category = CustomCategory(name=subCategory, main_category=mainCategory)
                db.session.add(new_category)

        note.title = title
        note.tags = tags
        note.content = content
        note.mainCategory = mainCategory
        note.subCategory = subCategory
        note.publishDate = publishDate
        note.sourceUrl = sourceUrl
        note.set_tags_list(tags_list)
        note.updated_at = now_bj()

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"success": False, "message": f"数据库写入失败: {str(e)}"}), 500
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

        db.session.expire(note)
        db.session.refresh(note)

        verify_note = db.session.query(Note).filter_by(id=note.id).first()
        if not verify_note or verify_note.content != content:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"success": False, "message": "数据验证失败，请重试"}), 500
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

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "success": True,
                "message": "保存成功",
                "note_id": note.id,
                "redirect_url": url_for("view_note", note_id=note.id)
            }), 200

        return redirect(url_for("view_note", note_id=note.id))

    tags_list = note.get_tags_list()

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
