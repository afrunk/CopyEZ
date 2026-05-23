#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RenovaMate 装修进度页面结构测试

测试 progress.html 中的看板结构是否符合预期：
1. 8 个阶段
2. 每个阶段 4 个状态容器
3. taskStage 下拉选项 value 是英文枚举
4. taskStatus 下拉选项 value 是英文枚举
5. 弹窗存在
6. 引用 renovamate.js
"""

import os
import sys

# 设置输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 阶段枚举
STAGES = ['design', 'demolition', 'water', 'mud', 'wood', 'paint', 'install', 'soft']

# 状态枚举
STATUSES = ['pending', 'ongoing', 'review', 'done']

def check_html_structure(html_content):
    """检查 HTML 结构"""
    errors = []
    warnings = []

    # 1. 检查 8 个阶段
    for stage in STAGES:
        stage_count = html_content.count(f'data-stage="{stage}"')
        if stage_count < 4:  # 每个阶段应该有 4 个状态容器
            errors.append(f"阶段 '{stage}' 的状态容器数量不足 (期望 4, 实际 {stage_count})")

    # 2. 检查 4 个状态
    for status in STATUSES:
        status_count = html_content.count(f'data-status="{status}"')
        if status_count < 8:  # 每个状态应该有 8 个阶段容器
            errors.append(f"状态 '{status}' 的阶段容器数量不足 (期望 8, 实际 {status_count})")

    # 3. 检查 taskStage 下拉选项
    stage_options = [
        '<option value="design">',
        '<option value="demolition">',
        '<option value="water">',
        '<option value="mud">',
        '<option value="wood">',
        '<option value="paint">',
        '<option value="install">',
        '<option value="soft">',
    ]
    for opt in stage_options:
        if opt not in html_content:
            errors.append(f"taskStage 下拉选项缺少: {opt}")

    # 4. 检查 taskStatus 下拉选项
    status_options = [
        '<option value="pending">',
        '<option value="ongoing">',
        '<option value="review">',
        '<option value="done">',
    ]
    for opt in status_options:
        if opt not in html_content:
            errors.append(f"taskStatus 下拉选项缺少: {opt}")

    # 5. 检查弹窗
    if 'id="taskModal"' not in html_content:
        errors.append("缺少 taskModal 弹窗")
    if 'id="editTaskModal"' not in html_content:
        errors.append("缺少 editTaskModal 弹窗")

    # 6. 检查引用 renovamate.js
    if 'renovamate.js' not in html_content:
        warnings.append("页面未引用 renovamate.js")

    # 7. 检查 kanban-board 结构
    if 'class="kanban-board"' not in html_content:
        errors.append("缺少 kanban-board 结构")
    if 'class="kanban-group' not in html_content:
        errors.append("缺少 kanban-group 结构")
    if 'class="kanban-column"' not in html_content:
        errors.append("缺少 kanban-column 结构")

    # 8. 检查保存按钮
    if 'onclick="saveProgressTask()"' not in html_content:
        warnings.append("缺少 saveProgressTask() 调用")
    if 'onclick="saveEditedTask()"' not in html_content:
        warnings.append("缺少 saveEditedTask() 调用")

    return errors, warnings


def main():
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    progress_html = os.path.join(project_root, 'templates', 'decoration', 'progress.html')

    print("=" * 60)
    print("RenovaMate 装修进度页面结构测试")
    print("=" * 60)
    print()

    if not os.path.exists(progress_html):
        print(f"❌ 错误: 文件不存在: {progress_html}")
        sys.exit(1)

    print(f"📄 检查文件: {progress_html}")
    print()

    with open(progress_html, 'r', encoding='utf-8') as f:
        html_content = f.read()

    errors, warnings = check_html_structure(html_content)

    # 打印结果
    print("✅ 检查项:")
    print("  - 8 个装修阶段结构")
    print("  - 每个阶段 4 个状态容器")
    print("  - taskStage 下拉选项 value 为英文枚举")
    print("  - taskStatus 下拉选项 value 为英文枚举")
    print("  - 新建/编辑任务弹窗存在")
    print("  - kanban-board 结构存在")
    print()

    if warnings:
        print("⚠️  警告:")
        for w in warnings:
            print(f"  - {w}")
        print()

    if errors:
        print("❌ 错误:")
        for e in errors:
            print(f"  - {e}")
        print()
        print("=" * 60)
        print("测试结果: ❌ 失败")
        print("=" * 60)
        sys.exit(1)
    else:
        print("✅ 所有检查通过!")
        print()
        print("详细验证:")
        print(f"  - 8 个阶段: {', '.join(STAGES)}")
        print(f"  - 4 个状态: {', '.join(STATUSES)}")
        print(f"  - 新建任务弹窗: ✓")
        print(f"  - 编辑任务弹窗: ✓")
        print(f"  - kanban-board: ✓")
        print()
        print("=" * 60)
        print("测试结果: ✅ 通过")
        print("=" * 60)
        sys.exit(0)


if __name__ == '__main__':
    main()
