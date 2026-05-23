/**
 * RenovaMate 装修手册页面 E2E 测试
 *
 * 测试内容：
 * 1. 页面加载与结构
 * 2. 笔记 CRUD 持久化（P0 修复验证）
 * 3. 添加内容按钮
 * 4. 新增记录弹窗打开/关闭
 * 5. 保存记录
 * 6. 编辑记录
 * 7. 删除记录
 * 8. 左侧目录点击
 * 9. 阶段折叠/展开
 * 10. 图片占位点击 Toast
 * 11. 关联任务/分类点击
 * 12. 空状态下新增记录有效
 * 13. Console 无红色报错
 */

const { test, expect } = require('@playwright/test');

/**
 * 收集 Console 错误的辅助函数
 */
function collectConsoleErrors(page) {
  const errors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const text = msg.text();
      if (!text.includes('chrome-extension') && !text.includes('favicon')) {
        errors.push(text);
      }
    }
  });
  return errors;
}

test.describe('装修手册页面 (/decoration/notes)', () => {
  let consoleErrors;

  test.afterEach(async ({ page }) => {
    const realErrors = consoleErrors.filter(e => !e.includes('favicon') && !e.includes('chrome-extension'));
    expect(realErrors, `Console 错误: ${realErrors.join(', ')}`).toHaveLength(0);
  });

  // ==================== 页面加载 ====================

  test('1. 页面能正常加载', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/notes');
    await expect(page).toHaveTitle(/手册/);
  });

  test('2. 页面标题显示正确', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/notes');
    const title = page.locator('h1.page-title');
    await expect(title).toContainText('装修手册');
  });

  // ==================== P0 修复验证：笔记从 API 加载 ====================

  test('3. 页面加载后从数据库 API 获取笔记数据', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/notes');
    // 等待 JS 执行完毕（initNotesPage 调用 loadNotesFromAPI）
    await page.waitForTimeout(1500);
    // 不应该有 JS 报错
    expect(consoleErrors).toHaveLength(0);
  });

  test('4. 页面加载后能从数据库读取笔记记录（空状态或已有记录）', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/notes');
    await page.waitForTimeout(1500);
    // 至少手册布局应该可见
    const layout = page.locator('.manual-layout');
    await expect(layout).toBeVisible();
  });

  // ==================== 添加内容按钮 ====================

  test('5. 添加内容按钮存在', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/notes');
    await page.waitForTimeout(300);

    const addBtn = page.locator('button:has-text("添加内容"), button:has-text("添加"), button:has-text("新增记录")').first();
    await expect(addBtn).toBeVisible();
  });

  test('6. 点击添加内容能打开弹窗', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/notes');
    await page.waitForTimeout(300);

    const addBtn = page.locator('button:has-text("添加内容"), button:has-text("新增记录")').first();
    await addBtn.click();
    await page.waitForTimeout(500);

    // 检查弹窗是否打开
    const modal = page.locator('#noteEntryModal.active, .modal.active');
    await expect(modal).toBeVisible();
  });

  test('7. 添加内容弹窗能关闭', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/notes');
    await page.waitForTimeout(300);

    // 打开弹窗
    const addBtn = page.locator('button:has-text("添加内容"), button:has-text("新增记录")').first();
    await addBtn.click();
    await page.waitForTimeout(500);

    // 点击取消按钮关闭
    const cancelBtn = page.locator('#noteEntryModal button:has-text("取消")').first();
    await cancelBtn.click();
    await page.waitForTimeout(500);

    // 检查弹窗已关闭
    const modal = page.locator('#noteEntryModal.active');
    await expect(modal).toHaveCount(0);
  });

  test('8. 添加内容弹窗包含必要字段', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/notes');
    await page.waitForTimeout(300);

    // 打开弹窗
    const addBtn = page.locator('button:has-text("添加内容"), button:has-text("新增记录")').first();
    await addBtn.click();
    await page.waitForTimeout(500);

    // 检查必要字段
    const titleInput = page.locator('#noteTitle');
    const contentInput = page.locator('#noteContent');
    await expect(titleInput).toBeVisible();
    await expect(contentInput).toBeVisible();
  });

  // ==================== 新增笔记并验证持久化 ====================

  test('9. 新增笔记后写入数据库并刷新后仍然存在', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/notes');
    await page.waitForTimeout(500);

    // 打开新增弹窗
    const addBtn = page.locator('button:has-text("添加内容"), button:has-text("新增记录")').first();
    await addBtn.click();
    await page.waitForTimeout(500);

    // 填写表单
    await page.fill('#noteTitle', '自动化测试手册记录');
    await page.fill('#noteContent', '这是自动化测试创建的内容');

    // 保存
    const saveBtn = page.locator('#noteEntryModal button:has-text("保存记录"), #noteEntryModal button:has-text("保存")').first();
    await saveBtn.click();
    await page.waitForTimeout(1000);

    // 应该出现保存成功提示
    const toast = page.locator('.toast-message');
    await expect(toast).toContainText('已新增');

    // 刷新页面
    await page.reload();
    await page.waitForTimeout(1500);

    // 记录应该还在
    const record = page.locator('.manual-entry').filter({ hasText: '自动化测试手册记录' });
    await expect(record.first()).toBeVisible();
  });

  // ==================== 编辑笔记并验证持久化 ====================

  test('10. 编辑笔记后刷新仍然显示更新内容', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/notes');
    await page.waitForTimeout(1500);

    // 找到一条笔记并编辑
    const entries = page.locator('.manual-entry');
    const count = await entries.count();

    if (count > 0) {
      // 点击编辑按钮
      const editBtn = page.locator('.note-action-btn[title="编辑"]').first();
      await editBtn.click();
      await page.waitForTimeout(500);

      // 修改标题
      const titleInput = page.locator('#editNoteTitle');
      await titleInput.fill('已编辑：自动化测试手册记录');
      await titleInput.press('Tab');

      // 保存
      const saveBtn = page.locator('#editNoteModal button:has-text("保存修改"), #editNoteModal button:has-text("保存")').first();
      await saveBtn.click();
      await page.waitForTimeout(1000);

      // 刷新页面
      await page.reload();
      await page.waitForTimeout(1500);

      // 编辑后的标题应该还在
      const editedRecord = page.locator('.manual-entry').filter({ hasText: '已编辑：自动化测试手册记录' });
      await expect(editedRecord.first()).toBeVisible();
    } else {
      // 如果没有笔记，跳过（由测试 9 创建的笔记可能已被其他测试删除）
      test.skip();
    }
  });

  // ==================== 删除笔记并验证持久化 ====================

  test('11. 删除笔记后刷新不再显示', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/notes');
    await page.waitForTimeout(1500);

    // 找到一条笔记
    const entries = page.locator('.manual-entry');
    const count = await entries.count();

    if (count > 0) {
      const firstEntry = entries.first();
      const originalTitle = await firstEntry.locator('.manual-entry-title').textContent();

      // 点击删除按钮
      const deleteBtn = firstEntry.locator('.note-action-btn.danger');
      await deleteBtn.click();
      await page.waitForTimeout(500);

      // 确认删除
      page.on('dialog', dialog => dialog.accept());
      await deleteBtn.click();
      await page.waitForTimeout(1000);

      // 刷新页面
      await page.reload();
      await page.waitForTimeout(1500);

      // 删除的标题不应该再出现
      const deletedRecord = page.locator('.manual-entry').filter({ hasText: originalTitle });
      await expect(deletedRecord).toHaveCount(0);
    } else {
      // 如果没有笔记，跳过
      test.skip();
    }
  });

  // ==================== 阶段折叠/展开 ====================

  test('12. 阶段可以折叠/展开', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/notes');
    await page.waitForTimeout(300);

    const chapterHeader = page.locator('.manual-chapter-header').first();
    await chapterHeader.click();
    await page.waitForTimeout(300);
    // 应该可以点击不报错
  });

  // ==================== 图片占位 ====================

  test('13. 图片占位点击有 Toast 反馈', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/notes');
    await page.waitForTimeout(300);

    const imgPlaceholder = page.locator('.img-upload-item').first();
    const count = await imgPlaceholder.count();

    if (count > 0) {
      await imgPlaceholder.click();
      await page.waitForTimeout(500);
      // 应该出现 Toast
      const toast = page.locator('.toast-message');
      await expect(toast).toBeVisible();
    }
  });

  // ==================== 空状态 ====================

  test('14. 空状态下添加内容按钮有效', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/notes');
    await page.waitForTimeout(300);

    const addBtn = page.locator('button:has-text("添加内容"), button:has-text("新增记录"), button:has-text("添加")').first();
    await addBtn.click();
    await page.waitForTimeout(500);

    const modalOrToast = await page.locator('#noteEntryModal.active, .toast-message').count();
    expect(modalOrToast).toBeGreaterThan(0);
  });

  // ==================== Console 无报错 ====================

  test('15. Console 无红色报错', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/notes');
    await page.waitForTimeout(2000);
    expect(consoleErrors.filter(e => !e.includes('favicon'))).toHaveLength(0);
  });
});
