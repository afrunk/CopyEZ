"""
Template filters for Jinja2 templates.

This module contains reusable template filters used across the application.
"""

from urllib.parse import quote


def urlquote_filter(s):
    """
    URL-encode a string for use in templates.

    Usage in templates:
        {{ some_url|urlquote }}

    Args:
        s: String to encode

    Returns:
        URL-encoded string
    """
    if s is None:
        return ''
    return quote(str(s), safe='')


# Register all filters with Flask app
def register_filters(app):
    """
    Register all template filters with the Flask app.

    Args:
        app: Flask application instance
    """
    app.add_template_filter(urlquote_filter, name='urlquote')
