# D1：数据库模型设计方案

> 本文档为 RenovaMate 数据库模型设计文档。
> 由多 Agent 工作流生成（Project Manager → Project Architect → Code Implementer）。
> **仅作为设计方案参考，不包含任何代码实现。**
> 等待确认后再进入代码实现阶段（D2）。

---

## 1. 设计原则

1. **复用现有技术栈**：使用 SQLAlchemy 经典模式（`db.Model`），通过 `app.extensions.db` 实例管理。
2. **命名隔离**：所有模型使用 `Decoration` 前缀，避免与 CopyEZ 现有模型冲突。
3. **第一版优先**：优先实现最小可用功能，可选字段标注"后续再做"。
4. **空数据友好**：所有页面默认显示空状态，不预设演示数据。

---

## 2. 模型总览

| 模型 | 表名 | 第一版 | 说明 |
|------|------|--------|------|
| `DecorationProject` | `decoration_projects` | ✅ | 装修项目 |
| `DecorationCategoryGroup` | `decoration_category_groups` | ✅ | 分类大类 |
| `DecorationCategory` | `decoration_categories` | ✅ | 子分类 |
| `CompareItem` | `compare_items` | ✅ | 分类方案 |
| `Expense` | `expenses` | ✅ | 实际花费 |
| `ProgressTask` | `progress_tasks` | ✅ | 装修任务 |
| `DecorationNote` | `decoration_notes` | ✅ | 手册记录 |
| `DecorationNoteImage` | `decoration_note_images` | ✅ | 手册图片 |
| `CompareItemValue` | — | ❌ 后续 | 动态字段值（第一版用固定字段） |
| `Attachment` | — | ❌ 后续 | 通用附件（第一版用字段路径） |

---

## 3. 模型详细设计

---

### 3.1 DecorationProject（装修项目）

**用途**：装修项目总览，存储项目基本信息、预算、当前阶段。

**表名**：`decoration_projects`

**关系图**：

```
DecorationProject (1)
  ├── (N) DecorationCategoryGroup
  ├── (N) DecorationCategory
  ├── (N) ProgressTask
  ├── (N) Expense
  └── (N) DecorationNote
```

**字段定义**：

| 字段名 | 类型 | Nullable | 默认值 | 说明 |
|--------|------|---------|--------|------|
| `id` | `Integer` | ❌ | 自增 | 主键 |
| `name` | `String(100)` | ❌ | — | 项目名称，如"新房装修" |
| `area` | `String(20)` | ✅ | — | 面积，如"120㎡" |
| `style` | `String(50)` | ✅ | — | 装修风格，如"现代简约" |
| `current_stage` | `String(20)` | ✅ | — | 当前阶段，见阶段枚举（design/demolition/water/mud/wood/paint/install/soft） |
| `total_budget` | `Integer` | ✅ | `0` | 总预算（元），0 表示未设置 |
| `created_at` | `DateTime` | ❌ | `now_bj` | 创建时间 |
| `updated_at` | `DateTime` | ❌ | `now_bj` | 更新时间 |

**索引**：
- 主键索引：`id`
- 建议唯一索引：`name`（每个项目名称唯一）

---

## 统一阶段枚举（跨模型共用）

> 以下枚举值在 DecorationProject.current_stage、ProgressTask.stage、DecorationNote.stage 中**统一使用**，前端页面展示时映射为中文。

| 枚举值 | 中文展示 | 说明 |
|--------|----------|------|
| `design` | 设计阶段 | 量房、设计方案 |
| `demolition` | 拆改阶段 | 墙体拆改 |
| `water` | 水电阶段 | 水电改造、定位 |
| `mud` | 泥工阶段 | 瓷砖铺贴、防水 |
| `wood` | 木工阶段 | 吊顶、柜子 |
| `paint` | 油漆阶段 | 墙面油漆、木器漆 |
| `install` | 安装阶段 | 安装地板、门窗、灯具 |
| `soft` | 软装阶段 | 家具、窗帘、电器进场 |

---

### 3.2 DecorationCategoryGroup（分类大类）

**用途**：分类大类，如"设备系统"、"主材选择"、"施工项目"、"软装搭配"。

**表名**：`decoration_category_groups`

**关系图**：

```
DecorationProject (1) ──→ (N) DecorationCategoryGroup
DecorationCategoryGroup (1) ──→ (N) DecorationCategory
```

**字段定义**：

| 字段名 | 类型 | Nullable | 默认值 | 说明 |
|--------|------|---------|--------|------|
| `id` | `Integer` | ❌ | 自增 | 主键 |
| `project_id` | `Integer` | ❌ | — | 外键 → `decoration_projects.id`，级联删除 |
| `name` | `String(50)` | ❌ | — | 大类名称 |
| `icon` | `String(10)` | ✅ | "🏠" | Emoji 图标 |
| `description` | `String(255)` | ✅ | — | 说明描述 |
| `order` | `Integer` | ✅ | `0` | 排序序号，数字越小越靠前 |
| `enabled` | `Boolean` | ❌ | `True` | 是否启用，False 为禁用 |
| `created_at` | `DateTime` | ❌ | `now_bj` | 创建时间 |
| `updated_at` | `DateTime` | ❌ | `now_bj` | 更新时间 |

**索引**：
- 主键索引：`id`
- 外键索引：`project_id`
- 建议索引：`project_id + order`（按项目排序查询）

---

### 3.3 DecorationCategory（子分类）

**用途**：子分类，如"中央空调"、"瓷砖"、"水电"、"木工"。

**表名**：`decoration_categories`

**字段定义**：

| 字段名 | 类型 | Nullable | 默认值 | 说明 |
|--------|------|---------|--------|------|
| `id` | `Integer` | ❌ | 自增 | 主键 |
| `project_id` | `Integer` | ❌ | — | 外键 → `decoration_projects.id`，级联删除 |
| `group_id` | `Integer` | ❌ | — | 外键 → `decoration_category_groups.id`，级联删除 |
| `name` | `String(50)` | ❌ | — | 分类名称，如"中央空调" |
| `status` | `String(20)` | ❌ | "not-started" | 当前状态，见状态枚举 |
| `budget` | `Integer` | ✅ | `0` | 预算金额（元） |
| `selected_plan_id` | `Integer` | ✅ | — | 已选最终方案 ID → `compare_items.id`（可选）。删除 CompareItem 时，SQLAlchemy 外键配置 `ondelete='SET NULL'`，自动置为空，避免孤儿引用 |
| `view_mode` | `String(20)` | ❌ | "card" | 展示方式：card/table/list |
| `note` | `Text` | ✅ | — | 备注说明 |
| `created_at` | `DateTime` | ❌ | `now_bj` | 创建时间 |
| `updated_at` | `DateTime` | ❌ | `now_bj` | 更新时间 |

**状态枚举（`status`）**：

| 值 | 含义 | 对应前端 |
|----|------|----------|
| `not-started` | 未开始 | `status-not-started` |
| `comparing` | 比价中 | `status-comparing` |
| `selected` | 已选方案 | `status-selected` |
| `ongoing` | 进行中 | `status-ongoing` |
| `pending` | 待确认 | `status-pending` |

**索引**：
- 主键索引：`id`
- 外键索引：`project_id`、`group_id`
- 建议索引：`project_id + group_id`（按项目和大类查询子分类）

---

### 3.4 CompareItem（分类方案）

**用途**：分类的具体方案，如中央空调的大金 VRV-P 方案、约克 YES-smart 方案。

**表名**：`compare_items`

**设计决策**：第一版采用**固定字段**（共用一张表），不实现动态字段（CompareItemValue）。各分类共用同一套字段，分类特殊字段内容可存在 `note` 备注中。

**字段定义**：

| 字段名 | 类型 | Nullable | 默认值 | 说明 | 第一版 |
|--------|------|---------|--------|------|--------|
| `id` | `Integer` | ❌ | 自增 | 主键 | ✅ |
| `project_id` | `Integer` | ❌ | — | 外键 → `decoration_projects.id` | ✅ |
| `category_id` | `Integer` | ❌ | — | 外键 → `decoration_categories.id` | ✅ |
| `brand` | `String(50)` | ✅ | — | 品牌，如"大金" | ✅ |
| `model` | `String(50)` | ✅ | — | 型号，如"VRV-P" | ✅ |
| `power` | `String(20)` | ✅ | — | 匹数，如"6匹" | ✅ |
| `units` | `String(20)` | ✅ | — | 一拖几，如"一拖五" | ✅ |
| `price` | `Integer` | ✅ | `0` | 总价（元） | ✅ |
| `outdoor_unit_count` | `Integer` | ✅ | `0` | 外机数量 | ✅ |
| `indoor_unit_count` | `Integer` | ✅ | `0` | 内机数量 | ✅ |
| `efficiency_level` | `String(10)` | ✅ | — | 能效等级：一级/二级/三级 | ✅ |
| `warranty` | `String(20)` | ✅ | — | 保修年限，如"3年" | ✅ |
| `rating` | `Float` | ✅ | `0` | 推荐指数（0.0-5.0） | ✅ |
| `note` | `Text` | ✅ | — | 备注，可存分类特殊字段 | ✅ |
| `is_selected` | `Boolean` | ❌ | `False` | 是否为该分类的最终方案 | ✅ |
| `product_image` | `String(255)` | ✅ | — | 产品图片路径 | ❌ 后续 |
| `quote_image` | `String(255)` | ✅ | — | 报价单图片路径 | ❌ 后续 |
| `created_at` | `DateTime` | ❌ | `now_bj` | 创建时间 | ✅ |
| `updated_at` | `DateTime` | ❌ | `now_bj` | 更新时间 | ✅ |

**业务约束**：
- 每个 `category_id` 最多有 **1 条** `is_selected=True` 的记录
- 由应用层（事务/锁）保证，不依赖数据库唯一约束

**外键删除行为**：
- `selected_plan_id` 外键配置 `ondelete='SET NULL'`
- 当删除某条 CompareItem 记录时，如果它恰好是某分类的 `selected_plan_id`，该字段自动被置为 NULL，不会产生孤儿引用

**索引**：
- 主键索引：`id`
- 外键索引：`project_id`、`category_id`
- 建议索引：`category_id + is_selected`（查询某分类的已选方案）

---

### 3.5 Expense（实际花费）

**用途**：实际花费记录，对应预算控制页的支出流水。

**表名**：`expenses`

**字段定义**：

| 字段名 | 类型 | Nullable | 默认值 | 说明 |
|--------|------|---------|--------|------|
| `id` | `Integer` | ❌ | 自增 | 主键 |
| `project_id` | `Integer` | ❌ | — | 外键 → `decoration_projects.id`，级联删除 |
| `category_id` | `Integer` | ✅ | — | 外键 → `decoration_categories.id`（可选，关联分类） |
| `name` | `String(100)` | ❌ | — | 支出名称，如"水电一期付款" |
| `amount` | `Integer` | ❌ | `0` | 金额（元），正整数 |
| `expense_date` | `Date` | ✅ | — | 支出日期 |
| `payment_method` | `String(20)` | ✅ | — | 支付方式，见枚举 |
| `payee` | `String(100)` | ✅ | — | 收款方/商家 |
| `receipt_image` | `String(255)` | ✅ | — | 票据图片路径 |
| `note` | `Text` | ✅ | — | 备注 |
| `created_at` | `DateTime` | ❌ | `now_bj` | 创建时间 |
| `updated_at` | `DateTime` | ❌ | `now_bj` | 更新时间 |

**支付方式枚举（`payment_method`）**：

| 值 | 含义 |
|----|------|
| `wechat` | 微信支付 |
| `alipay` | 支付宝 |
| `bank_transfer` | 银行转账 |
| `cash` | 现金 |
| `other` | 其他 |

**索引**：
- 主键索引：`id`
- 外键索引：`project_id`、`category_id`
- 建议索引：`project_id + expense_date`（按项目和时间查询花费）

---

### 3.6 ProgressTask（装修任务）

**用途**：装修进度任务，对应进度管理 Kanban 面板的卡片。

**表名**：`progress_tasks`

**字段定义**：

| 字段名 | 类型 | Nullable | 默认值 | 说明 |
|--------|------|---------|--------|------|
| `id` | `Integer` | ❌ | 自增 | 主键 |
| `project_id` | `Integer` | ❌ | — | 外键 → `decoration_projects.id`，级联删除 |
| `category_id` | `Integer` | ✅ | — | 外键 → `decoration_categories.id`（可选，关联分类） |
| `name` | `String(100)` | ❌ | — | 任务名称 |
| `description` | `Text` | ✅ | — | 任务描述 |
| `stage` | `String(20)` | ❌ | — | 所属阶段，见阶段枚举 |
| `status` | `String(20)` | ❌ | "pending" | 任务状态，见状态枚举 |
| `assignee` | `String(50)` | ✅ | — | 负责人 |
| `due_date` | `Date` | ✅ | — | 截止日期 |
| `budget` | `Integer` | ✅ | `0` | 任务预算（元） |
| `created_at` | `DateTime` | ❌ | `now_bj` | 创建时间 |
| `updated_at` | `DateTime` | ❌ | `now_bj` | 更新时间 |

**阶段枚举（`stage`）**：使用统一阶段枚举（design/demolition/water/mud/wood/paint/install/soft），见"统一阶段枚举"章节。

**任务状态枚举（`status`）**：

| 值 | 含义 | 对应 Kanban 列 |
|----|------|---------------|
| `pending` | 待开始 | 待开始 |
| `ongoing` | 进行中 | 进行中 |
| `review` | 待验收 | 待验收 |
| `done` | 已完成 | 已完成 |

**索引**：
- 主键索引：`id`
- 外键索引：`project_id`、`category_id`
- 建议索引：`project_id + stage + status`（按项目和阶段+状态查询任务）

---

### 3.7 DecorationNote（装修手册记录）

**用途**：装修手册/装修笔记记录，包含决策、灵感、图片、链接、避坑、门店沟通等。

**表名**：`decoration_notes`

**字段定义**：

| 字段名 | 类型 | Nullable | 默认值 | 说明 |
|--------|------|---------|--------|------|
| `id` | `Integer` | ❌ | 自增 | 主键 |
| `project_id` | `Integer` | ❌ | — | 外键 → `decoration_projects.id`，级联删除 |
| `title` | `String(200)` | ❌ | — | 记录标题 |
| `content` | `Text` | ✅ | — | 记录正文内容 |
| `stage` | `String(20)` | ❌ | — | 所属阶段，见阶段枚举（design/.../soft） |
| `source_url` | `String(500)` | ✅ | — | 来源链接 |
| `tags` | `Text` | ✅ | — | 标签（JSON 数组格式，如 `["中央空调", "吊顶"]`），统一使用 JSON 数组 |
| `task_id` | `Integer` | ✅ | — | 外键 → `progress_tasks.id`（关联任务） |
| `category_id` | `Integer` | ✅ | — | 外键 → `decoration_categories.id`（关联分类） |
| `created_at` | `DateTime` | ❌ | `now_bj` | 创建时间 |
| `updated_at` | `DateTime` | ❌ | `now_bj` | 更新时间 |

**标签处理**：
- 统一使用 `tags` 字段存储 JSON 数组，如 `["中央空调", "吊顶"]`
- 使用 `Text` 类型存储 JSON 字符串
- 辅助函数：`get_tags_list()` / `set_tags_list()` 解析 JSON
- 不保留冗余字段（移除旧的逗号分隔字符串格式）

**关联关系**：
- N 条手册记录可关联 0 或 1 个任务（`task_id`）
- N 条手册记录可关联 0 或 1 个分类（`category_id`）

**索引**：
- 主键索引：`id`
- 外键索引：`project_id`、`task_id`、`category_id`
- 建议索引：`project_id + stage`（按项目和阶段查询手册记录）

---

### 3.8 DecorationNoteImage（手册图片）

**用途**：装修手册记录的图片附件，支持多图。

**表名**：`decoration_note_images`

**关系图**：

```
DecorationNote (1) ──→ (N) DecorationNoteImage
```

**字段定义**：

| 字段名 | 类型 | Nullable | 默认值 | 说明 |
|--------|------|---------|--------|------|
| `id` | `Integer` | ❌ | 自增 | 主键 |
| `note_id` | `Integer` | ❌ | — | 外键 → `decoration_notes.id`，级联删除 |
| `image_path` | `String(255)` | ❌ | — | 图片文件路径 |
| `caption` | `String(200)` | ✅ | — | 图片说明/备注 |
| `order` | `Integer` | ✅ | `0` | 排序序号，数字越小越靠前 |
| `created_at` | `DateTime` | ❌ | `now_bj` | 创建时间 |

**索引**：
- 主键索引：`id`
- 外键索引：`note_id`
- 建议索引：`note_id + order`（按笔记排序查询图片）

---

### 3.9 CompareItemValue（动态字段，暂不实现）

**用途**：方案动态字段值，允许不同分类有不同字段。

**状态**：❌ 后续再做

**设计说明**：
- 第一版 CompareItem 使用固定字段（brand、model、price 等）
- 分类特殊字段内容存入 `note` 备注字段
- 如果后续需要真正支持动态字段（如瓷砖有"规格"、中央空调有"匹数"），可增加此表

**字段定义（预留）**：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | `Integer` | 主键 |
| `compare_item_id` | `Integer` | 外键 → `compare_items.id` |
| `field_key` | `String(50)` | 字段标识，如 "brand"、"spec" |
| `field_label` | `String(50)` | 字段中文名，如"品牌"、"规格" |
| `field_type` | `String(20)` | 字段类型：text/number/select/image |
| `field_value` | `Text` | 字段值 |
| `order` | `Integer` | 排序 |

---

### 3.10 Attachment（通用附件，暂不实现）

**用途**：通用附件，支持方案图片、报价单、票据等多种类型。

**状态**：❌ 后续再做（D9 附件上传阶段）

**设计说明**：
- 第一版将图片路径直接存在各模型的 `*_image` 字段中
- 如 `CompareItem.product_image`、`Expense.receipt_image`
- 如果后续需要统一的附件管理，可增加此表

**字段定义（预留）**：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | `Integer` | 主键 |
| `project_id` | `Integer` | 外键 → `decoration_projects.id` |
| `category` | `String(20)` | 附件分类：product/quote/receipt/manual/other |
| `reference_type` | `String(20)` | 引用类型：compare_item/expense/note |
| `reference_id` | `Integer` | 引用记录 ID |
| `file_path` | `String(255)` | 文件路径 |
| `file_name` | `String(200)` | 原始文件名 |
| `file_size` | `Integer` | 文件大小（字节） |
| `mime_type` | `String(50)` | MIME 类型 |
| `description` | `String(200)` | 描述 |
| `created_at` | `DateTime` | 创建时间 |

---

## 4. 模型关系汇总

```
DecorationProject (1)
  ├── (N) DecorationCategoryGroup
  │     └── (N) DecorationCategory
  │           └── (N) CompareItem
  │                 └── (N) CompareItemValue [后续]
  ├── (N) DecorationCategory
  │     ├── (N) CompareItem
  │     ├── (N) Expense
  │     └── (N) ProgressTask
  ├── (N) Expense
  ├── (N) ProgressTask
  └── (N) DecorationNote
        └── (N) DecorationNoteImage
```

---

## 5. 预算计算逻辑（供参考）

| 指标 | 计算方式 |
|------|----------|
| 总预算 | `DecorationProject.total_budget` |
| 预计花费 | Σ `CompareItem.price`（`is_selected=True` 的记录） |
| 实际已花 | Σ `Expense.amount` |
| 剩余预算 | `total_budget - 实际已花` |
| 分类预算 | 该分类 `selected_plan_id` 对应 `CompareItem.price` |
| 分类实际花费 | Σ `Expense.amount`（该分类） |

---

## 6. 第一版 vs 后续扩展对比

| 模型/功能 | 第一版 | 后续 |
|-----------|--------|------|
| `DecorationProject` | ✅ | 多项目支持 |
| `DecorationCategoryGroup` | ✅ | 层级大类（支持二级大类） |
| `DecorationCategory` | ✅ | 动态字段（通过 CompareItemValue） |
| `CompareItem` 固定字段 | ✅ | — |
| `CompareItemValue` 动态字段 | ❌ | ✅ |
| `Expense` | ✅ | 分期付款、退款 |
| `ProgressTask` | ✅ | 任务依赖、里程碑 |
| `DecorationNote` | ✅ | 富文本编辑器 |
| `DecorationNoteImage` | ✅ | 云存储 |
| `Attachment` 独立附件表 | ❌ | ✅ |
| 软删除（`deleted_at`） | ❌ | ✅ |
| 图片上传 | ❌ | D9 |

---

## 7. 文件组织结构（供 D2 参考）

```
app/models/renovamate/
  __init__.py          # 导出所有 RenovaMate 模型
  project.py            # DecorationProject
  category.py           # DecorationCategoryGroup, DecorationCategory
  compare.py            # CompareItem
  expense.py            # Expense
  task.py              # ProgressTask
  note.py               # DecorationNote, DecorationNoteImage
```

---

## 8. 待确认问题（修订后）

~~1. ~~**每个项目是否只允许一个 `DecorationProject` 记录？**~~ ✅ 已明确：第一版只支持单个项目，暂无多项目需求
~~2. ~~**是否需要软删除？**~~ ✅ 已明确：第一版暂不加软删除，后续可加 `deleted_at`
~~3. ~~**CompareItem 是否需要区分不同分类的字段？**~~ ✅ 已明确：第一版共用固定字段，分类特殊字段存 `note`
~~4. ~~**图片存储方式？**~~ ✅ 已明确：第一版本地文件系统，路径存 `String(255)` 字段
~~5. ~~**删除 CompareItem 时的孤儿引用？**~~ ✅ 已明确：使用 `ondelete='SET NULL'`
~~6. ~~**阶段枚举是否统一？**~~ ✅ 已明确：统一使用 design/demolition/water/mud/wood/paint/install/soft
~~7. ~~**tags 字段是否需要双格式兼容？**~~ ✅ 已明确：统一使用 `tags` JSON 数组，不保留逗号分隔格式
   - 方案 B（后续）：云存储（OSS/S3），路径存 URL

---

**本文档由多 Agent 工作流生成（修订版）**
- Project Manager：`02_project_manager_output.md`
- Project Architect：`03_architect_output.md`
- Code Implementer：本文件（`database_design_d1.md`）
- Code Reviewer：`04_implementer_output.md`
- **本修订版已处理所有 Code Reviewer 提出的 MUST/SHOULD 问题，等待确认后进入 D2 代码实现阶段**

**修订记录**：
- 2026-05-12：初版设计
- 2026-05-12 修订：CompareItem 删除行为（ondelete='SET NULL'）；统一阶段枚举；移除 tags 双格式兼容
