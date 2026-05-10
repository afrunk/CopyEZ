"""
Text processing utilities for the application.

This module contains pure text processing functions that don't depend on Flask.
"""

import re


def estimate_text_length(markdown_text: str) -> int:
    """
    Estimate the actual text length from markdown content.

    Used for displaying "Current article: XXXX characters" on the reading page.

    Processing steps:
    1. Remove fenced code blocks (```...```)
    2. Remove inline code (`...`)
    3. Remove images (![alt](url))
    4. Keep visible text in links ([text](url))
    5. Remove HTML tags
    6. Remove common markdown symbols
    7. Count actual characters (excluding whitespace)

    Args:
        markdown_text: The markdown content to analyze

    Returns:
        Estimated character count of visible text
    """
    if not markdown_text:
        return 0

    text = markdown_text

    # 1) Remove fenced code block
    text = re.sub(r"```[\s\S]*?```", "", text)

    # 2) Remove inline code
    text = re.sub(r"`[^`]*`", "", text)

    # 3) Remove images
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)

    # 4) Keep visible text in links
    text = re.sub(r"\[([^\]]*?)\]\([^)]*\)", r"\1", text)

    # 5) Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # 6) Remove common markdown symbols
    text = re.sub(r"[>#*_~\-]+", " ", text)

    # 7) Remove all whitespace, count actual characters
    text = re.sub(r"\s+", "", text).strip()
    return len(text)
