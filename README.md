# CopyEZ - 数字化公文素材工作台

一个基于 Flask 的个人公文素材管理平台，支持长文笔记、语录摘抄、知识图谱、Markdown 渲染与 Word 导出。

## 技术栈

| 层级 | 技术 |
|------|------|
| Web 框架 | Flask 3.x |
| ORM | SQLAlchemy（经典模式） |
| 数据库 | SQLite（`instance/copyez.db`） |
| 模板引擎 | Jinja2 |
| 前端 | 原生 HTML / CSS / JavaScript |

## 项目结构

```
CopyEZ/
├── app/
│   ├── extensions.py          # Flask 扩展统一入口（db 实例）
│   ├── models/                # 数据库模型
│   │   ├── note.py            # Note 素材模型
│   │   ├── memo.py            # Memo 随心记模型
│   │   ├── category.py        # 自定义分类模型
│   │   ├── ledger_account.py  # 账户模型
│   │   ├── ledger_category.py # 收支分类模型
│   │   └── ledger_transaction.py # 交易记录模型
│   ├── modules/               # 功能模块（各 Blueprint）
│   │   ├── copyez/           # CopyEZ 核心模块
│   │   │   ├── note_pages.py  # 笔记页面（列表/阅读/新建/编辑）
│   │   │   ├── note_api.py    # 笔记 CRUD API
│   │   │   ├── note_queries.py # 笔记查询 API（搜索/归档/分类过滤）
│   │   │   ├── note_meta.py   # 笔记元数据 API（批注/深度思考）
│   │   │   ├── note_relations.py # 笔记关联图谱 API
│   │   │   ├── memo.py        # 随心记 API（创建/删除/置顶/星标）
│   │   │   ├── memos.py       # 随心记 Blueprint
│   │   │   ├── quote.py       # 语录摘抄 API
│   │   │   ├── quotes.py      # 语录本 Blueprint
│   │   │   ├── category.py    # 分类/标签 API
│   │   │   ├── dashboard.py   # 仪表盘/热力图 API
│   │   │   ├── formatting.py  # Markdown 格式化 API
│   │   │   ├── upload_utils.py # 图片上传工具
│   │   │   ├── search.py      # 搜索页面
│   │   │   ├── guide.py       # 使用手册页面
│   │   │   └── scrape.py     # 内容抓取 Blueprint
│   │   ├── ledger/            # LedgerEZ 账本模块
│   │   ├── portal/            # 首页入口模块
│   │   └── orc_documents/     # 文档扫描入口
│   ├── routes/                # 页面路由统一导出
│   └── utils/                 # 工具函数
│       ├── datetime_utils.py  # 北京时间工具
│       ├── filters.py         # Jinja2 模板过滤器
│       ├── text_utils.py      # 文本处理工具
│       ├── content_utils.py   # 内容清洗/渲染工具
│       ├── presets.py         # 预置分类/标签配置
│       ├── log_utils.py       # 日志工具（带自动轮转）
│       └── scraper/           # 网页抓取模块
│           ├── base.py
│           ├── manager.py
│           └── wechat.py      # 微信公众号适配
├── static/                    # 静态资源
│   ├── style.css             # 主样式
│   ├── main.js               # 主脚本
│   ├── annotations.js        # 批注功能
│   └── category-selector.js   # 分类选择器
├── templates/                 # Jinja2 模板
│   ├── base.html             # 基础模板
│   ├── index.html            # 素材列表页
│   ├── note.html             # 素材阅读页
│   ├── new.html              # 新建素材页
│   ├── edit.html             # 编辑素材页
│   ├── search.html           # 搜索结果页
│   ├── guide.html            # 使用手册页
│   ├── memos.html            # 随心记页面
│   ├── my_quotes.html       # 语录本页面
│   ├── portal.html          # 首页
│   ├── landing.html         # 落地页
│   └── ledger/              # 账本模板
├── scripts/                  # 维护脚本
├── fonts/                   # 字体资源
├── images/                  # 图片资源
├── instance/                # SQLite 数据库（自动创建）
├── logs/                    # 运行时日志（自动轮转）
├── app.py                  # Flask 应用入口（288 行）
└── config.py               # 运行时配置
```

## 路由总览

### 页面路由

| URL | 端点 | 说明 |
|-----|------|------|
| `/` | `index` | 首页 |
| `/guide` | `guide` | 使用手册 |
| `/ORC_documents` | `orc_documents` | 文档扫描入口 |
| `/search` | `search_page` | 搜索页 |
| `/notes` | `notes` | 素材列表 |
| `/note/<id>` | `view_note` | 素材阅读 |
| `/new` | `new_note` | 新建素材 |
| `/edit/<id>` | `edit_note` | 编辑素材 |
| `/memos` | `memos_page` | 随心记 |
| `/my_quotes` | `my_quotes_page` | 语录本 |
| `/ledger/` | `ledger.ledger_home` | 记账本首页 |
| `/ledger/overview` | `ledger.ledger_overview` | 账单概览 |

### API 路由

| URL | 方法 | 端点 | 说明 |
|-----|------|------|------|
| `/api/notes` | GET/POST | `api_notes` | 笔记列表/创建 |
| `/api/notes/<id>` | GET/PUT/DELETE | `note_detail` | 笔记详情/更新/删除 |
| `/api/notes/<id>/annotations` | GET/PUT | `note_annotations` | 批注 |
| `/api/notes/<id>/thought` | PUT | `note_thought` | 深度思考 |
| `/api/notes/search` | GET | `search_notes` | 搜索 |
| `/api/notes/by_category` | GET | `notes_by_category` | 分类过滤 |
| `/api/notes/archive` | GET | `archive_notes` | 归档列表 |
| `/api/notes/<id>/related` | GET | `related_notes` | 关联素材 |
| `/api/notes/<id>/outline` | GET | `note_outline` | 大纲提炼 |
| `/api/memos` | GET/POST | `api_memos` | 随心记列表/创建 |
| `/api/memos/<id>/pin` | PUT | `api_memo_pin` | 置顶 |
| `/api/memos/<id>/star` | PUT | `api_memo_star` | 星标 |
| `/api/memos/<id>` | PUT/DELETE | `api_memo_detail` | 更新/删除 |
| `/api/format_markdown` | POST | `api_format_markdown` | Markdown 格式化 |
| `/api/upload_image` | POST | `upload_image` | 图片上传 |
| `/api/scrape` | POST | `scrape_content` | 内容抓取 |
| `/scrape/wechat` | GET | `scrape_wechat` | 微信抓取页 |
| `/ledger/api/accounts` | GET/POST | `ledger_api.get_accounts` | 账户列表/创建 |
| `/ledger/api/accounts/<id>` | PUT/DELETE | `ledger_api.update_account` | 更新/删除账户 |
| `/ledger/api/categories` | GET/POST | `ledger_api.get_categories` | 收支分类列表/创建 |
| `/ledger/api/transactions` | GET/POST | `ledger_api.get_transactions` | 交易列表/创建 |
| `/ledger/api/transactions/<id>` | PUT/DELETE | `ledger_api.update_transaction` | 更新/删除交易 |
| `/ledger/api/stats/monthly` | GET | `ledger_api.monthly_stats` | 月度统计 |
| `/ledger/api/stats/trend` | GET | `ledger_api.monthly_trend` | 近月趋势 |
| `/api/categories` | GET | `get_categories` | 分类列表 |
| `/api/tags` | GET | `get_tags` | 标签列表 |
| `/api/activity_stats` | GET | `api_activity_stats` | 热力图数据 |
| `/api/tag_collection` | GET | `api_tag_collection` | 标签收集 |
| `/api/format_markdown` | POST | `api_format_markdown` | Markdown 格式化 |
| `/api/upload_image` | POST | `upload_image` | 图片上传 |
| `/api/scrape` | POST | `scrape_content` | 内容抓取 |
| `/scrape/wechat` | GET | `scrape_wechat` | 微信抓取页 |

## 数据模型

### Note（素材）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | 主键 |
| `title` | String(200) | 标题 |
| `content` | Text | 正文（Markdown） |
| `created_at` | DateTime | 创建时间 |
| `updated_at` | DateTime | 更新时间 |
| `mainCategory` | String(50) | 一级分类（全文/框架/短文摘要） |
| `subCategory` | String(100) | 二级分类 |
| `tags_json` | Text | 三级标签（JSON 数组） |
| `publishDate` | String(10) | 发布日期 |
| `sourceUrl` | String(500) | 原文链接 |
| `annotations` | Text | 批注（JSON） |
| `global_thought` | Text | 深度思考 |

### Memo（随心记）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | 主键 |
| `content` | Text | 内容 |
| `image_path` | String(200) | 图片路径 |
| `created_at` | DateTime | 创建时间 |
| `is_pinned` | Boolean | 是否置顶 |
| `is_starred` | Boolean | 是否星标 |
| `pinned_at` | DateTime | 置顶时间 |
| `starred_at` | DateTime | 星标时间 |

### CustomCategory（自定义分类）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | 主键 |
| `name` | String(100) | 分类名称 |
| `main_category` | String(50) | 所属一级分类 |

### Account（账户）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | 主键 |
| `name` | String(50) | 账户名称 |
| `account_type` | String(20) | 类型（cash/bank/alipay/wechat） |
| `initial_balance` | Numeric(12,2) | 初始余额 |
| `balance` | Numeric(12,2) | 当前余额 |
| `icon` | String(30) | 图标名 |
| `color` | String(7) | 主题色 |
| `is_active` | Boolean | 是否启用 |

### LedgerCategory（收支分类）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | 主键 |
| `name` | String(50) | 分类名称 |
| `category_type` | String(10) | 类型（income/expense） |
| `icon` | String(30) | 图标名 |
| `color` | String(7) | 主题色 |

### Transaction（交易记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | 主键 |
| `account_id` | Integer | 账户 ID |
| `category_id` | Integer | 分类 ID |
| `amount` | Numeric(12,2) | 金额 |
| `transaction_type` | String(10) | 类型（income/expense） |
| `note` | String(200) | 备注 |
| `transaction_date` | Date | 交易日期 |

## 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python app.py
# 访问 http://127.0.0.1:5000
```

## 配置

运行时配置位于 `config.py`，可通过环境变量覆盖：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `COPYEZ_SECRET_KEY` | `copyez-secret-key` | Flask 密钥 |
| `DATABASE_URL` | SQLite 绝对路径 | 数据库路径 |

## 核心功能

### 素材管理
- **长文笔记**：Markdown 编辑、公文 A4 排版、批注、大纲提炼、关联图谱
- **随心记**：轻量级随手记，支持置顶/星标
- **语录本**：摘抄引用、跳转原文、Word 导出

### 智能工具
- **内容抓取**：一键从微信公众号等网页提取标题与正文
- **格式清洗**：自动识别 Word 字体层级，生成结构化 Markdown
- **知识图谱**：基于分类与标签的关联文章推荐

### 安全功能
- **开门见锁**：沉浸式屏幕锁定，保障素材私密性
- **数据自修复**：启动时自动检测并补全数据库字段

### LedgerEZ 个人记账
- **账户管理**：现金、银行卡、支付宝、微信支付等多账户支持
- **收支记录**：支持收入/支出分类、备注、日期记录
- **月度统计**：本月收支汇总、结余计算
- **支出分布**：甜甜圈图表展示各类目支出占比
- **近月趋势**：近6个月收支双柱状图对比

## 变更记录

### [2.3.0] - 2026-05-10
### 项目结构整理
- **根目录清理**：删除空 `routes/`、`utils/`、`copyez.db`（空文件）
- **日志迁移**：新建 `logs/` 目录，`notes_error.log` 移入其中
- **日志轮转**：`app/utils/log_utils.py` 实现自动轮转，超过 200 行自动截断旧日志
- **文档重构**：`CHANGELOG.md` 改写为 `README.md`，补充完整项目结构、路由总览、数据模型文档
- **依赖整合**：`utils/scraper/` 移入 `app/utils/scraper/`，统一使用 `app.utils` 命名空间
- **配置精简**：`config.py` 仅保留运行时配置，预置数据统一由 `app/utils/presets.py` 提供
- **导入统一**：修复 `upload_utils.py`、`category.py`、`scrape.py` 等模块的导入路径
### LedgerEZ 个人记账
- **数据模型**：新增 `Account`、`LedgerCategory`、`Transaction` 三个模型
- **API 接口**：完整的账户/分类/交易 CRUD + 月度统计 + 近月趋势 API
- **记账主页**：`templates/ledger/index.html`，顶部月结余卡片、账户横滑条、收支流水列表、底部 FAB 记账弹窗
- **账单概览**：`templates/ledger/overview.html`，甜甜圈支出分布图、6个月趋势柱状图、账户总资产卡片
- **UI 设计**：移动优先，绿色渐变主题，DM Sans 字体，底部弹窗表单，Toast 反馈

### [2.2.1] - 2026-03-10
- guide page: 添加功能介绍
- 解析 Word 格式：从 Word 复制的内容会自动识别并格式化
- Memo 支持"置顶/星标"
- **UI 视觉增强**：重构置顶与星标样式
- **智能粘贴 2.0**：新增 Word 字体深度扫描

### [2.2.0] - 2026-03-10
- **智能素材抓取系统**：支持微信公众号文章一键提取
- **微信排版适配**：段落级拆分、自动小标题识别

### [2.1.0] - 2026-03-10
- **首页重构**：热力图居中展示
- **动态侧栏**：历史时间轴与使用手册改为吸附式
- **沉浸式阅读**：移动端对标微信公众号体验

### [2.0.0] - 2026-03-09
- **核心模块上线**：随心记、语录本双核心功能
- **数据看板**：GitHub 风格贡献热力图
- **安全锁定**：开门见锁沉浸式锁定系统
