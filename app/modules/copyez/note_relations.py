"""
Note relations API module.

APIs for related notes and knowledge graph (task chain detection).
"""

from flask import Blueprint, jsonify

from app.extensions import db
from app.models.note import Note

note_relations_bp = Blueprint("note_relations", __name__)


@note_relations_bp.route("/api/note/<int:note_id>/related", methods=["GET"])
def get_related_notes(note_id: int):
    """API：获取关联文章（知识图谱）

    根据当前文章的 subCategory（二级分类）和 tags（三级标签）检索相似度最高的前5篇文章。
    逻辑权重：相同标签 > 相同二级分类。

    同时支持脉络识别：如果标题包含'方案'、'计划'或'行动'，自动检索标题中包含相同关键词的'总结'、'通报'或'调研报告'。
    """
    note = Note.query.get_or_404(note_id)

    current_tags = note.get_tags_list()
    current_sub_category = note.subCategory
    current_title = note.title

    query = Note.query.filter(Note.id != note_id)

    task_chain_keywords = []
    task_chain_types = []

    trigger_keywords = ['方案', '计划', '行动']
    found_trigger = None

    for keyword in trigger_keywords:
        if keyword in current_title:
            found_trigger = keyword
            task_chain_keywords.append(keyword)
            break

    if found_trigger:
        task_chain_types = ['总结', '通报', '调研报告']

    task_chain_notes = []
    if task_chain_keywords and task_chain_types:
        task_query = Note.query.filter(Note.id != note_id)

        trigger_conditions = []
        for keyword in task_chain_keywords:
            trigger_conditions.append(Note.title.like(f'%{keyword}%'))

        type_conditions = []
        for doc_type in task_chain_types:
            type_conditions.append(Note.title.like(f'%{doc_type}%'))

        if trigger_conditions and type_conditions:
            task_query = task_query.filter(
                db.or_(*trigger_conditions)
            ).filter(
                db.or_(*type_conditions)
            )

        task_chain_notes = task_query.order_by(Note.created_at.desc()).limit(5).all()

    related_notes = []
    all_notes = query.all()

    for other_note in all_notes:
        score = 0
        other_tags = other_note.get_tags_list()

        if current_tags and other_tags:
            common_tags = set(current_tags) & set(other_tags)
            score += len(common_tags) * 10

        if current_sub_category and other_note.subCategory == current_sub_category:
            score += 5

        if score > 0:
            related_notes.append({
                'note': other_note,
                'score': score
            })

    related_notes.sort(key=lambda x: x['score'], reverse=True)
    related_notes = related_notes[:5]

    result = {
        'related': [],
        'task_chain': {
            'detected': len(task_chain_notes) > 0,
            'keywords': task_chain_keywords,
            'notes': []
        }
    }

    for item in related_notes:
        note_obj = item['note']
        result['related'].append({
            'id': note_obj.id,
            'title': note_obj.title,
            'subCategory': note_obj.subCategory or '',
            'publishDate': note_obj.publishDate or '',
            'score': item['score']
        })

    for task_note in task_chain_notes:
        result['task_chain']['notes'].append({
            'id': task_note.id,
            'title': task_note.title,
            'subCategory': task_note.subCategory or '',
            'publishDate': task_note.publishDate or ''
        })

    response = jsonify(result)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
