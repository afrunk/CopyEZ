# Flask Auto Refactor Skill

## 目标

你是一个 Flask 项目自动重构代理。

你的任务是帮助当前 Flask 多项目工作台进行渐进式模块化重构。

**核心原则：分析所有情况后，执行一个阶段，然后停止。**

---

## 快速命令模式

当用户输入简写命令时，执行对应操作：

| 命令 | 含义 |
|------|------|
| `1` | 分析 + 规划 + 执行 + 验证 + 报告 + 停止 |
| `2` | 只验证，不改代码 |
| `3` | 只审计，不改代码 |
| `0` | 停止并总结 |

---

## 命令 1 完整执行流程

### 步骤 1：扫描 app.py

扫描 `app.py`，找到下一个未迁移的模块或函数。

**迁移完成标志：**
- 函数已移到 `app/modules/*/` 目录
- Blueprint 已在 `app/modules/*/__init__.py` 中定义
- 路由已在 `app/modules/*/routes.py` 中定义
- `app.py` 中不再包含该函数的定义

**扫描策略：**
1. 从 app.py 底部向上扫描（越靠后越可能是新代码）
2. 识别独立的函数块
3. 识别 `@app.route` 装饰的函数
4. 识别工具函数（如 render_content, ensure_schema）

### 步骤 2：分析（关键！）

对每个候选模块进行完整分析：

```text
模块：[模块名]
位置：app.py 第 X 行 - 第 Y 行

依赖分析：
  ├─ 被谁引用：
  │   - /api/xxx (通过 url_for)
  │   - 其他函数
  │
  ├─ 引用谁：
  │   - from app.extensions import db
  │   - from app.models import Xxx
  │   - 其他模块
  │
  └─ 外部依赖：
      - utils.scraper.manager
      - docx 库
      - bleach 库

风险评估：
  ├─ 迁移风险：高/中/低
  ├─ 影响范围：小/中/大
  ├─ 回滚难度：易/中/难
  └─ 潜在问题：
      - 循环导入风险
      - 路径冲突
      - 测试覆盖不足

迁移方案：
  ├─ 方案 A：[描述]
  │   优点：...
  │   缺点：...
  │
  └─ 方案 B：[描述]
      优点：...
      缺点：...
```

### 步骤 3：执行

根据分析结果，执行迁移：

**如果只有一个可行方案：**
- 直接执行
- 记录修改

**如果有多个可行方案：**
- 选择风险最低的方案
- 执行并记录

**如果风险太高且无好方案：**
- 输出完整分析
- 提出建议
- 跳过此模块，尝试下一个

### 步骤 4：验证

必须验证所有基础路径：

```
GET /
GET /notes
GET /search
GET /guide
GET /ledger/
GET /ledger/overview
GET /api/memos
GET /api/categories
GET /api/tags
GET /api/activity_stats
```

**如果涉及上传：**
```
POST /api/upload_image (test.exe -> 应拒绝)
POST /api/memo/upload_image (test.exe -> 应拒绝)
```

**如果涉及格式化：**
```
POST /api/format_markdown
```

### 步骤 5：报告

输出标准报告（见下方格式）。

### 步骤 6：停止

报告完成后立即停止。

---

## 当前项目结构

### CopyEZ

负责：
- `/notes` - 笔记页面
- `/search` - 搜索页面
- `/guide` - 指南页面
- Memo - 随心记 API
- Quote - 摘抄语录
- Category / Tags - 分类标签
- Dashboard - 活动统计
- Markdown formatting - 格式化
- Upload / Image - 上传图片
- Export / Word - Word 导出
- Scrape - 微信抓取

### LedgerEZ

负责：
- `/ledger/` - 账本主页
- `/ledger/overview` - 账本概览

### Portal

负责：
- `/` - 首页工作台
- `/ORC_documents` - landing 页面

---

## 已完成迁移

以下函数/模块已迁移到 `app/modules/` 或 `app/utils/`：

- Memo API 相关函数
- Category / Tags API
- Activity Stats / Dashboard API
- Format Markdown API
- upload_image 函数
- allowed_image 工具函数
- urlquote_filter 模板过滤器
- estimate_text_length 文本处理工具
- collect_quote_items 摘抄语录函数
- Ledger 路由
- Search 路由
- Portal 路由

---

## 报告格式

```text
阶段：[阶段编号]
执行内容：[具体做了什么]

分析过程：
  依赖：[列出关键依赖]
  风险：[高/中/低]
  方案：[选择的方案]

修改文件：[列表]
新增文件：[列表]
删除文件：[列表]
URL 是否变化：是 / 否
endpoint 是否变化：是 / 否
JSON 是否变化：是 / 否
模板是否修改：是 / 否
前端 JS 是否修改：是 / 否
数据库是否修改：是 / 否
验证结果：[PASS / FAIL / RISK]
下一阶段建议：[建议]

已停止，等待用户输入 1 继续。
```

---

## 基本约束

除非用户明确指定，否则禁止：

- 修改数据库结构
- 修改模板
- 修改前端 JS
- 改变 URL
- 改变 endpoint
- 改变 JSON 响应结构
- 启用 create_app()
- 改变 python app.py 启动方式

**允许：**
- 迁移任何模块（包括 Quote、Notes、Export、Scrape）
- 只要分析清楚、验证通过

---

## db 导入规范

所有代码必须使用：

```python
from app.extensions import db
```

---

## 验证失败处理

如果验证失败：

```text
STOP: 验证失败

失败项：[列出失败的 URL/API]
原因：[分析原因]
建议：[最小修复方案]

已停止，等待用户输入 1 继续。
```

---

## 使用方式

在 Cursor 中输入：

```text
1
```

执行：扫描 → 分析 → 迁移 → 验证 → 报告 → 停止
