"""
Formatting API - CopyEZ 公文素材库

提供 Markdown 格式化接口：
- POST /api/format_markdown - 在线格式整理（不对数据库写入）

直接依赖函数（纯字符串处理，无 db 依赖）：
- deep_clean_content
- auto_structure_speech_markdown
"""

import re
from flask import jsonify, request


def deep_clean_content(content: str) -> str:
    """
    深度清洗函数：对从 Word 粘贴的长文本执行强力格式清洗
    - 逐行扫描：将内容按行分割
    - 正则清洗：对每一行执行 re.sub(r'^[ \\t\\u00A0\\u3000]+', '', line)
      - [ \\t] 匹配普通空格和制表符
      - \\u00A0 匹配 Word 常见的 &nbsp;（不间断空格）
      - \\u3000 匹配中文全角空格
    - 规范化换行：合并连续的多个空行为一个
    - 预期结果：数据库中存储的每一段开头都必须是"绝对顶格"的汉字，没有任何空白
    """
    if not content:
        return content

    # 统一换行符为 \\n
    content = content.replace("\\r\\n", "\\n").replace("\\r", "\\n")

    # 逐行扫描并清洗：去除每一行行首的所有空格、制表符、不间断空格、全角空格
    # 使用 re.MULTILINE 标志，确保 ^ 匹配每一行的开头
    content = re.sub(r'^[ \\t\\u00A0\\u3000]+', '', content, flags=re.MULTILINE)

    # 规范化换行：将连续的多个空行（2个及以上）合并为一个空行
    content = re.sub(r'\\n\\n+', '\\n\\n', content)

    # 去除首尾的空白字符（但保留内部的换行结构）
    content = content.strip()

    return content


def auto_structure_speech_markdown(content: str) -> str:
    """
    针对"政法系统讲话稿 / 经验交流稿"这类 Word 粘贴文本的轻量级结构化工具。

    设计目标：
    - 识别「一、二、三、」这类总分结构，自动升级为 Markdown 标题（# 一级标题）
    - 识别「第一阶段……」「一是突出党性。」「二是自我超越。」等句式，
      自动为首句加粗，生成 **第一阶段……** 的效果
    - 完全兼容已有内容：如果用户已经手写了 # / ## 标题，则不做任何结构化改写

    触发条件（防误伤）：
    - 原文中不存在任何以 # 开头的 Markdown 标题
    - 且至少出现 2 条"总分结构"行（如「一、」「二、」「三、」），
      或至少出现 2 条「一是」「二是」这类小条目句式，才启用自动结构化
    """
    if not content:
        return content

    # 统一换行
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    lines = content.splitlines()

    # 如果用户已经手写 Markdown 标题，则不做任何处理，完全尊重原文
    if any(re.match(r"^\s*#+\s+", line) for line in lines):
        return content

    # 统计是否满足"讲话稿结构"特征，避免普通材料被误改
    top_heading_pattern = re.compile(r"^\s*[一二三四五六七八九十]{1,3}、")
    # 子层级标题模式：例如「（一）主要做法」「（二）下步打算」
    sub_heading_pattern = re.compile(r"^\s*（[一二三四五六七八九十]{1,3}）")
    bullet_sentence_pattern = re.compile(r"^\s*[一二三四五六七八九十][是要]")

    top_heading_count = sum(1 for line in lines if top_heading_pattern.match(line or ""))
    bullet_sentence_count = sum(1 for line in lines if bullet_sentence_pattern.match(line or ""))

    if top_heading_count < 2 and bullet_sentence_count < 2:
        # 特征不明显，当成普通文章，不启用自动结构化
        return content

    processed_lines = []

    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()

        # 空行原样保留（交给 deep_clean_content 做后续规范化）
        if not stripped:
            processed_lines.append(line)
            continue

        # 1）总分结构：「一、心路历程：……」「二、成长感悟：……」
        if top_heading_pattern.match(stripped):
            # 直接作为一级标题输出（后续渲染时再按公文样式展示）
            processed_lines.append("# " + stripped)
            continue

        # 1.1）子层级结构：「（一）主要做法」「（二）下步打算」
        if sub_heading_pattern.match(stripped):
            # 作为二级标题输出
            processed_lines.append("## " + stripped)
            continue

        # 2）阶段型小标题：「第一阶段，在……阶段。后文……」
        #    只将首句（以全角句号"。"结尾）加粗，后面的正文保持普通段落
        m_phase = re.match(r"^(第[一二三四五六七八九十]{1,3}阶段[^。]*。)(.*)$", stripped)
        if m_phase:
            head = m_phase.group(1).strip()
            tail = m_phase.group(2).lstrip()
            if tail:
                processed_lines.append(f"**{head}**{tail}")
            else:
                processed_lines.append(f"**{head}**")
            continue

        # 3）条目型句式：「一是突出党性。……」「二是自我超越。……」
        #    同样仅加粗首句，保持后文原样
        m_bullet = re.match(r"^([一二三四五六七八九十][是要][^。]*。)(.*)$", stripped)
        if m_bullet:
            head = m_bullet.group(1).strip()
            tail = m_bullet.group(2).lstrip()
            if tail:
                processed_lines.append(f"**{head}**{tail}")
            else:
                processed_lines.append(f"**{head}**")
            continue

        # 其它行保持不变
        processed_lines.append(line)

    return "\n".join(processed_lines)


def api_format_markdown():
    """
    在线格式整理 API：
    - 仅对传入的 Markdown 文本执行 auto_structure_speech_markdown + deep_clean_content
    - 不做数据库写入，只返回整理后的内容，供前端在编辑页原地替换
    """
    data = request.get_json(silent=True) or {}
    raw_content = data.get("content", "")

    try:
        structured_raw = auto_structure_speech_markdown(raw_content)
        cleaned = deep_clean_content(structured_raw)
    except Exception as e:
        return jsonify(
            {
                "success": False,
                "message": f"格式整理失败: {str(e)}",
            }
        ), 500

    return jsonify(
        {
            "success": True,
            "content": cleaned,
        }
    )
