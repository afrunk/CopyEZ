"""
RenovaMate Blueprint - Flask Routes
装修助手模块

URL 前缀: /decoration
模板目录: templates/decoration/
静态目录: static/decoration/
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import os
from app.extensions import db
from app.models.renovamate import (
    DecorationProject,
    DecorationCategoryGroup,
    DecorationCategory,
    CompareItem,
    Expense,
    ProgressTask,
    DecorationNote,
)

# 从 blueprint 文件向上到达项目根目录
# __file__ = app/modules/renovamate/__init__.py
# 向上 3 层: __file__ -> renovamate -> modules -> app -> 项目根
_blueprint_dir = os.path.dirname(os.path.abspath(__file__))               # app/modules/renovamate
_modules_dir = os.path.dirname(_blueprint_dir)                             # app/modules
_app_dir = os.path.dirname(_modules_dir)                                  # app
_project_root = os.path.dirname(_app_dir)                                  # 项目根目录

bp = Blueprint(
    'decoration',
    __name__,
    template_folder='../../templates',  # 相对于 blueprint 目录，指向项目根的 templates
    static_folder=os.path.join(_project_root, 'static', 'decoration'),
    static_url_path='/assets',  # 静态文件路径前缀（避免与 API 路由冲突）
    url_prefix='/decoration'
)

# Alias for app.py registration
renovamate_bp = bp


@bp.context_processor
def inject_sidebar_badges():
    """向所有模板注入侧边栏徽章动态数据"""
    ctx = get_project_context()
    return {
        'sidebar_compare_count': ctx.get('sidebar_compare_count', 0),
        'sidebar_over_count': ctx.get('sidebar_over_count', 0),
        'sidebar_notes_count': ctx.get('sidebar_notes_count', 0),
    }


def get_project_context():
    """获取项目上下文数据，用于所有页面"""
    project = DecorationProject.query.first()
    if project:
        total_budget = str(project.total_budget or 0)
        actual_spent = Expense.query.filter_by(project_id=project.id).with_entities(
            db.func.coalesce(db.func.sum(Expense.amount), 0)
        ).scalar() or 0
        remaining = str((project.total_budget or 0) - actual_spent)
        # estimated_cost = sum of CompareItem.total_price for selected plans
        estimated_cost = 0
        categories = DecorationCategory.query.filter_by(project_id=project.id).all()
        for cat in categories:
            if cat.selected_plan_id:
                item = CompareItem.query.get(cat.selected_plan_id)
                if item:
                    estimated_cost += item.total_price or 0

        # 侧边栏徽章动态计数
        sidebar_compare_count = len(categories)

        # 超支分类数：实际花费 > 已选方案预算
        over_count = 0
        for cat in categories:
            spent = Expense.query.filter_by(project_id=project.id, category_id=cat.id).with_entities(
                db.func.coalesce(db.func.sum(Expense.amount), 0)
            ).scalar() or 0
            budget = 0
            if cat.selected_plan_id:
                item = CompareItem.query.get(cat.selected_plan_id)
                if item:
                    budget = item.total_price or 0
            if budget > 0 and spent > budget:
                over_count += 1
            elif budget == 0 and spent > 0:
                # 无方案但有花费，也算超支
                over_count += 1

        sidebar_over_count = over_count

        # 手册条目数
        sidebar_notes_count = DecorationNote.query.filter_by(project_id=project.id).count()
    else:
        project = None
        total_budget = '未设置'
        actual_spent = 0
        remaining = '未设置'
        estimated_cost = 0
        sidebar_compare_count = 0
        sidebar_over_count = 0
        sidebar_notes_count = 0
    return {
        'project': project,
        'total_budget': total_budget,
        'actual_spent': actual_spent,
        'remaining': remaining,
        'estimated_cost': estimated_cost,
        'sidebar_compare_count': sidebar_compare_count,
        'sidebar_over_count': sidebar_over_count,
        'sidebar_notes_count': sidebar_notes_count,
    }


@bp.route('/')
def index():
    """RenovaMate 首页总览"""
    ctx = get_project_context()
    return render_template(
        'decoration/index.html',
        active_page='overview',
        page_title='首页总览',
        project=ctx['project'],
        categories=[],
        todos=[],
        recent_expenses=[],
        alerts=[],
        total_budget=ctx['total_budget'],
        actual_spent=ctx['actual_spent'],
        remaining=ctx['remaining']
    )


@bp.route('/project/save', methods=['POST'])
def save_project():
    """保存项目设置（创建或更新）"""
    project_id = request.form.get('project_id', '').strip()
    name = request.form.get('name', '').strip()
    house_area = request.form.get('house_area', '').strip()
    style = request.form.get('style', '').strip()
    total_budget_str = request.form.get('total_budget', '').strip()
    current_stage = request.form.get('current_stage', '').strip()
    description = request.form.get('description', '').strip()

    total_budget = 0
    if total_budget_str:
        try:
            total_budget = int(total_budget_str)
        except ValueError:
            total_budget = 0

    if project_id:
        project = DecorationProject.query.get(int(project_id))
        if project:
            project.name = name or '未命名项目'
            project.house_area = house_area
            project.style = style
            project.total_budget = total_budget
            project.current_stage = current_stage or None
            project.description = description
    else:
        project = DecorationProject(
            name=name or '未命名项目',
            house_area=house_area,
            style=style,
            total_budget=total_budget,
            current_stage=current_stage or None,
            description=description
        )
        db.session.add(project)

    db.session.commit()
    return redirect(url_for('decoration.index'))


@bp.route('/progress')
def progress():
    """装修进度"""
    ctx = get_project_context()
    progress_summary = {
        "percent": 0,
        "pending": 0,
        "ongoing": 0,
        "review": 0,
        "done": 0
    }
    return render_template(
        'decoration/progress.html',
        active_page='progress',
        page_title='装修进度',
        project=ctx['project'],
        total_budget=ctx['total_budget'],
        actual_spent=ctx['actual_spent'],
        remaining=ctx['remaining'],
        progress_summary=progress_summary
    )


@bp.route('/compare')
def compare():
    """分类比较"""
    ctx = get_project_context()
    return render_template(
        'decoration/compare.html',
        active_page='compare',
        page_title='分类比较',
        project=ctx['project'],
        total_budget=ctx['total_budget'],
        actual_spent=ctx['actual_spent'],
        remaining=ctx['remaining']
    )


@bp.route('/budget')
def budget():
    """预算控制"""
    ctx = get_project_context()
    project = ctx['project']
    estimated_cost = 0
    budget_items = []
    if project:
        # estimated_cost = sum of CompareItem.total_price where category.selected_plan_id = item.id
        categories = DecorationCategory.query.filter_by(project_id=project.id).all()
        for cat in categories:
            if cat.selected_plan_id:
                item = CompareItem.query.get(cat.selected_plan_id)
                if item:
                    estimated_cost += item.total_price or 0
                    budget_items.append({
                        'category_id': cat.id,
                        'category_name': cat.name,
                        'plan_name': item.brand + ' ' + item.model if item.model else item.brand,
                        'budget': item.total_price or 0,
                        'spent': 0,
                        'has_plan': True,
                        'status': 'pending'
                    })
                else:
                    budget_items.append({
                        'category_id': cat.id,
                        'category_name': cat.name,
                        'plan_name': '(方案已删除)',
                        'budget': 0,
                        'spent': 0,
                        'has_plan': False,
                        'status': 'pending'
                    })
            else:
                budget_items.append({
                    'category_id': cat.id,
                    'category_name': cat.name,
                    'plan_name': '未选方案',
                    'budget': 0,
                    'spent': 0,
                    'has_plan': False,
                    'status': 'pending'
                })
    return render_template(
        'decoration/budget.html',
        active_page='budget',
        page_title='预算控制',
        project=ctx['project'],
        total_budget=ctx['total_budget'],
        actual_spent=ctx['actual_spent'],
        remaining=ctx['remaining'],
        estimated_cost=estimated_cost,
        budget_items=budget_items,
        expenses=[],
        risk_alerts=[],
        spending_analysis=[]
    )


@bp.route('/notes')
def notes():
    """装修手册"""
    ctx = get_project_context()
    return render_template(
        'decoration/notes.html',
        active_page='notes',
        page_title='装修手册',
        project=ctx['project'],
        total_budget=ctx['total_budget'],
        actual_spent=ctx['actual_spent'],
        remaining=ctx['remaining']
    )


@bp.route('/compare/air-conditioner')
def air_conditioner():
    """中央空调详情"""
    ctx = get_project_context()
    project = ctx['project']

    # 查询当前项目下名称为"中央空调"的子分类
    ac_category = None
    if project:
        ac_category = DecorationCategory.query.filter_by(
            project_id=project.id,
            name='中央空调'
        ).first()

    return render_template(
        'decoration/air_conditioner.html',
        active_page='compare',
        page_title='中央空调详情',
        project=project,
        total_budget=ctx['total_budget'],
        actual_spent=ctx['actual_spent'],
        remaining=ctx['remaining'],
        ac_category=ac_category,
    )


# ═══════════════════════════════════════════
# API: 分类大类 (DecorationCategoryGroup)
# ═══════════════════════════════════════════

@bp.route('/api/groups')
def api_get_groups():
    """获取当前项目的所有分类大类"""
    project = DecorationProject.query.first()
    if not project:
        return jsonify({"status": "error", "message": "请先创建装修项目"}), 400

    groups = DecorationCategoryGroup.query.filter_by(project_id=project.id).order_by(DecorationCategoryGroup.sort_order).all()
    return jsonify({
        "status": "success",
        "data": [g.to_dict() for g in groups],
        "project_id": project.id
    })


@bp.route('/api/groups', methods=['POST'])
def api_create_group():
    """创建新的分类大类"""
    project = DecorationProject.query.first()
    if not project:
        return jsonify({"status": "error", "message": "请先创建装修项目"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "请求数据无效"}), 400

    name = data.get("name", "").strip()
    if not name:
        return jsonify({"status": "error", "message": "大类名称不能为空"}), 400

    group = DecorationCategoryGroup(
        project_id=project.id,
        name=name,
        icon=data.get("icon", "🏠"),
        description=data.get("description", ""),
        sort_order=int(data.get("sort_order", 0)),
        is_enabled=data.get("is_enabled", True)
    )
    db.session.add(group)
    db.session.commit()

    return jsonify({"status": "success", "data": group.to_dict()})


@bp.route('/api/groups/<int:group_id>', methods=['PUT'])
def api_update_group(group_id):
    """更新分类大类"""
    group = DecorationCategoryGroup.query.get(group_id)
    if not group:
        return jsonify({"status": "error", "message": "大类不存在"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "请求数据无效"}), 400

    if "name" in data:
        name = data["name"].strip()
        if not name:
            return jsonify({"status": "error", "message": "大类名称不能为空"}), 400
        group.name = name
    if "icon" in data:
        group.icon = data["icon"]
    if "description" in data:
        group.description = data["description"]
    if "sort_order" in data:
        group.sort_order = int(data["sort_order"])
    if "is_enabled" in data:
        group.is_enabled = bool(data["is_enabled"])

    db.session.commit()
    return jsonify({"status": "success", "data": group.to_dict()})


@bp.route('/api/groups/<int:group_id>', methods=['DELETE'])
def api_delete_group(group_id):
    """删除分类大类"""
    group = DecorationCategoryGroup.query.get(group_id)
    if not group:
        return jsonify({"status": "error", "message": "大类不存在"}), 404

    db.session.delete(group)
    db.session.commit()
    return jsonify({"status": "success", "message": "大类已删除"})


# ═══════════════════════════════════════════
# API: 子分类 (DecorationCategory)
# ═══════════════════════════════════════════

@bp.route('/api/categories')
def api_get_categories():
    """获取当前项目的所有子分类"""
    project = DecorationProject.query.first()
    if not project:
        return jsonify({"status": "success", "data": [], "project_id": None})

    categories = DecorationCategory.query.filter_by(project_id=project.id).order_by(DecorationCategory.sort_order).all()
    return jsonify({
        "status": "success",
        "data": [c.to_dict() for c in categories],
        "project_id": project.id
    })


@bp.route('/api/categories', methods=['POST'])
def api_create_category():
    """创建新的子分类"""
    project = DecorationProject.query.first()
    if not project:
        return jsonify({"status": "error", "message": "请先创建装修项目"}), 400

    groups = DecorationCategoryGroup.query.filter_by(project_id=project.id).all()
    if not groups:
        return jsonify({"status": "error", "message": "请先添加分类大类"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "请求数据无效"}), 400

    name = data.get("name", "").strip()
    if not name:
        return jsonify({"status": "error", "message": "分类名称不能为空"}), 400

    group_id = data.get("group_id")
    if not group_id:
        return jsonify({"status": "error", "message": "请选择所属大类"}), 400

    # 验证 group_id 是否属于当前项目
    group = DecorationCategoryGroup.query.filter_by(id=int(group_id), project_id=project.id).first()
    if not group:
        return jsonify({"status": "error", "message": "所属大类不存在"}), 400

    category = DecorationCategory(
        project_id=project.id,
        group_id=int(group_id),
        name=name,
        icon=data.get("icon", "📦"),
        budget=float(data.get("budget", 0) or 0),
        status=data.get("status", "not_started"),
        view_mode=data.get("view_mode", "card"),
        description=data.get("description", ""),
        sort_order=int(data.get("sort_order", 0)),
        is_enabled=data.get("is_enabled", True)
    )
    db.session.add(category)
    db.session.commit()

    return jsonify({"status": "success", "data": category.to_dict()})


@bp.route('/api/categories/<int:category_id>', methods=['PUT'])
def api_update_category(category_id):
    """更新子分类"""
    category = DecorationCategory.query.get(category_id)
    if not category:
        return jsonify({"status": "error", "message": "子分类不存在"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "请求数据无效"}), 400

    if "name" in data:
        name = data["name"].strip()
        if not name:
            return jsonify({"status": "error", "message": "分类名称不能为空"}), 400
        category.name = name
    if "icon" in data:
        category.icon = data["icon"]
    if "budget" in data:
        category.budget = float(data["budget"] or 0)
    if "status" in data:
        category.status = data["status"]
    if "view_mode" in data:
        category.view_mode = data["view_mode"]
    if "description" in data:
        category.description = data["description"]
    if "sort_order" in data:
        category.sort_order = int(data["sort_order"])
    if "is_enabled" in data:
        category.is_enabled = bool(data["is_enabled"])

    # group_id 变更时验证
    if "group_id" in data:
        new_group_id = int(data["group_id"])
        project = DecorationProject.query.first()
        if not project:
            return jsonify({"status": "error", "message": "请先创建装修项目"}), 400
        group = DecorationCategoryGroup.query.filter_by(id=new_group_id, project_id=project.id).first()
        if not group:
            return jsonify({"status": "error", "message": "所属大类不存在"}), 400
        category.group_id = new_group_id

    db.session.commit()
    return jsonify({"status": "success", "data": category.to_dict()})


@bp.route('/api/categories/<int:category_id>', methods=['DELETE'])
def api_delete_category(category_id):
    """删除子分类"""
    category = DecorationCategory.query.get(category_id)
    if not category:
        return jsonify({"status": "error", "message": "子分类不存在"}), 404

    db.session.delete(category)
    db.session.commit()
    return jsonify({"status": "success", "message": "子分类已删除"})


# ═══════════════════════════════════════════
# API: CompareItem 方案管理
# ═══════════════════════════════════════════

@bp.route('/api/compare-items')
def api_get_compare_items():
    """获取所有方案"""
    project = DecorationProject.query.first()
    if not project:
        return jsonify({"status": "error", "message": "请先创建装修项目"}), 400

    items = CompareItem.query.filter_by(project_id=project.id).order_by(CompareItem.sort_order, CompareItem.created_at.desc()).all()
    return jsonify({
        "status": "success",
        "data": [item.to_dict() for item in items]
    })


@bp.route('/api/compare-items/<int:category_id>')
def api_get_compare_items_by_category(category_id):
    """获取指定分类的方案"""
    project = DecorationProject.query.first()
    if not project:
        return jsonify({"status": "error", "message": "请先创建装修项目"}), 400

    items = CompareItem.query.filter_by(
        project_id=project.id,
        category_id=category_id
    ).order_by(CompareItem.sort_order, CompareItem.created_at.desc()).all()

    # 获取分类信息
    category = DecorationCategory.query.get(category_id)

    return jsonify({
        "status": "success",
        "data": [item.to_dict() for item in items],
        "category": category.to_dict() if category else None
    })


@bp.route('/api/compare-items', methods=['POST'])
def api_create_compare_item():
    """创建新的方案"""
    project = DecorationProject.query.first()
    if not project:
        return jsonify({"status": "error", "message": "请先创建装修项目"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "请求数据无效"}), 400

    category_id = data.get('category_id')
    if not category_id:
        return jsonify({"status": "error", "message": "分类 ID 不能为空"}), 400

    # 验证分类存在且属于当前项目
    category = DecorationCategory.query.filter_by(
        id=category_id, project_id=project.id
    ).first()
    if not category:
        return jsonify({"status": "error", "message": "分类不存在或不属于当前项目"}), 404

    item = CompareItem(
        project_id=project.id,
        category_id=category_id,
        brand=data.get('brand', ''),
        model=data.get('model', ''),
        spec=data.get('spec', ''),
        room_count=int(data.get('room_count') or 0),
        total_price=int(data.get('total_price') or 0),
        outdoor_unit_count=int(data.get('outdoor_unit_count') or 0),
        indoor_unit_count=int(data.get('indoor_unit_count') or 0),
        energy_level=data.get('energy_level', ''),
        warranty=data.get('warranty', ''),
        rating=float(data.get('rating') or 0),
        product_image=data.get('product_image', ''),
        quote_image=data.get('quote_image', ''),
        note=data.get('note', ''),
        sort_order=int(data.get('sort_order') or 0)
    )
    db.session.add(item)
    db.session.commit()

    return jsonify({"status": "success", "data": item.to_dict()})


@bp.route('/api/compare-items/<int:item_id>', methods=['PUT'])
def api_update_compare_item(item_id):
    """更新方案"""
    item = CompareItem.query.get(item_id)
    if not item:
        return jsonify({"status": "error", "message": "方案不存在"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "请求数据无效"}), 400

    item.brand = data.get('brand', item.brand)
    item.model = data.get('model', item.model)
    item.spec = data.get('spec', item.spec)
    item.room_count = int(data.get('room_count') or item.room_count)
    item.total_price = int(data.get('total_price') or item.total_price)
    item.outdoor_unit_count = int(data.get('outdoor_unit_count') or item.outdoor_unit_count)
    item.indoor_unit_count = int(data.get('indoor_unit_count') or item.indoor_unit_count)
    item.energy_level = data.get('energy_level', item.energy_level)
    item.warranty = data.get('warranty', item.warranty)
    item.rating = float(data.get('rating') or item.rating)
    item.product_image = data.get('product_image', item.product_image)
    item.quote_image = data.get('quote_image', item.quote_image)
    item.note = data.get('note', item.note)
    item.sort_order = int(data.get('sort_order') or item.sort_order)

    db.session.commit()
    return jsonify({"status": "success", "data": item.to_dict()})


@bp.route('/api/compare-items/<int:item_id>', methods=['DELETE'])
def api_delete_compare_item(item_id):
    """删除方案"""
    item = CompareItem.query.get(item_id)
    if not item:
        return jsonify({"status": "error", "message": "方案不存在"}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({"status": "success", "message": "方案已删除"})


@bp.route('/api/compare-items/<int:item_id>/select', methods=['POST'])
def api_select_compare_item(item_id):
    """选为最终方案（同一分类只能有一个选中）"""
    item = CompareItem.query.get(item_id)
    if not item:
        return jsonify({"status": "error", "message": "方案不存在"}), 404

    # 取消同分类的其他选中状态
    CompareItem.query.filter(
        CompareItem.category_id == item.category_id,
        CompareItem.id != item_id
    ).update({'is_selected': False})

    # 选中当前方案
    item.is_selected = True
    db.session.commit()

    # 更新分类的 selected_plan_id 和状态
    category = DecorationCategory.query.get(item.category_id)
    if category:
        category.selected_plan_id = item_id
        category.status = 'selected'
        db.session.commit()

    return jsonify({
        "status": "success",
        "data": item.to_dict(),
        "message": "已选为最终方案"
    })


@bp.route('/api/compare-items/<int:item_id>/deselect', methods=['POST'])
def api_deselect_compare_item(item_id):
    """取消选中方案"""
    item = CompareItem.query.get(item_id)
    if not item:
        return jsonify({"status": "error", "message": "方案不存在"}), 404

    item.is_selected = False
    db.session.commit()

    # 清除分类的选中状态
    category = DecorationCategory.query.get(item.category_id)
    if category and category.selected_plan_id == item_id:
        category.selected_plan_id = None
        category.status = 'not_started'
        db.session.commit()

    return jsonify({
        "status": "success",
        "data": item.to_dict(),
        "message": "已取消选中"
    })


# ═══════════════════════════════════════════
# API: 预算汇总 (Budget Summary)
# ═══════════════════════════════════════════

@bp.route('/api/budget/summary')
def api_budget_summary():
    """获取预算汇总数据（预计花费 + 实际已花 + 明细 + 分析）"""
    project = DecorationProject.query.first()
    if not project:
        return jsonify({"status": "error", "message": "请先创建装修项目"}), 400

    total_budget = project.total_budget or 0

    # actual_spent = sum of all Expense.amount
    actual_spent = Expense.query.filter_by(project_id=project.id).with_entities(
        db.func.coalesce(db.func.sum(Expense.amount), 0)
    ).scalar() or 0

    remaining = total_budget - actual_spent

    # estimated_cost = sum of CompareItem.total_price for selected plans
    estimated_cost = 0

    # budget_items: each category with its selected plan + spent
    categories = DecorationCategory.query.filter_by(project_id=project.id).all()
    budget_items = []
    spending_by_category = {}

    for cat in categories:
        budget = 0
        plan_name = '未选方案'
        has_plan = False
        if cat.selected_plan_id:
            item = CompareItem.query.get(cat.selected_plan_id)
            if item:
                budget = item.total_price or 0
                plan_name = (item.brand or '') + (' ' + item.model if item.model else '')
                has_plan = True
                estimated_cost += budget
        budget_items.append({
            'category_id': cat.id,
            'category_name': cat.name,
            'plan_name': plan_name,
            'budget': budget,
            'spent': 0,
            'has_plan': has_plan,
            'status': 'pending'
        })
        spending_by_category[cat.id] = {
            'category_name': cat.name,
            'total': 0,
            'count': 0
        }

    # 计算每个分类的实际花费
    expenses = Expense.query.filter_by(project_id=project.id).all()
    for exp in expenses:
        if exp.category_id and exp.category_id in spending_by_category:
            spending_by_category[exp.category_id]['total'] += exp.amount or 0
            spending_by_category[exp.category_id]['count'] += 1
        # 更新 budget_items 中的 spent
        for item in budget_items:
            if item['category_id'] == exp.category_id:
                item['spent'] = (item.get('spent') or 0) + (exp.amount or 0)

    # 计算每个分类的状态
    over_count = 0
    saved_amount = 0
    for item in budget_items:
        if not item['has_plan']:
            item['status'] = 'pending'
        elif item['spent'] > item['budget']:
            item['status'] = 'over'
            over_count += 1
            saved_amount -= (item['spent'] - item['budget'])
        elif item['budget'] > 0 and item['spent'] == item['budget']:
            item['status'] = 'equal'
        elif item['spent'] > 0:
            item['status'] = 'saved'
            saved_amount += (item['budget'] - item['spent'])
        else:
            item['status'] = 'pending'

    # spending_analysis: top 5 categories by spending
    sorted_spending = sorted(
        [v for v in spending_by_category.values() if v['total'] > 0],
        key=lambda x: x['total'],
        reverse=True
    )[:5]

    return jsonify({
        "status": "success",
        "data": {
            "total_budget": total_budget,
            "estimated_cost": estimated_cost,
            "actual_spent": actual_spent,
            "remaining": remaining,
            "over_count": over_count,
            "saved_amount": saved_amount,
            "budget_items": budget_items,
            "spending_by_category": sorted_spending
        }
    })


# ═══════════════════════════════════════════
# API: Expense 实际花费
# ═══════════════════════════════════════════

@bp.route('/api/expenses')
def api_get_expenses():
    """获取所有花费记录"""
    project = DecorationProject.query.first()
    if not project:
        return jsonify({"status": "error", "message": "请先创建装修项目"}), 400

    items = Expense.query.filter_by(project_id=project.id).order_by(Expense.pay_date.desc(), Expense.created_at.desc()).all()
    return jsonify({
        "status": "success",
        "data": [item.to_dict() for item in items],
        "total": sum(item.amount for item in items)
    })


@bp.route('/api/expenses', methods=['POST'])
def api_create_expense():
    """创建新的花费记录"""
    project = DecorationProject.query.first()
    if not project:
        return jsonify({"status": "error", "message": "请先创建装修项目"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "请求数据无效"}), 400

    title = data.get('title', '').strip()
    if not title:
        return jsonify({"status": "error", "message": "花费名称不能为空"}), 400

    amount = int(data.get('amount') or 0)
    pay_date_str = data.get('pay_date')
    pay_date = None
    if pay_date_str:
        try:
            pay_date = datetime.strptime(pay_date_str[:10], '%Y-%m-%d').date()
        except ValueError:
            pay_date = None

    item = Expense(
        project_id=project.id,
        category_id=data.get('category_id'),
        compare_item_id=data.get('compare_item_id'),
        title=title,
        amount=amount,
        pay_date=pay_date,
        pay_method=data.get('pay_method', ''),
        vendor=data.get('vendor', ''),
        receipt_image=data.get('receipt_image', ''),
        note=data.get('note', '')
    )
    db.session.add(item)
    db.session.commit()

    return jsonify({"status": "success", "data": item.to_dict()})


@bp.route('/api/expenses/<int:expense_id>', methods=['GET'])
def api_get_expense(expense_id):
    """获取单条花费记录详情"""
    item = Expense.query.get(expense_id)
    if not item:
        return jsonify({"status": "error", "message": "花费记录不存在"}), 404
    
    return jsonify({"status": "success", "data": item.to_dict()})


@bp.route('/api/expenses/<int:expense_id>', methods=['PUT'])
def api_update_expense(expense_id):
    """更新花费记录"""
    item = Expense.query.get(expense_id)
    if not item:
        return jsonify({"status": "error", "message": "花费记录不存在"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "请求数据无效"}), 400

    if 'title' in data:
        title = data['title'].strip()
        if not title:
            return jsonify({"status": "error", "message": "花费名称不能为空"}), 400
        item.title = title
    if 'amount' in data:
        item.amount = int(data['amount'] or 0)
    if 'pay_date' in data:
        pay_date_str = data.get('pay_date')
        if pay_date_str:
            try:
                item.pay_date = datetime.strptime(pay_date_str[:10], '%Y-%m-%d').date()
            except ValueError:
                item.pay_date = None
        else:
            item.pay_date = None
    if 'pay_method' in data:
        item.pay_method = data['pay_method']
    if 'vendor' in data:
        item.vendor = data['vendor']
    if 'receipt_image' in data:
        item.receipt_image = data['receipt_image']
    if 'note' in data:
        item.note = data['note']
    if 'category_id' in data:
        item.category_id = data['category_id']

    db.session.commit()
    return jsonify({"status": "success", "data": item.to_dict()})


@bp.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
def api_delete_expense(expense_id):
    """删除花费记录"""
    item = Expense.query.get(expense_id)
    if not item:
        return jsonify({"status": "error", "message": "花费记录不存在"}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({"status": "success", "message": "花费记录已删除"})


# ═══════════════════════════════════════════
# API: ProgressTask 装修任务
# ═══════════════════════════════════════════

@bp.route('/api/tasks')
def api_get_tasks():
    """获取所有装修任务"""
    project = DecorationProject.query.first()
    if not project:
        return jsonify({"status": "error", "message": "请先创建装修项目"}), 400

    items = ProgressTask.query.filter_by(project_id=project.id).order_by(ProgressTask.created_at.desc()).all()
    return jsonify({
        "status": "success",
        "data": [item.to_dict() for item in items]
    })


@bp.route('/api/lookup-data')
def api_lookup_data():
    """统一返回当前项目下所有可供关联的数据，用于下拉填充"""
    project = DecorationProject.query.first()
    if not project:
        return jsonify({
            "status": "success",
            "data": {
                "categories": [],
                "tasks": [],
                "compare_items": [],
                "notes": []
            }
        })

    # 1. 分类列表（含所属大类名）
    category_objs = DecorationCategory.query.filter_by(project_id=project.id).all()
    categories = []
    for c in category_objs:
        group_name = ''
        if c.group_id:
            g = DecorationCategoryGroup.query.get(c.group_id)
            if g:
                group_name = g.name
        categories.append({
            'id': c.id,
            'name': c.name,
            'group_name': group_name
        })

    # 2. 任务列表
    task_objs = ProgressTask.query.filter_by(project_id=project.id).all()
    tasks = [{
        'id': t.id,
        'title': t.title,
        'stage': t.stage,
        'status': t.status
    } for t in task_objs]

    # 3. 方案列表（含分类名）
    item_objs = CompareItem.query.filter_by(project_id=project.id).all()
    compare_items = []
    for item in item_objs:
        cat_name = ''
        if item.category_id:
            cat = DecorationCategory.query.get(item.category_id)
            if cat:
                cat_name = cat.name
        compare_items.append({
            'id': item.id,
            'brand': item.brand,
            'model': item.model,
            'category_id': item.category_id,
            'category_name': cat_name
        })

    # 4. 手册记录列表
    note_objs = DecorationNote.query.filter_by(project_id=project.id).all()
    notes = [{
        'id': n.id,
        'title': n.title,
        'stage': n.stage,
        'category_id': n.category_id,
        'task_id': n.task_id,
        'compare_item_id': n.compare_item_id
    } for n in note_objs]

    return jsonify({
        "status": "success",
        "data": {
            "categories": categories,
            "tasks": tasks,
            "compare_items": compare_items,
            "notes": notes
        }
    })


@bp.route('/api/tasks', methods=['POST'])
def api_create_task():
    """创建新的装修任务"""
    project = DecorationProject.query.first()
    if not project:
        return jsonify({"status": "error", "message": "请先创建装修项目"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "请求数据无效"}), 400

    title = data.get('title', '').strip()
    if not title:
        return jsonify({"status": "error", "message": "任务名称不能为空"}), 400

    item = ProgressTask(
        project_id=project.id,
        category_id=data.get('category_id'),
        title=title,
        stage=data.get('stage', 'design'),
        status=data.get('status', 'pending'),
        budget_amount=int(data.get('budget_amount') or 0),
        actual_amount=int(data.get('actual_amount') or 0),
        owner=data.get('owner', ''),
        note=data.get('note', '')
    )
    db.session.add(item)
    db.session.commit()

    return jsonify({"status": "success", "data": item.to_dict()})


@bp.route('/api/tasks/<int:task_id>', methods=['PUT'])
def api_update_task(task_id):
    """更新装修任务"""
    item = ProgressTask.query.get(task_id)
    if not item:
        return jsonify({"status": "error", "message": "任务不存在"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "请求数据无效"}), 400

    if 'title' in data:
        title = data['title'].strip()
        if not title:
            return jsonify({"status": "error", "message": "任务名称不能为空"}), 400
        item.title = title
    if 'stage' in data:
        item.stage = data['stage']
    if 'status' in data:
        item.status = data['status']
    if 'budget_amount' in data:
        item.budget_amount = int(data['budget_amount'] or 0)
    if 'actual_amount' in data:
        item.actual_amount = int(data['actual_amount'] or 0)
    if 'owner' in data:
        item.owner = data['owner']
    if 'note' in data:
        item.note = data['note']
    if 'category_id' in data:
        item.category_id = data['category_id']

    db.session.commit()
    return jsonify({"status": "success", "data": item.to_dict()})


@bp.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    """删除装修任务"""
    item = ProgressTask.query.get(task_id)
    if not item:
        return jsonify({"status": "error", "message": "任务不存在"}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({"status": "success", "message": "任务已删除"})


# ═══════════════════════════════════════════
# API: DecorationNote 装修手册
# ═══════════════════════════════════════════

@bp.route('/api/notes')
def api_get_notes():
    """获取所有装修手册记录"""
    project = DecorationProject.query.first()
    if not project:
        return jsonify({"status": "error", "message": "请先创建装修项目"}), 400

    items = DecorationNote.query.filter_by(project_id=project.id).order_by(DecorationNote.created_at.desc()).all()
    return jsonify({
        "status": "success",
        "data": [item.to_dict() for item in items]
    })


@bp.route('/api/notes', methods=['POST'])
def api_create_note():
    """创建新的装修手册记录"""
    project = DecorationProject.query.first()
    if not project:
        return jsonify({"status": "error", "message": "请先创建装修项目"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "请求数据无效"}), 400

    title = data.get('title', '').strip()
    if not title:
        return jsonify({"status": "error", "message": "记录标题不能为空"}), 400

    import json as _json
    tags = data.get('tags', [])
    if isinstance(tags, list):
        tags = _json.dumps(tags, ensure_ascii=False)
    elif not isinstance(tags, str):
        tags = '[]'

    image_urls = data.get('image_urls', [])
    if isinstance(image_urls, list):
        image_urls = _json.dumps(image_urls, ensure_ascii=False)
    elif not isinstance(image_urls, str):
        image_urls = '[]'

    item = DecorationNote(
        project_id=project.id,
        category_id=data.get('category_id'),
        task_id=data.get('task_id'),
        compare_item_id=data.get('compare_item_id'),
        stage=DecorationNote().normalize_stage(data.get('stage', 'design')),
        title=title,
        source_url=data.get('source_url', ''),
        content=data.get('content', ''),
        tags=tags,
        image_urls=image_urls
    )
    db.session.add(item)
    db.session.commit()

    return jsonify({"status": "success", "data": item.to_dict()})


@bp.route('/api/notes/<int:note_id>', methods=['PUT'])
def api_update_note(note_id):
    """更新装修手册记录"""
    item = DecorationNote.query.get(note_id)
    if not item:
        return jsonify({"status": "error", "message": "记录不存在"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "请求数据无效"}), 400

    if 'title' in data:
        title = data['title'].strip()
        if not title:
            return jsonify({"status": "error", "message": "记录标题不能为空"}), 400
        item.title = title
    if 'stage' in data:
        item.stage = DecorationNote().normalize_stage(data['stage'])
    if 'source_url' in data:
        item.source_url = data['source_url']
    if 'content' in data:
        item.content = data['content']
    if 'tags' in data:
        import json as _json
        tags = data['tags']
        if isinstance(tags, list):
            item.tags = _json.dumps(tags, ensure_ascii=False)
        else:
            item.tags = tags or '[]'
    if 'image_urls' in data:
        import json as _json
        image_urls = data['image_urls']
        if isinstance(image_urls, list):
            item.image_urls = _json.dumps(image_urls, ensure_ascii=False)
        else:
            item.image_urls = image_urls or '[]'
    if 'category_id' in data:
        item.category_id = data['category_id']
    if 'task_id' in data:
        item.task_id = data['task_id']
    if 'compare_item_id' in data:
        item.compare_item_id = data['compare_item_id']

    db.session.commit()
    return jsonify({"status": "success", "data": item.to_dict()})


@bp.route('/api/notes/<int:note_id>', methods=['DELETE'])
def api_delete_note(note_id):
    """删除装修手册记录"""
    item = DecorationNote.query.get(note_id)
    if not item:
        return jsonify({"status": "error", "message": "记录不存在"}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({"status": "success", "message": "记录已删除"})


@bp.route('/api/tasks/<int:task_id>/notes', methods=['GET'])
def api_get_task_notes(task_id):
    """获取任务关联的装修手册笔记"""
    notes = DecorationNote.query.filter_by(task_id=task_id).order_by(DecorationNote.created_at.desc()).all()
    return jsonify({
        "status": "success",
        "data": [note.to_dict() for note in notes],
        "count": len(notes)
    })


# ═══════════════════════════════════════════
# API: 图片上传 (Decoration Images)
# 注意：这个路由已在 app.py 中直接注册为 /decoration/api/upload/image
# 蓝图中的这个定义仅作为后备，保持向后兼容
# ═══════════════════════════════════════════

# 此路由已移至 app.py 以避免与蓝图静态路由冲突
