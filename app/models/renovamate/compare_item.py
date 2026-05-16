"""
CompareItem Model - 中央空调方案
"""
from datetime import datetime
from app.extensions import db


class CompareItem(db.Model):
    """中央空调方案"""
    __tablename__ = 'renovamate_compare_items'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('decoration_projects.id'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('decoration_categories.id'), nullable=False, index=True)

    # 基本信息
    brand = db.Column(db.String(100), default='')           # 品牌
    model = db.Column(db.String(100), default='')           # 型号
    spec = db.Column(db.String(100), default='')             # 配置/匹数
    room_count = db.Column(db.Integer, default=0)            # 一拖几

    # 价格
    total_price = db.Column(db.Integer, default=0)           # 总价

    # 设备数量
    outdoor_unit_count = db.Column(db.Integer, default=0)     # 外机数量
    indoor_unit_count = db.Column(db.Integer, default=0)     # 内机数量

    # 其他
    energy_level = db.Column(db.String(20), default='')     # 能效等级
    warranty = db.Column(db.String(50), default='')         # 保修年限
    rating = db.Column(db.Float, default=0)                # 推荐指数 (0-5)

    # 图片链接（占位）
    product_image = db.Column(db.String(500), default='')    # 产品图片
    quote_image = db.Column(db.String(500), default='')      # 报价单图片

    # 备注
    note = db.Column(db.Text, default='')

    # 选择状态
    is_selected = db.Column(db.Boolean, default=False)       # 是否选中为最终方案

    # 排序
    sort_order = db.Column(db.Integer, default=0)

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'category_id': self.category_id,
            'brand': self.brand,
            'model': self.model,
            'spec': self.spec,
            'room_count': self.room_count,
            'total_price': self.total_price,
            'outdoor_unit_count': self.outdoor_unit_count,
            'indoor_unit_count': self.indoor_unit_count,
            'energy_level': self.energy_level,
            'warranty': self.warranty,
            'rating': self.rating,
            'product_image': self.product_image,
            'quote_image': self.quote_image,
            'note': self.note,
            'is_selected': self.is_selected,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<CompareItem {self.id}: {self.brand} {self.model}>'
