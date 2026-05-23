# Cursor 多 Agent 迭代开发工作流

本工作流为 Flask/Django/Python Web 项目设计，采用多 Agent 协作模式，通过迭代开发确保代码质量和功能完整性。

---

## 目录结构

```
.cursor/
└── skills/                    # Cursor 技能定义
    ├── project-manager/       # 项目经理
    │   └── SKILL.md
    ├── project-architect/     # 架构师
    │   └── SKILL.md
    ├── code-implementer/      # 代码实现者
    │   └── SKILL.md
    ├── code-reviewer/         # 代码审查者
    │   └── SKILL.md
    ├── test-verifier/         # 测试验证者
    │   └── SKILL.md
    └── ui-reviewer/           # UI 审查者
        └── SKILL.md

.ai-workflow/                  # 工作流文档
├── 01_requirements.md         # 需求文档
├── 02_project_manager_output.md  # 项目经理输出
├── 03_architect_output.md    # 架构师输出
├── 04_implementer_output.md  # 实现者输出
├── 05_reviewer_output.md     # 审查者输出
├── 06_test_output.md         # 测试验证输出
└── 07_iteration_log.md        # 迭代日志
```

---

## 角色职责

| 角色 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **Project Manager** | 需求分析、任务拆分 | 需求文档 | 项目经理输出 |
| **Project Architect** | 技术方案设计、架构分析 | 项目经理输出 | 架构师输出 |
| **Code Implementer** | 按方案实现代码 | 架构师输出 | 实现者输出 |
| **Code Reviewer** | 代码审查、质量把控 | 实现者输出 | 审查报告 |
| **UI Reviewer** | 界面审查、交互验证 | 实现者输出 | UI 审查报告 |
| **Test Verifier** | 测试验证、问题发现 | 实现者输出 | 测试报告 |

---

## 工作流程图

```
┌─────────────┐
│   开始迭代   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Project    │── 读取 01_requirements.md
│  Manager    │
└──────┬──────┘
       │ 输出 02_project_manager_output.md
       ▼
┌─────────────┐
│  Project    │── 读取 02_...
│  Architect  │
└──────┬──────┘
       │ 输出 03_architect_output.md
       ▼
┌─────────────┐
│   Code      │── 读取 03_...
│ Implementer │
└──────┬──────┘
       │ 输出 04_implementer_output.md
       ▼
   ┌───┴───┐
   │       │
   ▼       ▼
┌─────┐ ┌─────┐
│Code │ │ UI  │── 并行执行
│Rev. │ │Rev. │
└──┬──┘ └──┬──┘
   │       │
   └─┬─────┘
     │ 输出 05_reviewer_output.md
     ▼
┌─────────────┐
│   Test      │── 读取 04_..., 05_...
│  Verifier   │
└──────┬──────┘
       │ 输出 06_test_output.md
       ▼
┌─────────────┐
│ 更新迭代日志 │
│ 07_iter...  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 问题全部修复?│
└──────┬──────┘
       │
   是  │  否
   ▼       ▼
┌─────┐ ┌─────────────┐
│ 结束 │ │ 下一轮迭代   │
└─────┘ └─────────────┘
```

---

## 迭代规则

### 循环限制

- **最大迭代次数**：3 轮
- **每轮必须记录**：
  - 修改了哪些文件
  - 为什么修改
  - 是否可以结束

### 第二轮及以后规则

当进入第二轮迭代时：

1. **只修复必须修复项**
   - MUST 级别问题必须修复
   - SHOULD 级别问题尽量修复
   - NICE 级别问题可选

2. **禁止行为**
   - 不允许大范围重构
   - 不允许删除已有功能
   - 不允许修改与需求无关的文件
   - 不允许改变已有接口

3. **允许行为**
   - 修复 reviewer 指出的问题
   - 优化 reviewer 建议的内容
   - 补充遗漏的边界处理

### 结束条件

满足以下任一条件，可结束迭代：

1. **无阻断性问题**
   - MUST 问题数量 = 0
   - 所有核心功能可用

2. **达到最大迭代次数**
   - 第 3 轮结束后自动结束
   - 未解决问题记录到日志

3. **需求不明确**
   - 写入 `07_iteration_log.md`
   - 等待用户补充信息

---

## 使用方式

### 启动新的迭代

1. 在 `01_requirements.md` 中填写需求
2. 执行 Project Manager 角色
3. 按顺序执行其他角色
4. 记录到 `07_iteration_log.md`

### 继续未完成的迭代

1. 检查 `07_iteration_log.md` 当前状态
2. 从中断点继续执行
3. 修复问题后继续下一阶段

### 手动触发角色

在 Cursor 中输入对应角色名称或使用 Task 工具调用：

```
project-manager
project-architect
code-implementer
code-reviewer
test-verifier
ui-reviewer
```

---

## 文档说明

### 01_requirements.md - 需求文档

每次迭代前，用户在此填写功能需求。

**必填项**：
- 需求描述
- 功能列表
- 验收标准

### 02_project_manager_output.md - 项目经理输出

分析需求，拆分为可执行任务。

**输出内容**：
- 任务优先级（P0/P1/P2）
- 本轮目标
- 风险提示

### 03_architect_output.md - 架构师输出

设计技术方案，指导代码实现。

**输出内容**：
- 路由设计
- 数据模型
- 文件变更清单
- 风险评估

### 04_implementer_output.md - 实现者输出

按照架构方案实现代码。

**输出内容**：
- 代码摘要
- 文件变更详情
- 测试建议

### 05_reviewer_output.md - 审查者输出

审查代码质量和 UI 表现。

**输出内容**：
- 问题分级（MUST/SHOULD/NICE）
- 修复建议
- 审查结论

### 06_test_output.md - 测试验证输出

验证代码可运行性。

**输出内容**：
- 静态检查结果
- 手动测试命令
- 问题清单

### 07_iteration_log.md - 迭代日志

记录所有迭代的执行过程。

**输出内容**：
- 迭代历史
- 修改文件清单
- 问题追踪
- 决策记录

---

## 问题分级

| 级别 | 含义 | 处理方式 |
|------|------|----------|
| **MUST** | 必须修复，否则功能无法正常工作 | 立即修复 |
| **SHOULD** | 建议修复，影响代码质量或用户体验 | 尽量修复 |
| **NICE** | 可选优化，提升可维护性 | 视情况修复 |

---

## 约束条件

1. **不改变已有接口**
   - URL 路由保持不变
   - JSON 响应格式保持不变
   - 数据库表结构保持不变

2. **不删除已有功能**
   - 除非用户明确要求
   - 除非功能完全冗余且无引用

3. **中文优先**
   - 所有说明使用中文
   - 代码注释尽量使用中文

4. **完整可运行**
   - 每次修改后保证代码完整
   - 不允许 TODO 或 NotImplementedError

---

## 参考项目

- [pridiuksson/cursor-agents](https://github.com/pridiuksson/cursor-agents) - Multi-agent workflow
- [spencerpauly/awesome-cursor-skills](https://github.com/spencerpauly/awesome-cursor-skills) - Cursor Skills 格式
- [e-gov/cursor-prompts](https://github.com/e-gov/cursor-prompts) - 命令式工作流

---

## 适用项目类型

本工作流适合：

- ✅ Flask Web 应用
- ✅ Django 项目
- ✅ 其他 Python Web 框架
- ✅ API 服务
- ✅ SPA 后端

本工作流不适合：

- ❌ 纯前端项目（无后端）
- ❌ 简单的脚本工具
- ❌ 需要即时反馈的探索性开发

---

## 常见问题

### Q: 如果 reviewer 提出多个 MUST 问题怎么办？

A: 在第二轮中逐个修复。如果问题太多，考虑拆分为多个迭代。

### Q: 如果架构方案发现不可行怎么办？

A: 记录问题到日志，提出替代方案，等待用户确认。

### Q: 如果需求不明确怎么办？

A: 停止实现，将问题写入日志，等待用户补充信息。不要猜测需求。

### Q: 如何处理遗留问题？

A: 在 `07_iteration_log.md` 中记录，进入下一迭代或标记为待处理。

---

## 更新记录

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| YYYY-MM-DD | 1.0 | 初始版本 |
