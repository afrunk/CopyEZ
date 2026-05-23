# RenovaMate 原型图融合 CopyEZ：从静态原型到可用 Flask 子项目的完整任务需求

> 本文件是 RenovaMate 融合 CopyEZ 项目的总需求入口。  
> Cursor / Coso 后续所有迭代任务都必须先读取本文件，再按照多 Agent 工作流执行。  
> 本文件目标不是写一次性提示词，而是把"静态原型图 → 可运行 Flask 子项目 → 可新增数据的装修助手"的全过程任务沉淀下来。

---

## 0. 项目总目标

将 RenovaMate 装修助手静态原型逐步融合进现有 CopyEZ Flask 项目，作为一个独立子项目模块使用。

最终访问前缀：

```text
/decoration
```

最终目标是做成一个真正可用的本地装修助手，而不是静态展示页。

RenovaMate 需要支持：

```text
1. 装修项目总览
2. 装修进度管理
3. 分类大类管理
4. 子分类管理
5. 具体分类方案比较
6. 中央空调等分类详情页
7. 预算控制
8. 实际花费记录
9. 装修手册 / 装修笔记
10. 图片和附件记录
11. PC 编辑、iPad 横屏展示、手机基础适配
```

---

## 1. 核心原则

### 1.1 不破坏 CopyEZ 原项目

RenovaMate 是 CopyEZ 的子项目，不允许破坏 CopyEZ 原有功能。

禁止影响：

```text
1. CopyEZ 首页
2. 素材管理
3. 随心记
4. 语录本
5. 阅读功能
6. LedgerEZ
7. 原有数据库模型
8. 原有模板
9. 原有静态资源
10. 原有路由
```

如必须修改 CopyEZ 原文件，必须先写入：

```text
.ai-workflow/07_iteration_log.md
```

说明原因、风险、涉及文件，等待确认后再改。

---

### 1.2 独立模块

RenovaMate 必须作为独立模块存在。

推荐结构：

```text
app/modules/renovamate/
  __init__.py
  routes.py                 # 如果当前项目风格需要，可后续拆出

templates/decoration/
  base.html
  index.html
  progress.html
  compare.html
  air_conditioner.html
  budget.html
  notes.html
  placeholder.html

static/decoration/
  css/
    renovamate.css
  js/
    renovamate.js
  uploads/
    notes/
    plans/
    receipts/
```

访问路径使用：

```text
/decoration
```

内部模块目录可以继续叫 `renovamate`，避免大规模改 import。

---

### 1.3 先静态迁移，再接数据库

开发阶段分两大步：

```text
第一阶段：把静态原型完整迁移到 Flask，可访问、可点击、样式正常。
第二阶段：逐步接数据库，让所有数据由用户自己新增。
```

第一阶段不接数据库。

第二阶段开始后，页面不能再依赖大量写死演示数据。

---

### 1.4 最终网站默认应为空数据

这是项目最重要的产品逻辑之一。

最终 RenovaMate 上线后，默认不应该自带演示装修数据。

用户首次进入时应看到空状态：

```text
暂无装修项目，请先创建装修项目
暂无分类，请先添加分类
暂无方案，请新增第一个方案
暂无花费记录，请点击"新增花费"
暂无装修任务，请点击"新建任务"
暂无装修手册记录，请点击"添加内容"
```

原型里的中央空调、门窗、预算、支出、任务、手册记录只用于开发参考，不应作为真实默认数据写入数据库。

可以后续添加：

```text
导入示例数据
```

但不能默认污染真实数据。

---

## 2. 当前已完成状态

当前已经完成：

```text
1. decoration Blueprint 已接入
2. /decoration 可访问
3. static/decoration/css/renovamate.css 已迁移
4. static/decoration/js/renovamate.js 已迁移
5. templates/decoration/base.html 已创建
6. templates/decoration/index.html 首页已迁移
7. templates/decoration/progress.html 装修进度页已迁移
```

当前待迁移：

```text
1. templates/decoration/compare.html 分类比较页
2. templates/decoration/air_conditioner.html 中央空调详情页
3. templates/decoration/budget.html 预算控制页
4. templates/decoration/notes.html 装修手册页
```

当前原型来源：

```text
templates/原型图/pages/1-overview.html
templates/原型图/pages/4-progress.html
templates/原型图/pages/2-compare.html
templates/原型图/pages/2-air-conditioner.html
templates/原型图/pages/3-budget.html
templates/原型图/pages/5-notes.html
templates/原型图/pages/css/renovamate.css
templates/原型图/pages/js/renovamate.js
```

---

## 3. 多 Agent 工作流规则

### 3.1 每轮执行顺序

每一轮必须按以下顺序：

```text
1. project-manager 读取需求并拆分本轮任务
2. project-architect 分析涉及文件、路由、模板、静态资源和风险
3. code-implementer 执行代码修改
4. code-reviewer 审查代码，不直接改代码
5. test-verifier 验证 Flask、路由、模板、静态资源、JS 报错
6. ui-reviewer 检查页面布局、按钮、PC / iPad / 手机显示
7. web-app-tester 执行浏览器自动化测试（涉及页面交互时必须执行）
8. 写入 .ai-workflow/07_iteration_log.md
```

### 3.2 web-app-tester 必读规则

只要任务涉及页面交互，就必须运行浏览器自动化测试。

**强制执行条件**：
- 新增/编辑/删除功能
- 表单提交
- 弹窗交互
- 页面跳转
- 数据持久化（刷新后数据是否保留）

**web-app-tester 职责**：
1. 使用 Playwright 进行真实的浏览器自动化测试
2. 检查页面是否能打开
3. 检查按钮是否可点击
4. 检查弹窗是否能打开和关闭
5. 检查表单是否能填写和保存
6. 检查新增/编辑/删除是否有页面反馈
7. 检查 Console 是否有红色 JS 报错
8. 检查路由跳转是否正确
9. 检查刷新后持久化数据是否仍然存在
10. 输出测试结果，不允许跳过失败项

**测试工具选择**：
1. 优先使用 Cursor Web App Testing MCP（`cursor-ide-browser`）
2. 如果 MCP 不可用，使用 Playwright

**自动化测试失败时**：
- 不允许进入下一阶段任务
- 必须修复测试失败项
- 修复后补充回归测试

**测试文件位置**：
```
tests/
  renovamate/
    progress.spec.js      # 装修进度页
    compare.spec.js      # 分类比较页
    index.spec.js        # 首页总览
    budget.spec.js       # 预算控制页
    notes.spec.js       # 装修手册页
```

**测试命令**：
```bash
# 安装 Playwright（如果未安装）
npm run playwright:install

# 运行所有 E2E 测试
npm run test:e2e

# 运行带 UI 的测试
npm run test:e2e:headed

# 运行特定测试文件
npx playwright test tests/renovamate/progress.spec.js
```

---

### 3.2 每轮只做一个目标

每轮只允许一个明确目标，例如：

```text
迁移分类比较页
迁移中央空调详情页
迁移预算控制页
迁移装修手册页
修复分类比较页筛选
修复中央空调详情页表格
修复预算页新增花费
修复装修手册编辑记录
接入 DecorationProject 模型
接入分类管理数据库
```

禁止一轮同时迁移多个页面或同时迁移页面和接数据库。

---

### 3.3 最多循环 3 轮

如果 reviewer 或 verifier 发现必须修复项：

```text
第 2 轮只修复必须修复项
第 3 轮只修复剩余阻断项
```

最多 3 轮。

不允许越修越大。

---

### 3.4 每轮必须写日志

每轮完成后追加写入：

```text
.ai-workflow/07_iteration_log.md
```

记录：

```text
1. 本轮目标
2. 修改文件
3. 修改原因
4. Project Manager 输出摘要
5. Architect 输出摘要
6. Implementer 修改摘要
7. Code Reviewer 复核结果
8. Test Verifier 验证结果
9. UI Reviewer 检查结果
10. 是否需要下一轮修复
11. 是否可以结束本轮
```

---

## 4. 静态页面迁移规则

### 4.1 只迁移主体内容

从原型 HTML 迁移到 Flask 模板时，只迁移主体内容。

禁止迁移：

```text
<!DOCTYPE html>
<html>
<head>
<body>
aside.sidebar
header.topbar
app-layout
main
CSS link
JS script
```

这些由：

```text
templates/decoration/base.html
```

统一提供。

---

### 4.2 所有模板必须继承 base.html

页面必须使用：

```jinja2
{% extends "decoration/base.html" %}
```

内容写入：

```jinja2
{% block content %}
...
{% endblock %}
```

如果需要页面级 JS：

```jinja2
{% block extra_js %}
...
{% endblock %}
```

如果需要页面级 CSS：

```jinja2
{% block extra_css %}
...
{% endblock %}
```

---

### 4.3 所有链接必须用 url_for

禁止保留：

```text
1-overview.html
2-compare.html
2-air-conditioner.html
3-budget.html
4-progress.html
5-notes.html
```

必须替换为：

```jinja2
{{ url_for('decoration.index') }}
{{ url_for('decoration.progress') }}
{{ url_for('decoration.compare') }}
{{ url_for('decoration.air_conditioner') }}
{{ url_for('decoration.budget') }}
{{ url_for('decoration.notes') }}
```

---

## 5. 第一阶段：静态页面迁移任务清单

---

### 任务 S1：迁移分类比较页面

来源：

```text
templates/原型图/pages/2-compare.html
```

目标：

```text
templates/decoration/compare.html
```

路由：

```text
/decoration/compare
```

页面定位：

```text
装修分类入口 + 分类管理中心
```

必须包含：

```text
1. 页面标题区
2. 分类大类区域
3. 分类筛选区域
4. 子分类卡片区域
5. 卡片 / 表格视图切换
6. 新增大类弹窗
7. 新增子分类弹窗
8. 编辑子分类弹窗
9. 子分类删除确认
10. 中央空调入口跳转
```

大类：

```text
设备系统
家电家具
主材选择
施工项目
软装搭配
```

子分类：

```text
设备系统：中央空调、新风系统、地暖、热水器、智能家居
家电家具：冰箱、洗衣机、电视、洗碗机
主材选择：门窗、瓷砖、地板、木门、卫浴、全屋定制
施工项目：水电、木工、瓦工、油漆、防水、吊顶、拆改
软装搭配：灯具、窗帘、沙发、床、挂画、地毯
```

交互要求：

```text
1. 点击大类卡片可以筛选子分类
2. 点击筛选按钮可以筛选子分类
3. 点击卡片 / 表格可以切换视图
4. 点击新增大类可以打开弹窗
5. 点击新增子分类可以打开弹窗
6. 新增子分类后页面能显示新分类
7. 点击编辑可以打开编辑弹窗
8. 修改后页面内容能更新
9. 点击删除有确认框
10. 点击中央空调能跳转到 /decoration/compare/air-conditioner 或占位页
11. 所有按钮不能无反应
12. Console 不能出现红色 JS 报错
```

空状态要求：

```text
暂无分类，请先添加分类大类或子分类
```

验收：

```text
1. /decoration/compare 可访问
2. 页面不被 sidebar 遮挡
3. sidebar active 为"分类比较"
4. 大类筛选有效
5. 卡片 / 表格切换有效
6. 新增、编辑、删除子分类有效
7. 中央空调可跳转
8. 首页和装修进度不受影响
```

---

### 任务 S2：迁移中央空调详情页

来源：

```text
templates/原型图/pages/2-air-conditioner.html
```

目标：

```text
templates/decoration/air_conditioner.html
```

路由：

```text
/decoration/compare/air-conditioner
```

页面定位：

```text
具体分类的方案比较详情页
```

必须包含：

```text
1. 页面标题区
2. 分类概览卡片
3. 操作按钮区
4. 参数设置摘要
5. 方案对比表格
6. 方案卡片视图
7. 新增方案弹窗
8. 编辑方案弹窗或编辑占位
9. 参数设置弹窗
10. 相关装修手册记录
11. 决策建议区域
```

中央空调方案字段：

```text
品牌
型号
匹数
一拖几
总价
外机数量
内机数量
能效等级
保修
推荐指数
产品图片
报价单图片
备注
是否最终方案
```

交互要求：

```text
1. 返回分类跳转 /decoration/compare
2. 新增方案打开弹窗
3. 保存后新增方案到页面
4. 参数设置打开弹窗
5. 选为最终方案可切换高亮
6. 表格 / 卡片切换有效
7. 产品图和报价单点击有反馈
8. 查看全部手册跳转 /decoration/notes
9. Console 无红色报错
```

空状态要求：

```text
暂无方案，请新增第一个方案
```

验收：

```text
1. /decoration/compare/air-conditioner 可访问
2. 页面布局正常
3. 表格横向滚动正常
4. 已选方案高亮
5. 新增方案有效
6. 选为最终方案有效
7. 分类比较页可跳转到此页面
```

---

### 任务 S3：迁移预算控制页面

来源：

```text
templates/原型图/pages/3-budget.html
```

目标：

```text
templates/decoration/budget.html
```

路由：

```text
/decoration/budget
```

页面定位：

```text
装修预算驾驶舱
```

必须包含：

```text
1. 页面标题区
2. 预算驾驶舱 Hero
3. 预算使用率
4. 预计占比
5. 核心统计卡片
6. 预算风险提醒
7. 预算明细表
8. 预算筛选按钮
9. 实际花费记录
10. 新增花费弹窗
11. 分类花费分析
12. 下一步预算建议
```

预算逻辑：

```text
总预算：来自项目设置
预计花费：来自各分类已选最终方案求和
实际已花：来自花费记录求和
剩余预算：总预算 - 实际已花
差额：预算值 - 实际花费
```

重要限制：

```text
实际已花不能手动编辑
剩余预算不能手动编辑
预计花费不能在预算页直接手动编辑
```

交互要求：

```text
1. 新增花费按钮打开弹窗
2. 保存花费后新增到记录列表
3. 顶部实际已花、剩余预算前端可更新
4. 筛选按钮可筛选预算表
5. 表格"记一笔"可打开新增花费并自动填充分类
6. 表格"查看"有反馈
7. 支出记录点击有反馈
8. Console 无红色报错
```

空状态要求：

```text
暂无预算数据，请先设置总预算并选择分类方案
暂无花费记录，请点击"新增花费"
```

验收：

```text
1. /decoration/budget 可访问
2. 页面像预算驾驶舱，不是普通表格
3. 新增花费有效
4. 预算筛选有效
5. 首页和进度页不受影响
```

---

### 任务 S4：迁移装修手册页面

来源：

```text
templates/原型图/pages/5-notes.html
```

目标：

```text
templates/decoration/notes.html
```

路由：

```text
/decoration/notes
```

页面定位：

```text
装修过程记录、灵感、图片、链接、避坑、门店沟通记录
```

必须包含：

```text
1. 页面标题区
2. 左侧阶段目录
3. 右侧手册章节
4. 添加内容按钮
5. 新增记录弹窗
6. 编辑记录弹窗
7. 删除记录
8. 阶段折叠 / 展开
9. 图片占位和图片备注
10. 关联任务
11. 关联分类
12. 搜索或筛选入口
```

交互要求：

```text
1. 添加内容打开弹窗
2. 保存后新增记录
3. 每条记录有编辑按钮
4. 编辑弹窗回显原内容
5. 保存编辑后页面更新
6. 删除记录有确认
7. 左侧目录点击滚动到对应阶段
8. 阶段可折叠 / 展开
9. 图片点击有预览反馈
10. Console 无红色报错
```

空状态要求：

```text
暂无装修手册记录，请点击"添加内容"开始记录
```

验收：

```text
1. /decoration/notes 可访问
2. 页面布局正常
3. 新增、编辑、删除记录有效
4. 阶段目录正常
5. 首页、进度、分类、预算不受影响
```

---

## 6. 第二阶段：数据库与真实数据任务清单

> 只有当所有静态页面迁移完成，并通过验收后，才能开始第二阶段。

---

### 任务 D1：设计数据库模型方案

本任务只输出设计，不写代码。

需要设计：

```text
DecorationProject
DecorationCategoryGroup
DecorationCategory
CategoryField
CompareItem
CompareItemValue
Expense
ProgressTask
DecorationNote
DecorationNoteImage
Attachment
```

输出每个模型：

```text
1. 字段
2. 类型
3. 关系
4. 用途
5. 是否第一版必须
6. 是否可以后续再做
```

等待确认后再写代码。

---

### 任务 D2：接入 DecorationProject 项目设置

功能：

```text
1. 创建装修项目
2. 编辑项目名称
3. 编辑面积
4. 编辑装修风格
5. 编辑总预算
6. 编辑当前阶段
7. 首页读取真实项目数据
```

空状态：

```text
暂无装修项目，请先创建装修项目
```

要求：

```text
1. 总预算可编辑
2. 实际已花不可手动编辑
3. 剩余预算自动计算
```

---

### 任务 D3：接入分类大类和子分类

模型：

```text
DecorationCategoryGroup
DecorationCategory
```

功能：

```text
1. 新增大类
2. 编辑大类
3. 删除大类
4. 图标选择
5. 新增子分类
6. 编辑子分类
7. 删除子分类
8. 大类筛选
9. 卡片 / 表格视图
```

默认无数据：

```text
暂无分类，请先添加分类
```

---

### 任务 D4：接入具体分类方案

模型：

```text
CompareItem
```

先做固定字段版本，不做动态字段。

中央空调字段：

```text
品牌
型号
匹数
一拖几
总价
外机数量
内机数量
能效等级
保修
推荐指数
备注
是否最终方案
```

功能：

```text
1. 新增方案
2. 编辑方案
3. 删除方案
4. 选为最终方案
5. 最终方案进入预算控制
```

默认无数据：

```text
暂无方案，请新增第一个方案
```

---

### 任务 D5：接入实际花费

模型：

```text
Expense
```

字段：

```text
项目
分类
方案
支出名称
金额
支付日期
支付方式
收款方
票据图片
备注
```

功能：

```text
1. 新增花费
2. 编辑花费
3. 删除花费
4. 按分类汇总
5. 首页最近花费读取真实数据
6. 预算页实际已花求和
```

---

### 任务 D6：接入预算控制真实逻辑

预算页逻辑：

```text
总预算 = DecorationProject.total_budget
预计花费 = 各分类最终方案 CompareItem.price 求和
实际已花 = Expense.amount 求和
剩余预算 = 总预算 - 实际已花
分类预算 = 分类最终方案价格
分类实际花费 = 当前分类 Expense 求和
差额 = 分类预算 - 分类实际花费
```

状态：

```text
实际花费 > 分类预算：超支
实际花费 < 分类预算：节省
实际花费 = 分类预算：持平
没有最终方案：未选择
没有实际花费：未发生
```

---

### 任务 D7：接入装修进度任务

模型：

```text
ProgressTask
```

功能：

```text
1. 新建任务
2. 编辑任务
3. 删除任务
4. 修改状态
5. 关联分类
6. 关联手册
7. 首页待办读取真实数据
8. 进度页读取真实任务
```

状态：

```text
pending 待开始
ongoing 进行中
review 待验收
done 已完成
```

阶段：

```text
design 设计
demolition 拆改
water 水电
mud 泥工
wood 木工
paint 油漆
install 安装
soft 软装
```

---

### 任务 D8：接入装修手册记录

模型：

```text
DecorationNote
DecorationNoteImage
```

功能：

```text
1. 新增记录
2. 编辑记录
3. 删除记录
4. 关联阶段
5. 关联分类
6. 关联任务
7. 关联方案
8. 图片备注
```

默认无数据：

```text
暂无装修手册记录，请点击"添加内容"开始记录
```

---

### 任务 D9：接入附件与图片上传

模型：

```text
Attachment
```

图片类型：

```text
方案图片
报价单图片
票据图片
施工现场图片
装修手册图片
```

第一版只做：

```text
1. 上传
2. 预览
3. 删除
4. 备注
```

不做：

```text
OCR
图片识别
自由画笔标注
```

---

## 7. 第三阶段：产品完善任务

静态和数据库都完成后，再考虑：

```text
1. 创建装修项目向导
2. 空状态引导
3. 示例数据导入
4. 数据导出
5. PDF 报告
6. 图片打点标注
7. 方案筛选和排序
8. 预算风险自动分析
9. 手机端深度适配
10. 多项目管理
```

---

## 8. 下一轮推荐任务

当前下一轮推荐任务：

```text
任务 BUGFIX-PROGRESS：修复装修进度页面任务新增功能
```

执行时必须遵守：

```text
只修 progress 页面的任务新增 bug
使用 web-app-tester 验证修复
完成后写入 07_iteration_log.md
```

验收必须满足：

```text
1. /decoration/progress 可访问
2. 新建任务可以保存
3. 不再提示"未找到对应的任务列"
4. 新增任务能显示在对应阶段和状态下
5. 新增任务能再次编辑
6. 自动化测试通过
7. Console 无红色 JS 报错
```

## 9. 测试能力要求

### 9.1 Playwright E2E 测试

所有涉及页面交互的任务必须通过 Playwright 自动化测试。

**安装 Playwright**：
```bash
npm install -D @playwright/test
npx playwright install chromium
```

**测试文件命名规范**：
```
tests/
  renovamate/
    progress.spec.js    # 装修进度页
    compare.spec.js    # 分类比较页
    index.spec.js     # 首页总览
    budget.spec.js    # 预算控制页
    notes.spec.js     # 装修手册页
```

**每个新功能必须包含**：
1. 页面加载测试
2. 按钮/弹窗交互测试
3. 表单填写测试
4. 数据持久化测试（刷新后数据是否保留）
5. Console 错误检测

**测试失败时**：
- 不允许跳过
- 不允许进入下一阶段
- 必须修复后补充回归测试

### 9.2 数据库功能测试

涉及数据库的新增/编辑/删除功能，必须测试：

1. **新增后刷新数据在吗？** - 验证持久化
2. **编辑后刷新数据对吗？** - 验证更新
3. **删除后刷新数据没了吗？** - 验证删除

---

## 附录：测试命令速查

```bash
# 安装依赖
npm install -D @playwright/test
npx playwright install chromium

# 运行测试
npm run test:e2e          # 运行所有测试
npm run test:e2e:headed   # 带 UI 运行
npx playwright test tests/renovamate/progress.spec.js  # 单文件
```
