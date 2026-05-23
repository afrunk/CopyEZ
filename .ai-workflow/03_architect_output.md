# Project Architect 输出 - D3-2：接入 DecorationCategory 子分类

**日期**：2026-05-12
**状态**：待执行

---

## 涉及文件分析

### 1. 新增文件

| 文件 | 用途 |
|------|------|
| `app/models/renovamate/category.py` | DecorationCategory 模型定义 |

### 2. 修改文件

| 文件 | 修改内容 |
|------|----------|
| `app/models/renovamate/__init__.py` | 导出 DecorationCategory |
| `app/modules/renovamate/__init__.py` | 添加子分类 CRUD API |
| `static/decoration/js/renovamate.js` | 改为 API 调用 |
| `tests/renovamate/compare.spec.js` | 新增 E2E 测试 |

---

## 模型设计

### DecorationCategory 模型

```python
class DecorationCategory(db.Model):
    __tablename__ = "decoration_categories"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("decoration_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    group_id = db.Column(db.Integer, db.ForeignKey("decoration_category_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(10), default="📦")
    budget = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default="not_started")
    view_mode = db.Column(db.String(20), default="card")
    description = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    is_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_bj)
    updated_at = db.Column(db.DateTime, default=now_bj, onupdate=now_bj)
```

**关系**：
- `DecorationCategory` → `DecorationCategoryGroup` (Many-to-One)
- `DecorationCategory` → `DecorationProject` (Many-to-One)

**级联删除**：删除项目时删除所有子分类，删除大类时删除所有子分类

---

## API 设计

### 子分类 API

| 方法 | 路由 | 说明 |
|------|------|------|
| GET | /decoration/api/categories | 获取所有子分类 |
| POST | /decoration/api/categories | 新增子分类 |
| PUT | /decoration/api/categories/<id> | 更新子分类 |
| DELETE | /decoration/api/categories/<id> | 删除子分类 |

### 业务规则

1. **GET /decoration/api/categories**
   - 返回当前项目的所有子分类
   - 按 sort_order 排序
   - 如果没有项目，返回空数组

2. **POST /decoration/api/categories**
   - 必填：name, group_id
   - group_id 必须关联到当前项目的已有大类
   - 如果没有项目，返回错误："请先创建装修项目"
   - 如果没有大类，返回错误："请先添加分类大类"

3. **PUT /decoration/api/categories/<id>**
   - 支持部分更新
   - 如果 group_id 变化，验证新 group_id 属于当前项目

4. **DELETE /decoration/api/categories/<id>**
   - 物理删除
   - 返回成功消息

---

## 前端修改方案

### JS 函数修改

| 函数 | 修改内容 |
|------|----------|
| initComparePage() | 加载 API 数据 |
| renderSubcatCards() | 从 API 数据渲染 |
| renderSubcatTable() | 从 API 数据渲染 |
| openSubcatModal() | 调用 GET /api/categories |
| saveSubcatModal() | 调用 POST/PUT API |
| deleteSubcat() | 调用 DELETE API |

### 数据结构

```javascript
// 假数据 → API 调用
var subCategories = [];  // 不再硬编码

// API 响应格式
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "project_id": 1,
      "group_id": 1,
      "name": "中央空调",
      "icon": "❄️",
      "budget": 30000,
      "status": "comparing",
      "view_mode": "table",
      "description": "",
      "sort_order": 0,
      "is_enabled": true,
      "created_at": "2026-05-12T10:00:00",
      "updated_at": "2026-05-12T10:00:00"
    }
  ]
}
```

### 空状态逻辑

| 场景 | 提示 |
|------|------|
| 没有项目 | "请先创建装修项目"（新增子分类按钮点击时） |
| 没有大类 | "请先添加分类大类"（新增子分类按钮点击时） |
| 有项目和大类，无子分类 | "暂无装修分类" |

---

## 数据库变更

### 新增表

```sql
CREATE TABLE decoration_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(10) DEFAULT '📦',
    budget FLOAT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'not_started',
    view_mode VARCHAR(20) DEFAULT 'card',
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    is_enabled BOOLEAN DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (project_id) REFERENCES decoration_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES decoration_category_groups(id) ON DELETE CASCADE
);
```

### 索引

- PRIMARY KEY: id
- INDEX: project_id
- INDEX: group_id

---

## 风险评估

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| 前端 JS 重构影响现有功能 | 中 | 只修改 compare 页面相关函数 |
| 删除大类时子分类也删除 | 低 | 这是预期行为（CASCADE） |
| API 错误处理不完整 | 中 | 每个 API 都要有错误处理 |
| 刷新后筛选状态丢失 | 低 | 前端状态不需要持久化 |

---

## 测试要点

### 功能测试

1. 新增子分类（验证数据库）
2. 编辑子分类（验证更新）
3. 删除子分类（验证删除）
4. 刷新页面（验证持久化）
5. 空状态提示（验证各种场景）

### 边界测试

1. 没有项目时新增子分类
2. 没有大类时新增子分类
3. 删除了关联的大类时子分类也删除
