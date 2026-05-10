"""
Preset data for categories and tags.

This module contains static reference data used throughout the application:
- PRESET_CATEGORIES: Two-level document classification system
- PRESET_TAGS: Business/domain tags for organization

These are pre-configured reference values that can be used for form defaults
and validation in the CopyEZ note management system.
"""

# ── 预置的公文分类知识库 ────────────────────────────────────────────────────────
PRESET_CATEGORIES = {
    "全文": [
        "大、中型会议讲话",
        "座谈会发言",
        "开班动员",
        "总结讲话",
        "调研报告",
        "年度工作总结",
        "述职报告",
        "专题请示",
        "实施方案",
        "暂行办法",
        "指导意见",
        "行动计划",
        "典型经验材料",
        "先进事迹",
        "工作综述",
        "信息快报",
        "批复",
        "通报",
        "通知",
        "函询"
    ],
    "框架": [
        "讲话框架",
        "报告框架",
        "方案框架",
        "总结框架"
    ],
    "短文摘要": [
        "要点摘要",
        "核心观点",
        "金句摘录"
    ]
}

# ── 预置的三级标签（业务/领域） ────────────────────────────────────────────────
PRESET_TAGS = [
    # 政法业务
    "平安建设",
    "法治建设",
    "社会治理",
    "扫黑除恶",
    "维稳工作",
    # 组织人事
    "队伍建设",
    "廉政教育",
    "教育整顿",
    "基层党建",
    # 专项行动
    "大练兵",
    "大排查",
    "利剑行动",
    "清网行动",
    # 其他常用标签
    "党建",
    "政法类型",
    "专项行动",
    "安全生产",
    "环境保护",
    "乡村振兴",
    "经济发展"
]

def init_preset_categories(db_session, CustomCategory):
    """
    初始化预置的二级分类到数据库。

    Args:
        db_session: SQLAlchemy db.session instance
        CustomCategory: CustomCategory model class
    """
    for main_cat, sub_cats in PRESET_CATEGORIES.items():
        for sub_cat in sub_cats:
            existing = CustomCategory.query.filter_by(name=sub_cat).first()
            if not existing:
                category = CustomCategory(name=sub_cat, main_category=main_cat)
                db_session.add(category)
    db_session.commit()


ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
