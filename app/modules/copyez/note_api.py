"""
Note API module.

CRUD and utility APIs for notes: delete, favicon.
"""

from flask import Blueprint, make_response, jsonify

from app.extensions import db
from app.models.note import Note

note_api_bp = Blueprint("note_api", __name__)


@note_api_bp.route("/api/note/<int:note_id>/delete", methods=["DELETE"])
def delete_note(note_id: int):
    """API：删除文章"""
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    return jsonify({"success": True, "message": "文章已删除"})


@note_api_bp.route("/favicon.ico")
def favicon():
    """
    兼容浏览器默认请求 /favicon.ico：
    - 不再因为缺失 favicon 造成 404/日志噪音（更不会被误判成 500）
    """
    resp = make_response("", 204)
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp
