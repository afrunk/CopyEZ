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


def currency_filter(value):
    """
    Format a number as currency with thousands separators.

    Usage in templates:
        {{ amount|currency }}
        {{ amount|currency(prefix='¥') }}

    Args:
        value: Number or string to format

    Returns:
        Formatted currency string (e.g., "300,000" or "¥300,000")
    """
    if value is None:
        return '0'
    try:
        num = int(value)
        return f"{num:,}"
    except (ValueError, TypeError):
        return str(value)


# Register all filters with Flask app
def register_filters(app):
    """
    Register all template filters with the Flask app.

    Args:
        app: Flask application instance
    """
    app.add_template_filter(urlquote_filter, name='urlquote')
    app.add_template_filter(currency_filter, name='currency')
    app.add_template_filter(currency_filter, name='fmt_currency')
