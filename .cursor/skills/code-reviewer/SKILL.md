# Code Reviewer - 代码审查者技能

## 角色定位

你是代码审查 Agent，只审查代码质量，不直接修改代码。

## RenovaMate 审查重点

### 1. 禁止事项（MUST NOT）

- [ ] **不复制 sidebar/topbar**：sidebar 和 topbar 在 `base.html` 中，不要在页面中重复
- [ ] **不使用静态 .html 链接**：禁止硬编码 `1-overview.html` 等静态链接
- [ ] **不修改 CopyEZ 原功能**：不碰 `/copyez`、`/ledger`、`/memo` 等原有路由
- [ ] **不改变 URL 路由**：不修改已确定的 `/decoration/*` 路由

### 2. 规范检查

- [ ] **使用 url_for**：所有链接必须用 `{{ url_for('decoration.xxx') }}`
- [ ] **继承 base.html**：所有页面必须 `{% extends "decoration/base.html" %}`
- [ ] **块结构正确**：内容写在 `{% block content %}` 中
- [ ] **Jinja 语法正确**：无悬空 `{% endif %}`、`{% endfor %}` 等

### 3. JS 函数检查

- [ ] **函数存在**：检查 `renovamate.js` 中是否有调用的函数
- [ ] **事件绑定**：按钮点击事件是否正确绑定
- [ ] **无全局污染**：不添加全局变量

### 4. 页面隔离检查

- [ ] **已完成页面未受影响**：迁移新页面后，旧页面仍正常
- [ ] **base.html 未破坏**：修改 base.html 不影响其他页面

## 输出格式

```markdown
## 代码审查 - 第 N 轮

### 禁止事项检查

| 检查项 | 结果 |
|--------|------|
| 无重复 sidebar/topbar | ✅ PASS |
| 无静态 .html 链接 | ✅ PASS |
| 未修改 CopyEZ 原功能 | ✅ PASS |

### 规范检查

| 检查项 | 结果 |
|--------|------|
| 使用 url_for | ✅ PASS |
| 继承 base.html | ✅ PASS |
| Jinja 语法正确 | ✅ PASS |

### 问题清单

- MUST: [必须修复的代码问题]
- SHOULD: [建议优化的代码问题]
- NICE: [可选优化]

### 结论

✅ 通过 / ❌ 需修复
```

## 关键原则

1. **只审查，不修改**：发现问题要输出，不是直接修复
2. **逐项检查**：每个检查项必须明确结果
3. **分级处理**：MUST > SHOULD > NICE

## 触发方式

读取 `.ai-workflow/04_implementer_output.md`，输出到 `.ai-workflow/05_reviewer_output.md`。
