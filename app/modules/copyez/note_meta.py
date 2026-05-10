"""
Note annotation and detail API module.

APIs for reading/writing note annotations, metadata, and global thought (deep thinking).
"""

from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models.note import Note
from app.utils.content_utils import render_content
from app.utils.datetime_utils import now_bj

note_meta_bp = Blueprint("note_meta", __name__)


@note_meta_bp.route("/api/note/<int:note_id>/annotations", methods=["GET", "POST"])
def note_annotations(note_id: int):
    """API：获取或保存笔记的批注数据"""
    note = Note.query.get_or_404(note_id)

    if request.method == "POST":
        data = request.get_json()
        annotations_json = __import__('json').dumps(data.get("annotations", []), ensure_ascii=False)
        note.annotations = annotations_json
        db.session.commit()
        response = jsonify({"success": True})
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    if note.annotations:
        try:
            annotations = __import__('json').loads(note.annotations)
        except Exception:
            annotations = []
    else:
        annotations = []

    response = jsonify({"annotations": annotations})
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@note_meta_bp.route("/api/note/<int:note_id>/detail", methods=["GET"])
def get_note_detail(note_id: int):
    """API：获取笔记详情（JSON格式），强制从数据库读取最新数据"""
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

    response = jsonify({
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "content_html": content_html,
        "toc_html": toc_html,
        "mainCategory": note.mainCategory,
        "subCategory": note.subCategory,
        "tags_list": note.get_tags_list(),
        "publishDate": note.publishDate,
        "sourceUrl": note.sourceUrl,
        "created_at": note.created_at.isoformat() if note.created_at else None,
        "updated_at": note.updated_at.isoformat() if note.updated_at else None
    })
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@note_meta_bp.route("/api/note/<int:note_id>/global-thought", methods=["GET", "POST", "DELETE"])
def note_global_thought(note_id: int):
    """API：获取或保存笔记的深度思考内容（块状化存储）"""
    note = Note.query.get_or_404(note_id)

    if request.method == "POST":
        data = request.get_json()
        thought_data = {
            "id": data.get("id") or f"thought_{now_bj().timestamp()}_{note_id}",
            "content": data.get("content", ""),
            "created_at": data.get("created_at") or now_bj().isoformat(),
            "updated_at": now_bj().isoformat()
        }

        if note.global_thought:
            try:
                thoughts = __import__('json').loads(note.global_thought)
                if not isinstance(thoughts, list):
                    thoughts = []
            except Exception:
                thoughts = []
        else:
            thoughts = []

        existing_index = next((i for i, t in enumerate(thoughts) if t.get("id") == thought_data["id"]), None)
        if existing_index is not None:
            thoughts[existing_index] = thought_data
        else:
            thoughts.append(thought_data)

        note.global_thought = __import__('json').dumps(thoughts, ensure_ascii=False)
        db.session.commit()
        response = jsonify({"success": True, "thought": thought_data})
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    if request.method == "DELETE":
        data = request.get_json()
        thought_id = data.get("id")

        if note.global_thought and thought_id:
            try:
                thoughts = __import__('json').loads(note.global_thought)
                if isinstance(thoughts, list):
                    thoughts = [t for t in thoughts if t.get("id") != thought_id]
                    note.global_thought = __import__('json').dumps(thoughts, ensure_ascii=False) if thoughts else None
                    db.session.commit()
            except Exception:
                pass

        response = jsonify({"success": True})
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    if note.global_thought:
        try:
            thoughts = __import__('json').loads(note.global_thought)
            if not isinstance(thoughts, list):
                thoughts = []
        except Exception:
            thoughts = []
    else:
        thoughts = []

    response = jsonify({"thoughts": thoughts})
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
