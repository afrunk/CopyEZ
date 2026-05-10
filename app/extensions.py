"""
Flask extensions management

This module contains centralized Flask extension instances.

Usage:
    from app.extensions import db

    # In app.py or create_app():
    db.init_app(app)

Current status:
    - Phase 2A: db = SQLAlchemy() defined here
    - Phase 2: Connected to app via init_app()
    - Future: Other extensions (migrate, login_manager, etc.) can be added here
"""

from flask_sqlalchemy import SQLAlchemy

# SQLAlchemy instance - initialized without app, will be connected via init_app()
db = SQLAlchemy()

# Placeholder for future extensions:
# migrate = Migrate()
# login_manager = LoginManager()
# csrf = CSRFProtect()
