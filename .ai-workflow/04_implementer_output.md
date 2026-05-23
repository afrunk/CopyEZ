# 实现者输出 - D3-1

## 本轮实现内容

### 任务 1: 创建 DecorationCategoryGroup 模型
- 文件：`app/models/renovamate/category_group.py`
- 字段：id, project_id, name, icon, description, sort_order, is_enabled, created_at, updated_at

### 任务 2: 添加 API 路由
- 文件：`app/modules/renovamate/__init__.py`
- GET /decoration/api/groups - 获取所有大类
- POST /decoration/api/groups - 创建大类
- PUT /decoration/api/groups/<id> - 更新大类
- DELETE /decoration/api/groups/<id> - 删除大类

### 任务 3: 前端 API 调用
- 文件：`static/decoration/js/renovamate.js`
- 添加 `loadCategoryGroupsFromAPI()` 函数
- 修改 `saveGroupModal()` 调用 POST/PUT API
- 修改 `deleteGroup()` 调用 DELETE API
- 更新字段映射：g.enabled → g.is_enabled, g.desc → g.description, g.order → g.sort_order
- 更新 compare 页面初始化逻辑

### 任务 4: 数据库表创建
- 文件：`app.py`
- 添加 `decoration_category_groups` 表创建检查

## 文件变更

### 新增文件

| 文件 | 行数 | 用途 |
|------|------|------|
| `app/models/renovamate/category_group.py` | 48 | 分类大类模型 |

### 修改文件

| 文件 | 变更说明 |
|------|----------|
| `app/models/renovamate/__init__.py` | 导出新模型 |
| `app/modules/renovamate/__init__.py` | 添加 API 路由 |
| `static/decoration/js/renovamate.js` | 改为 API 调用 |
| `app.py` | 表创建逻辑 |

## 实现说明

- [x] 代码完整可运行
- [x] 无 TODO 或 NotImplementedError
- [x] 遵循项目规范（使用 db from app.extensions）
- [x] 包含必要的错误处理
- [x] 没有项目时显示"请先创建装修项目"
- [x] CRUD 操作通过 API 完成
