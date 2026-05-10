"""
Content processing utilities for the application.

This module contains pure text processing functions for content rendering,
markdown processing, and HTML sanitization. These functions have no Flask
dependencies and can be unit tested independently.
"""

import re
import json
import markdown
import bleach
from markupsafe import Markup


# ── HTML 安全白名单 ───────────────────────────────────────────────────────────

ALLOWED_HTML_TAGS = [
    # 文本与段落
    "p", "br", "span", "div", "strong", "em", "b", "i", "u", "s",
    # 标题
    "h1", "h2", "h3", "h4", "h5", "h6",
    # 列表
    "ul", "ol", "li",
    # 代码块与引用
    "pre", "code", "blockquote",
    # 表格
    "table", "thead", "tbody", "tr", "th", "td",
    # 链接与图片
    "a", "img",
    # 其它常见结构
    "hr"
]

ALLOWED_HTML_ATTRIBUTES = {
    # 全局允许的基础属性（不包含 style，避免破坏统一排版）
    "*": ["id", "class"],
    "a": ["href", "title", "target", "rel", "class"],
    # 图片必须显式允许 src / alt / class / data-src，否则会被 bleach 清洗掉
    "img": ["src", "alt", "title", "class", "data-src"],
}


# ── 内容清洗工具 ──────────────────────────────────────────────────────────────

def clean_word_formatting(text: str) -> str:
    """
    清理从 Word 粘贴过来的格式问题：
    - 移除段首多余空格和特殊空白符（如 &nbsp;）
    - 统一处理全角/半角空格
    """
    text = re.sub(r'^[\s\u3000\u00A0]+', '', text)
    text = text.replace('&nbsp;', ' ')
    text = text.replace('\u00A0', ' ')  # 不间断空格
    text = text.replace('\u3000', ' ')  # 全角空格
    text = re.sub(r' +', ' ', text)
    return text.strip()


def deep_clean_content(content: str) -> str:
    """
    深度清洗函数：对从 Word 粘贴的长文本执行强力格式清洗
    - 逐行扫描：将内容按行分割
    - 正则清洗：对每一行执行 re.sub(r'^[ \t\u00A0\u3000]+', '', line)
      - [ \t] 匹配普通空格和制表符
      - \u00A0 匹配 Word 常见的 &nbsp;（不间断空格）
      - \u3000 匹配中文全角空格
    - 规范化换行：合并连续的多个空行为一个
    - 预期结果：数据库中存储的每一段开头都必须是"绝对顶格"的汉字，没有任何空白
    """
    if not content:
        return content

    content = content.replace("\r\n", "\n").replace("\r", "\n")
    content = re.sub(r'^[ \t\u00A0\u3000]+', '', content, flags=re.MULTILINE)
    content = re.sub(r'\n\n+', '\n\n', content)
    content = content.strip()

    return content


def auto_structure_speech_markdown(content: str) -> str:
    """
    针对"政法系统讲话稿 / 经验交流稿"这类 Word 粘贴文本的轻量级结构化工具。

    设计目标：
    - 识别「一、二、三、」这类总分结构，自动升级为 Markdown 标题（# 一级标题）
    - 识别「第一阶段……。」「一是突出党性。」「二是自我超越。」等句式，
      自动为首句加粗，生成 **第一阶段……。** 的效果
    - 完全兼容已有内容：如果用户已经手写了 # / ## 标题，则不做任何结构化改写

    触发条件（防误伤）：
    - 原文中不存在任何以 # 开头的 Markdown 标题
    - 且至少出现 2 条"总分结构"行（如「一、」「二、」「三、」），
      或至少出现 2 条「一是」「二是」这类小条目句式，才启用自动结构化
    """
    if not content:
        return content

    content = content.replace("\r\n", "\n").replace("\r", "\n")
    lines = content.splitlines()

    if any(re.match(r"^\s*#+\s+", line) for line in lines):
        return content

    top_heading_pattern = re.compile(r"^\s*[一二三四五六七八九十]{1,3}、")
    sub_heading_pattern = re.compile(r"^\s*（[一二三四五六七八九十]{1,3}）")
    bullet_sentence_pattern = re.compile(r"^\s*[一二三四五六七八九十][是要]")

    top_heading_count = sum(1 for line in lines if top_heading_pattern.match(line or ""))
    bullet_sentence_count = sum(1 for line in lines if bullet_sentence_pattern.match(line or ""))

    if top_heading_count < 2 and bullet_sentence_count < 2:
        return content

    processed_lines = []

    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()

        if not stripped:
            processed_lines.append(line)
            continue

        if top_heading_pattern.match(stripped):
            processed_lines.append("# " + stripped)
            continue

        if sub_heading_pattern.match(stripped):
            processed_lines.append("## " + stripped)
            continue

        m_phase = re.match(r"^(第[一二三四五六七八九十]{1,3}阶段[^。]*。)(.*)$", stripped)
        if m_phase:
            head = m_phase.group(1).strip()
            tail = m_phase.group(2).lstrip()
            if tail:
                processed_lines.append(f"**{head}**{tail}")
            else:
                processed_lines.append(f"**{head}**")
            continue

        m_bullet = re.match(r"^([一二三四五六七八九十][是要][^。]*。)(.*)$", stripped)
        if m_bullet:
            head = m_bullet.group(1).strip()
            tail = m_bullet.group(2).lstrip()
            if tail:
                processed_lines.append(f"**{head}**{tail}")
            else:
                processed_lines.append(f"**{head}**")
            continue

        processed_lines.append(line)

    return "\n".join(processed_lines)


# ── 内容渲染 ─────────────────────────────────────────────────────────────────

def render_content(raw_content: str, return_toc: bool = False):
    """
    内容解析器（彻底修复版）：彻底修复长文档多个自然段被合并为一个 <p> 标签的问题

    核心策略：
    1. 行首去污：只删除行首空白字符，保留空行本身
    2. 强制段落分隔：确保每个非空行都被空行包围，强制 Markdown 识别为独立段落
    3. Markdown 渲染后，在 HTML 层面再次强制拆分段落（双重保险）

    参数:
        raw_content: 原始 Markdown 内容
        return_toc: 如果为 True，返回 (html, toc_html) 元组；否则只返回 html

    返回:
        如果 return_toc=False: Markup(html)
        如果 return_toc=True: (Markup(html), toc_html)
    """
    if not raw_content:
        if return_toc:
            return Markup(''), ''
        return Markup('')

    raw_content = raw_content.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.lstrip(' \t\u00A0\u3000') for line in raw_content.splitlines()]

    processed_lines = []
    for i, line in enumerate(lines):
        if line.strip():
            processed_lines.append(line)
            if i < len(lines) - 1:
                next_line = lines[i + 1]
                if next_line.strip():
                    processed_lines.append('')
        else:
            processed_lines.append(line)

    cleaned_content = '\n'.join(processed_lines)
    cleaned_content = re.sub(r'^(#+)([^#\s])', r'\1 \2', cleaned_content, flags=re.MULTILINE)
    cleaned_content = re.sub(r'\n\n+', '\n\n', cleaned_content)
    cleaned_content = cleaned_content.strip()

    section_counter = [0]

    def english_slugify(text, separator='-'):
        section_counter[0] += 1
        return f'section-{section_counter[0]}'

    md = markdown.Markdown(
        extensions=['toc', 'fenced_code', 'tables'],
        extension_configs={
            'toc': {
                'baselevel': 1,
                'slugify': english_slugify
            }
        }
    )

    html = md.convert(cleaned_content)
    toc_html = md.toc if hasattr(md, 'toc') and md.toc else ''

    def split_paragraphs_by_br(html_content: str) -> str:
        pattern = re.compile(r'<p([^>]*)>(.*?)</p>', re.DOTALL)

        def _replace(match):
            attrs = match.group(1)
            inner = match.group(2)
            parts = re.split(r'<br\s*/?>\s*', inner)
            parts = [p for p in parts if p.strip()]
            if len(parts) <= 1:
                return match.group(0)
            return ''.join(f'<p{attrs}>{p}</p>' for p in parts)

        return pattern.sub(_replace, html_content)

    html = split_paragraphs_by_br(html)

    original_paragraph_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]

    def force_split_merged_paragraphs(html_content: str, original_lines: list) -> str:
        if len(original_lines) <= 1:
            return html_content

        pattern = re.compile(r'<p([^>]*)>(.*?)</p>', re.DOTALL)

        def _replace(match):
            attrs = match.group(1)
            inner = match.group(2)
            text_content = re.sub(r'<[^>]+>', '', inner).strip()

            matching_lines = []
            for orig_line in original_lines:
                orig_text = orig_line.strip()
                if orig_text and len(orig_text) >= 15 and orig_text in text_content:
                    matching_lines.append(orig_text)

            if len(matching_lines) >= 2:
                parts = []
                remaining_html = inner
                remaining_text = text_content

                for i, orig_text in enumerate(matching_lines):
                    if i == len(matching_lines) - 1:
                        parts.append(remaining_html)
                        break

                    pos_in_text = remaining_text.find(orig_text)
                    if pos_in_text == -1:
                        continue

                    html_pos = 0
                    text_pos = 0
                    for char in remaining_html:
                        if text_pos >= pos_in_text + len(orig_text):
                            break
                        if char == '<':
                            while html_pos < len(remaining_html) and remaining_html[html_pos] != '>':
                                html_pos += 1
                            if html_pos < len(remaining_html):
                                html_pos += 1
                            continue
                        if text_pos < pos_in_text + len(orig_text):
                            html_pos += 1
                            text_pos += 1

                    if html_pos > 0 and html_pos < len(remaining_html):
                        parts.append(remaining_html[:html_pos])
                        remaining_html = remaining_html[html_pos:]
                        remaining_text = remaining_text[pos_in_text + len(orig_text):]
                    else:
                        text_ratio = (pos_in_text + len(orig_text)) / len(remaining_text) if remaining_text else 0
                        html_split_pos = int(len(remaining_html) * text_ratio)
                        if html_split_pos > 0 and html_split_pos < len(remaining_html):
                            parts.append(remaining_html[:html_split_pos])
                            remaining_html = remaining_html[html_split_pos:]
                            remaining_text = remaining_text[pos_in_text + len(orig_text):]

                if len(parts) >= 2:
                    return ''.join(f'<p{attrs}>{part}</p>' for part in parts if part.strip())

            return match.group(0)

        return pattern.sub(_replace, html_content)

    html = force_split_merged_paragraphs(html, original_paragraph_lines)

    def add_heading_class(match):
        level = match.group(1)
        attrs = match.group(2)

        if 'class=' not in attrs:
            attrs = f'{attrs} class="heading level-{level}"'
        elif 'heading' not in attrs:
            attrs = re.sub(
                r'class="([^"]*)"',
                rf'class="\1 heading level-{level}"',
                attrs
            )

        return f'<h{level}{attrs}>'

    html = re.sub(
        r'<h([123])([^>]*)>',
        add_heading_class,
        html
    )

    def add_paragraph_class(match):
        attrs = match.group(1)
        if 'class=' not in attrs:
            attrs = f'{attrs} class="paragraph"'
        elif 'paragraph' not in attrs:
            attrs = re.sub(
                r'class="([^"]*)"',
                r'class="\1 paragraph"',
                attrs
            )
        return f'<p{attrs}>'

    html = re.sub(
        r'<p([^>]*)>',
        add_paragraph_class,
        html
    )

    header_index = [0]

    def ensure_all_headings_have_id(html_content):
        nonlocal header_index

        pattern = r'<h([123])([^>]*)>(.*?)</h\1>'

        def replace_heading(match):
            nonlocal header_index
            level = match.group(1)
            attrs = match.group(2)
            content = match.group(3)

            if 'id=' not in attrs:
                header_index[0] += 1
                heading_id = f"section-{header_index[0]}"
                attrs = f'{attrs} id="{heading_id}"'

            return f'<h{level}{attrs}>{content}</h{level}>'

        return re.sub(pattern, replace_heading, html_content, flags=re.DOTALL)

    html = ensure_all_headings_have_id(html)

    def remove_empty_paragraphs(html_content: str) -> str:
        pattern = re.compile(r'<p([^>]*)>(.*?)</p>', re.DOTALL)

        def _replace(match):
            attrs = match.group(1)
            inner = match.group(2)

            if re.search(r'<img\b', inner, re.IGNORECASE):
                return match.group(0)

            text_content = re.sub(r'<[^>]+>', '', inner)
            text_content = re.sub(r'[\s\u00A0\u3000]+', '', text_content)

            if not text_content.strip():
                return ''

            return match.group(0)

        html_content = pattern.sub(_replace, html_content)
        html_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', html_content)

        return html_content

    html = remove_empty_paragraphs(html)

    html = bleach.clean(
        html,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRIBUTES,
        strip=True,
    )

    def apply_lazyload_to_images(html_content: str) -> str:
        img_pattern = re.compile(r'<img([^>]*?)src="([^"]+)"([^>]*)>', re.IGNORECASE)

        def _img_repl(match):
            before = match.group(1) or ""
            src_url = match.group(2) or ""
            after = match.group(3) or ""
            attrs = f"{before}{after}"

            if "data-src" in attrs:
                return match.group(0)

            if "class=" in attrs:
                attrs = re.sub(
                    r'class="([^"]*)"',
                    lambda m: f'class="{m.group(1)} lazyload"',
                    attrs,
                    count=1,
                )
            else:
                attrs = f'{attrs} class="lazyload"'

            attrs = re.sub(r"\s+", " ", attrs).strip()
            placeholder = "data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="

            return f'<img {attrs} src="{placeholder}" data-src="{src_url}">'

        return img_pattern.sub(_img_repl, html_content)

    html = apply_lazyload_to_images(html)

    if return_toc:
        return Markup(html), toc_html
    return Markup(html)
