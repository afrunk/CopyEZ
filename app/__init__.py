"""
app package - Flask application factory

This package will eventually contain the application factory pattern
for better modularization and testability.

Future structure:
    app/
        __init__.py      # create_app() factory function
        extensions.py    # Flask extensions (db, etc.)
        models/          # SQLAlchemy models
        routes/          # Blueprint routes
        services/        # Business logic services
        utils/           # Utility functions

Current status:
    - Phase 1A: Skeleton created, no business logic moved yet
    - Phase 1B: Migrate configuration to config.py
    - Phase 2:   Move db to extensions.py
    - Phase 3:   Migrate models
    - Phase 4:   Migrate simple page routes
    - Phase 5:   Migrate API and complex business
    - Phase 6:   Split services/utils
    - Phase 7:   Clean up old app.py

Note:
    The current app.py in the project root still serves as the main entry point.
    This package is being prepared for future refactoring.
"""

# Placeholder for future create_app() factory
# Will be implemented in Phase 1B or later

__version__ = "1.0.0"
