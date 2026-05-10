"""
Dashboard / Activity Stats API - CopyEZ 公文素材库

提供统计和看板相关的 JSON API：
- GET /api/activity_stats - 贡献热力图统计（365天）
- GET /api/tag_collection - 标签合集目录
"""

from datetime import datetime, timedelta, date
from flask import jsonify, request

from app.extensions import db
from app.models import Note
from app.utils.datetime_utils import now_bj


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
    - 始终覆盖从 (now - 364 天) 到 today 共 365 天，避免因为数据缺失导致前端"截断"
    """
    from sqlalchemy import func

    now = now_bj()
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
