"""
Category / Tags API - CopyEZ 公文素材库

提供分类和标签的 JSON API：
- GET /api/categories - 获取所有二级分类
- GET /api/tags - 获取所有三级标签
"""

from flask import request, jsonify
from sqlalchemy import distinct

from app.extensions import db
from app.models import Note, CustomCategory
from app.utils.presets import PRESET_CATEGORIES, PRESET_TAGS


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
