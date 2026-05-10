"""Quick setup script for LedgerEZ"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Flask app and extensions directly from app.py
exec(open('app.py', encoding='utf-8').read().split("if __name__")[0])

from app.models import User, LedgerCategory
from app.extensions import db

def setup():
    with app.app_context():
        # Check if demo user exists
        u = User.query.filter_by(phone='13800000001').first()
        if not u:
            u = User(phone='13800000001', nickname='阿峰', role='me')
            u.set_password('123456')
            db.session.add(u)
            print('Demo user created: 13800000001 / 123456')
        
        # Create default categories
        if LedgerCategory.query.count() == 0:
            income_cats = [
                ('淘宝收入', 'shopping-bag', '#22c55e'),
                ('工资收入', 'trending-up', '#16a34a'),
                ('其他收入', 'plus-circle', '#6b7280')
            ]
            expense_cats = [
                ('日常生活', 'utensils', '#f97316'),
                ('居住家庭', 'home', '#fb923c'),
                ('人情关系', 'users', '#8b5cf6'),
                ('电子数码', 'smartphone', '#3b82f6'),
                ('淘宝支出', 'shopping-cart', '#ec4899'),
                ('大额支出', 'credit-card', '#f59e0b'),
                ('其他支出', 'more-horizontal', '#94a3b8')
            ]
            for name, icon, color in income_cats:
                db.session.add(LedgerCategory(name=name, category_type='income', icon=icon, color=color))
            for name, icon, color in expense_cats:
                db.session.add(LedgerCategory(name=name, category_type='expense', icon=icon, color=color))
            print('Categories created')
        
        db.session.commit()
        print('Setup complete!')

if __name__ == '__main__':
    setup()
