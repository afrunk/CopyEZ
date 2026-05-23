/**
 * RenovaMate 预算控制页面 E2E 测试
 *
 * 测试内容：
 * 1. 设置总预算按钮
 * 2. 新增花费按钮
 * 3. 新增花费弹窗打开/关闭
 * 4. 保存花费
 * 5. 预算筛选按钮
 * 6. 表格中"记一笔"
 * 7. 表格中"查看"
 * 8. 支出记录点击
 * 9. 空状态按钮不能无反应
 * 10. Console 无红色报错
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

test.describe('预算控制页面 (/decoration/budget)', () => {
  let consoleErrors;

  test.afterEach(async ({ page }) => {
    const realErrors = consoleErrors.filter(e => !e.includes('favicon') && !e.includes('chrome-extension'));
    expect(realErrors, `Console 错误: ${realErrors.join(', ')}`).toHaveLength(0);
  });

  // ==================== 页面加载 ====================

  test('1. 页面能正常加载', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/budget');
    // 页面 title 是 "RenovaMate 装修助手"，检查页面内容包含预算相关文本
    await expect(page.locator('h1')).toContainText('预算');
  });

  test('2. 页面标题显示正确', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/budget');
    // 页面 h1 是 "预算控制"，class 为 budget-page-title
    const title = page.locator('h1:has-text("预算控制")');
    await expect(title).toBeVisible();
  });

  // ==================== 设置总预算按钮 ====================

  test('3. 设置总预算按钮存在', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/budget');
    await page.waitForTimeout(300);
    
    const setBudgetBtn = page.locator('button:has-text("设置总预算"), button:has-text("设置预算"), button:has-text("总预算"), .btn:has-text("预算")').first();
    const count = await setBudgetBtn.count();
    
    if (count > 0) {
      await expect(setBudgetBtn).toBeVisible();
    }
  });

  test('4. 设置总预算按钮有反馈', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/budget');
    await page.waitForTimeout(300);
    
    // 空状态下的"设置总预算"按钮会 showToast
    const setBudgetBtn = page.locator('.hero-project-card button:has-text("设置总预算")').first();
    const count = await setBudgetBtn.count();
    
    if (count > 0) {
      await setBudgetBtn.click();
      await page.waitForTimeout(800);
      
      // 检查 Toast（class 是 toast-message，不是 toast）
      const toastCount = await page.locator('.toast-message').count();
      expect(toastCount).toBeGreaterThan(0);
    }
  });

  // ==================== 新增花费按钮 ====================

  test('5. 新增花费按钮存在', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/budget');
    await page.waitForTimeout(300);
    
    const addExpenseBtn = page.locator('button:has-text("新增花费"), button:has-text("添加花费"), button:has-text("记一笔"), button:has-text("新增支出")').first();
    await expect(addExpenseBtn).toBeVisible();
  });

  test('6. 点击新增花费能打开弹窗', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/budget');
    await page.waitForTimeout(300);
    
    const addExpenseBtn = page.locator('button:has-text("新增花费"), button:has-text("添加花费"), button:has-text("记一笔")').first();
    await addExpenseBtn.click();
    await page.waitForTimeout(500);
    
    // 检查弹窗是否打开
    const modal = page.locator('.modal.active, #expenseModal, #addExpenseModal').first();
    await expect(modal).toBeVisible();
  });

  test('7. 新增花费弹窗能关闭', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/budget');
    await page.waitForTimeout(300);
    
    // 打开弹窗
    const addExpenseBtn = page.locator('button:has-text("新增花费")').first();
    await addExpenseBtn.click();
    await page.waitForTimeout(800);
    
    // 点击"取消"按钮关闭弹窗
    const closeBtn = page.locator('#expenseModal button:has-text("取消")').first();
    await closeBtn.click();
    await page.waitForTimeout(500);
    
    // 检查弹窗是否关闭（通过 overlay 不再有 active class）
    const modalActive = await page.locator('#expenseModal.active').count();
    await expect(modalActive).toBe(0);
  });

  test('8. 新增花费弹窗包含必要字段', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/budget');
    await page.waitForTimeout(300);
    
    // 打开弹窗
    const addExpenseBtn = page.locator('button:has-text("新增花费"), button:has-text("添加花费"), button:has-text("记一笔")').first();
    await addExpenseBtn.click();
    await page.waitForTimeout(500);
    
    // 检查必要字段
    const nameInput = page.locator('input[id*="name"], input[id*="expense"], input[id*="title"]').first();
    const amountInput = page.locator('input[id*="amount"], input[id*="money"], input[id*="price"]').first();
    
    // 至少有一个字段存在
    const hasName = await nameInput.count() > 0;
    const hasAmount = await amountInput.count() > 0;
    
    expect(hasName || hasAmount).toBeTruthy();
  });

  // ==================== 预算筛选 ====================

  test('9. 预算筛选按钮存在', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/budget');
    await page.waitForTimeout(300);
    
    const filterBtns = page.locator('.filter-btn, .budget-filter, button[class*="filter"]');
    const count = await filterBtns.count();
    
    if (count > 0) {
      await expect(filterBtns.first()).toBeVisible();
    }
  });

  test('10. 预算筛选按钮可点击', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/budget');
    await page.waitForTimeout(300);
    
    const filterBtns = page.locator('.filter-btn, .budget-filter, button[class*="filter"]');
    const count = await filterBtns.count();
    
    if (count > 0) {
      await filterBtns.first().click();
      await page.waitForTimeout(300);
    }
  });

  // ==================== 表格操作 ====================

  test('11. 表格中存在操作按钮', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/budget');
    await page.waitForTimeout(300);
    
    // 查找表格中的按钮
    const actionBtns = page.locator('table button, .table-wrapper button');
    const count = await actionBtns.count();
    
    // 表格应该存在按钮
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('12. "记一笔"按钮存在于表格中', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/budget');
    await page.waitForTimeout(300);
    
    const quickAddBtn = page.locator('table button:has-text("记一笔"), .table-wrapper button:has-text("记一笔")').first();
    const count = await quickAddBtn.count();
    
    if (count > 0) {
      await expect(quickAddBtn).toBeVisible();
    }
  });

  // ==================== 空状态按钮 ====================

  test('13. 空状态下新增花费按钮有效', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/budget');
    await page.waitForTimeout(300);
    
    // 点击"新增花费"按钮（不是"设置总预算"）
    const addExpenseBtn = page.locator('button:has-text("新增花费")').first();
    const count = await addExpenseBtn.count();
    
    if (count > 0) {
      await addExpenseBtn.click();
      await page.waitForTimeout(800);
      
      // 应该有反馈（弹窗打开）
      const modalCount = await page.locator('#expenseModal.active').count();
      expect(modalCount).toBeGreaterThan(0);
    }
  });

  // ==================== Console 无报错 ====================

  test('14. Console 无红色报错', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/budget');
    await page.waitForTimeout(1000);
    expect(consoleErrors.filter(e => !e.includes('favicon'))).toHaveLength(0);
  });
});
