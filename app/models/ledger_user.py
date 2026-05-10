"""
LedgerEZ User model.
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class User(db.Model):
    """User model for LedgerEZ dual-user accounting."""
    
    __tablename__ = "ledger_users"

    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    nickname = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="me")  # 'me' or 'wife'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Partner binding
    partner_id = db.Column(db.Integer, db.ForeignKey("ledger_users.id"), nullable=True)
    bind_code = db.Column(db.String(10), nullable=True)
    bind_code_expires_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    transactions = db.relationship("Transaction", back_populates="owner", lazy="dynamic")
    accounts = db.relationship("Account", back_populates="owner", lazy="dynamic")
    partner = db.relationship("User", remote_side=[id], foreign_keys=[partner_id], backref="partner_of")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_wife(self):
        return self.role == "wife"

    def __repr__(self):
        return f"<User {self.nickname} ({self.role})>"
