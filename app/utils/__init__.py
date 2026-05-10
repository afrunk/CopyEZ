"""
Utility functions

This package contains reusable utility functions.

Current status:
    - datetime_utils.py: Beijing time utilities
    - filters.py: Template filters
    - text_utils.py: Text processing utilities

Future utilities:
    app/utils/
        file_utils.py      # File handling
        markdown_utils.py  # Markdown helpers
"""

from app.utils.datetime_utils import now_bj, BJ_TZ
from app.utils.filters import urlquote_filter
from app.utils.text_utils import estimate_text_length
from app.utils.content_utils import (
    clean_word_formatting,
    deep_clean_content,
    auto_structure_speech_markdown,
    render_content,
    ALLOWED_HTML_TAGS,
    ALLOWED_HTML_ATTRIBUTES,
)
from app.utils.presets import PRESET_CATEGORIES, PRESET_TAGS, init_preset_categories, ALLOWED_IMAGE_EXTENSIONS
from app.utils.log_utils import write_log

__all__ = [
    'now_bj', 'BJ_TZ', 'urlquote_filter', 'estimate_text_length',
    'clean_word_formatting', 'deep_clean_content', 'auto_structure_speech_markdown',
    'render_content', 'ALLOWED_HTML_TAGS', 'ALLOWED_HTML_ATTRIBUTES',
    'PRESET_CATEGORIES', 'PRESET_TAGS', 'init_preset_categories', 'ALLOWED_IMAGE_EXTENSIONS',
    'write_log',
]
