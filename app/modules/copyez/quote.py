"""
Quote module - 摘抄语录功能

提取笔记中的高亮批注，生成语录列表。
"""

import re
import json
from datetime import datetime

import bleach
from app.extensions import db
from app.models import Note


def collect_quote_items():
    """
    遍历所有带批注的文章，提取「高亮原文 + 批注」列表，
    并按"文章"维度聚合，供"摘抄语录本"和导出复用。

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
        allowed = {"hl-red", "hl-blue", "hl-bold"}

        def _filter_class_attr(match):
            cls_raw = match.group(1) or ""
            kept = [c for c in cls_raw.split() if c in allowed]
            if not kept:
                return ""
            return f'class="{" ".join(kept)}"'

        cleaned = re.sub(r'class="([^"]*)"', _filter_class_attr, cleaned)
        cleaned = re.sub(r"\s+>", ">", cleaned)
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

            visible_text = re.sub(r"<[^>]+>", "", text_val)
            visible_text = re.sub(r"\s+", "", visible_text)
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
