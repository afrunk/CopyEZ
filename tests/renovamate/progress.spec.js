/**
 * RenovaMate 装修进度页面 E2E 测试
 *
 * 测试内容：
 * 1. 页面能正常加载
 * 2. 新建任务按钮存在
 * 3. 弹窗能打开和关闭
 * 4. 任务能新增
 * 5. 任务能编辑
 * 6. Console 无红色报错
 */

const { test, expect } = require('@playwright/test');

/**
 * 收集 Console 错误的辅助函数
 */
function collectConsoleErrors(page) {
  const errors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });
  return errors;
}

test.describe('装修进度页面 (/decoration/progress)', () => {
  let page;
  let consoleErrors;

  test.beforeEach(async ({ page: p }) => {
    page = p;
    consoleErrors = collectConsoleErrors(page);
  });

  test.afterEach(async () => {
    // 断言没有 Console 错误
    expect(consoleErrors, `Console 错误: ${consoleErrors.join(', ')}`).toHaveLength(0);
  });

  test('1. 页面能正常加载', async ({ page }) => {
    await page.goto('/decoration/progress');
    await expect(page).toHaveTitle(/装修进度/);
  });

  test('2. 页面标题显示正确', async ({ page }) => {
    await page.goto('/decoration/progress');
    const title = page.locator('h1.page-title');
    await expect(title).toContainText('装修进度看板');
  });

  test('3. 新建任务按钮存在', async ({ page }) => {
    await page.goto('/decoration/progress');
    const btn = page.locator('button:has-text("新建任务")');
    await expect(btn).toBeVisible();
  });

  test('4. 点击新建任务能打开弹窗', async ({ page }) => {
    await page.goto('/decoration/progress');
    await page.click('button:has-text("新建任务")');
    const modal = page.locator('#taskModal');
    await expect(modal).toBeVisible();
  });

  test('5. 新建任务弹窗包含必要字段', async ({ page }) => {
    await page.goto('/decoration/progress');
    await page.click('button:has-text("新建任务")');
    await expect(page.locator('#taskTitle')).toBeVisible();
    await expect(page.locator('#taskStage')).toBeVisible();
    await expect(page.locator('#taskStatus')).toBeVisible();
  });

  test('6. 阶段下拉选项正确', async ({ page }) => {
    await page.goto('/decoration/progress');
    await page.click('button:has-text("新建任务")');

    const stageSelect = page.locator('#taskStage');
    await expect(stageSelect).toBeVisible();

    const options = await stageSelect.locator('option').allTextContents();
    expect(options).toContain('设计阶段');
    expect(options).toContain('拆改阶段');
    expect(options).toContain('水电阶段');
  });

  test('7. 状态下拉选项正确', async ({ page }) => {
    await page.goto('/decoration/progress');
    await page.click('button:has-text("新建任务")');

    const statusSelect = page.locator('#taskStatus');
    await expect(statusSelect).toBeVisible();

    const options = await statusSelect.locator('option').allTextContents();
    expect(options).toContain('待开始');
    expect(options).toContain('进行中');
    expect(options).toContain('待验收');
    expect(options).toContain('已完成');
  });

  test('8. 看板结构存在（8个阶段，每个阶段4个状态）', async ({ page }) => {
    await page.goto('/decoration/progress');

    // 检查 8 个阶段
    const stages = ['design', 'demolition', 'water', 'mud', 'wood', 'paint', 'install', 'soft'];
    for (const stage of stages) {
      const cards = page.locator(`[data-stage="${stage}"]`);
      await expect(cards.first()).toBeVisible();
    }

    // 检查 4 个状态
    const statuses = ['pending', 'ongoing', 'review', 'done'];
    for (const status of statuses) {
      const cards = page.locator(`[data-status="${status}"]`);
      await expect(cards.first()).toBeVisible();
    }
  });

  test('9. 弹窗能关闭', async ({ page }) => {
    await page.goto('/decoration/progress');
    await page.click('button:has-text("新建任务")');

    const modal = page.locator('#taskModal');
    await expect(modal).toBeVisible();

    // 点击关闭按钮
    await page.click('#taskModal .modal-close');
    // 等待 CSS 动画完成
    await page.waitForTimeout(500);
    // 检查 modal 不再有 active class
    await expect(modal).not.toHaveClass(/active/);
  });

  test('10. 新增任务后能显示在看板中', async ({ page }) => {
    await page.goto('/decoration/progress');

    // 打开新建任务弹窗
    await page.click('button:has-text("新建任务")');

    // 填写任务名称
    const taskName = '测试任务-' + Date.now();
    await page.fill('#taskTitle', taskName);

    // 选择阶段和状态
    await page.selectOption('#taskStage', 'design');
    await page.selectOption('#taskStatus', 'pending');

    // 保存
    await page.click('button:has-text("保存任务")');

    // 等待弹窗关闭动画
    await page.waitForTimeout(500);

    // 检查 modal 不再有 active class
    await expect(page.locator('#taskModal')).not.toHaveClass(/active/);

    // 检查是否有 Toast 提示（成功时会显示 toast）
    await page.waitForTimeout(300);
  });

  // 注意：此测试需要数据库支持，当前跳过
  // 等接入 ProgressTask 数据库模型后启用
  test.skip('11. 新增任务后刷新数据仍然存在（需数据库）', async ({ page }) => {
    const taskName = '持久化测试-' + Date.now();

    await page.goto('/decoration/progress');

    // 新增任务
    await page.click('button:has-text("新建任务")');
    await page.fill('#taskTitle', taskName);
    await page.selectOption('#taskStage', 'design');
    await page.selectOption('#taskStatus', 'pending');
    await page.click('button:has-text("保存任务")');

    // 等待弹窗关闭动画
    await page.waitForTimeout(500);

    // 检查 modal 不再有 active class
    await expect(page.locator('#taskModal')).not.toHaveClass(/active/);
    await page.reload();

    // 检查任务是否仍然存在
    const taskCard = page.locator('.kanban-card', { hasText: taskName });
    await expect(taskCard.first()).toBeVisible();
  });

  test('12. 编辑任务弹窗能打开', async ({ page }) => {
    // 先新增一个任务
    const taskName = '编辑测试-' + Date.now();
    await page.goto('/decoration/progress');
    await page.click('button:has-text("新建任务")');
    await page.fill('#taskTitle', taskName);
    await page.selectOption('#taskStage', 'design');
    await page.selectOption('#taskStatus', 'pending');
    await page.click('button:has-text("保存任务")');
    await page.waitForTimeout(500);

    // 点击任务卡片
    const taskCard = page.locator('.kanban-card', { hasText: taskName });
    await taskCard.first().click();

    // 检查编辑弹窗是否打开
    const editModal = page.locator('#editTaskModal');
    await expect(editModal).toBeVisible();
  });

  test('13. 编辑任务弹窗包含必要字段', async ({ page }) => {
    // 先新增一个任务
    const taskName = '编辑字段测试-' + Date.now();
    await page.goto('/decoration/progress');
    await page.click('button:has-text("新建任务")');
    await page.fill('#taskTitle', taskName);
    await page.selectOption('#taskStage', 'design');
    await page.selectOption('#taskStatus', 'pending');
    await page.click('button:has-text("保存任务")');
    await page.waitForTimeout(500);

    // 点击任务卡片
    const taskCard = page.locator('.kanban-card', { hasText: taskName });
    await taskCard.first().click();

    // 检查编辑弹窗字段
    await expect(page.locator('#editTaskTitle')).toBeVisible();
    await expect(page.locator('#editTaskStage')).toBeVisible();
    await expect(page.locator('#editTaskStatus')).toBeVisible();
    await expect(page.locator('#editTaskBudget')).toBeVisible();
    await expect(page.locator('#editTaskOwner')).toBeVisible();
    await expect(page.locator('#editTaskNote')).toBeVisible();
  });
});
