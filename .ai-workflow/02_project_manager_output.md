# 项目经理输出 - D3-2：接入 DecorationCategory 子分类

**日期**：2026-05-12
**状态**：待执行

---

## 需求理解

本轮任务是接入 DecorationCategory 子分类模型，让分类比较页面（/decoration/compare）能够：

1. 从数据库读取子分类数据
2. 新增、编辑、删除子分类
3. 子分类关联分类大类（group_id）
4. 刷新页面后数据持久化
5. 大类筛选基于真实 group_id
6. 没有项目/大类时显示正确的空状态提示

**本轮范围**：只做子分类 CRUD，不做方案、预算、任务、装修手册。

---

## 项目现状分析

### 已有结构

| 类别 | 内容 |
|------|------|
| **模型** | DecorationProject, DecorationCategoryGroup |
| **API (大类)** | GET /decoration/api/groups, POST /decoration/api/groups, PUT /decoration/api/groups/<id>, DELETE /decoration/api/groups/<id> |
| **模板** | compare.html（子分类 UI 已存在） |
| **JS 函数** | initComparePage, renderCategoryGroups, renderSubcatCards, renderSubcatTable, openSubcatModal, saveSubcatModal, deleteSubcat, navigateToCategoryDetail |

### 需要新增/修改

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/models/renovamate/category.py` | 新增 | DecorationCategory 模型 |
| `app/models/renovamate/__init__.py` | 修改 | 导出新模型 |
| `app/modules/renovamate/__init__.py` | 修改 | 添加子分类 CRUD API |
| `static/decoration/js/renovamate.js` | 修改 | 改为 API 调用 |
| `tests/renovamate/compare.spec.js` | 新增 | Playwright E2E 测试 |

---

## 任务拆分

### [P0] 必须完成（阻塞项）

- [ ] 1. 创建 DecorationCategory 模型
- [ ] 2. 添加子分类 CRUD API
- [ ] 3. 前端 JS 改为调用 API
- [ ] 4. 验证新增/编辑/删除功能
- [ ] 5. 验证刷新后数据持久化
- [ ] 6. 验证空状态提示逻辑

### [P1] 应该完成（重要功能）

- [ ] 7. 创建 Playwright 测试文件

---

## 本轮目标

**核心目标**：完成 DecorationCategory 子分类接入

**成功标准**：
1. /decoration/compare 页面从数据库读取子分类
2. 新增子分类成功，刷新后数据存在
3. 编辑子分类成功，更新正确
4. 删除子分类成功，页面移除
5. 大类筛选基于真实 group_id
6. Playwright E2E 测试通过

**不包含**：
- CompareItem 方案模型
- Expense 花费模型
- ProgressTask 任务模型
- DecorationNote 装修手册

---

## 风险提示

1. **前端 JS 需要从假数据改为 API 调用**：涉及重构 initComparePage 等函数
2. **空状态逻辑需要调整**：没有项目时禁止新增，没有大类时禁止新增子分类
3. **API 命名一致性**：与 D3-1 大类 API 保持风格一致
4. **数据库关联**：sub_categories 表依赖 category_groups 表

---

## API 路由设计

```
GET    /decoration/api/categories          # 获取所有子分类
POST   /decoration/api/categories          # 新增子分类
PUT    /decoration/api/categories/<id>      # 更新子分类
DELETE /decoration/api/categories/<id>      # 删除子分类
```

---

## DecorationCategory 字段设计

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| project_id | Integer | 关联项目 |
| group_id | Integer | 关联分类大类 |
| name | String(100) | 分类名称 |
| icon | String(10) | 图标 |
| budget | Float | 预算 |
| status | String(20) | 状态 |
| view_mode | String(20) | 展示方式 |
| description | Text | 备注 |
| sort_order | Integer | 排序 |
| is_enabled | Boolean | 是否启用 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**status 枚举**：
- not_started → 未开始
- comparing → 比价中
- selected → 已选方案
- ongoing → 进行中
- pending_confirm → 待确认

**view_mode 枚举**：
- table → 表格模式
- card → 卡片模式
- list → 清单模式
