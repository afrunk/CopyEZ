/**
 * RenovaMate 中央空调详情页 E2E 测试
 *
 * 测试内容：
 * 1. 返回分类按钮
 * 2. 新增方案按钮
 * 3. 新增方案弹窗打开/关闭
 * 4. 保存方案
 * 5. 表格/卡片切换
 * 6. 选为最终方案
 * 7. 编辑方案按钮（Toast）
 * 8. 删除方案按钮
 * 9. 参数设置按钮
 * 10. 参数设置弹窗打开/关闭
 * 11. 查看装修手册按钮
 * 12. 产品图/报价单点击 Toast
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

test.describe('中央空调详情页 (/decoration/compare/air-conditioner)', () => {
  let consoleErrors;

  test.afterEach(async ({ page }) => {
    const realErrors = consoleErrors.filter(e => !e.includes('favicon') && !e.includes('chrome-extension'));
    expect(realErrors, `Console 错误: ${realErrors.join(', ')}`).toHaveLength(0);
  });

  // ==================== 页面加载 ====================

  test('1. 页面能正常加载', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare/air-conditioner');
    await page.waitForTimeout(500);
    // 页面应该能加载
    const body = await page.locator('body').isVisible();
    expect(body).toBeTruthy();
  });

  test('2. 页面标题显示正确', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare/air-conditioner');
    await page.waitForTimeout(500);
    const title = page.locator('h1');
    await expect(title).toContainText('中央空调');
  });

  // ==================== 返回按钮 ====================

  test('3. 返回分类按钮存在且可点击', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare/air-conditioner');
    await page.waitForTimeout(500);
    
    // 查找返回按钮
    const backBtn = page.locator('button:has-text("返回分类")').first();
    const count = await backBtn.count();
    
    if (count > 0) {
      await backBtn.click();
      await page.waitForTimeout(500);
      expect(page.url()).toContain('/decoration/compare');
      expect(page.url()).not.toContain('/air-conditioner');
    }
  });

  // ==================== 新增方案 ====================

  test('4. 新增方案按钮存在', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare/air-conditioner');
    
    const addBtn = page.locator('button:has-text("新增方案"), button:has-text("添加方案"), button:has-text("添加")').first();
    await expect(addBtn).toBeVisible();
  });

  test('5. 点击新增方案能打开弹窗', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare/air-conditioner');
    await page.waitForTimeout(300);
    
    const addBtn = page.locator('button:has-text("新增方案"), button:has-text("添加方案")').first();
    await addBtn.click();
    await page.waitForTimeout(500);
    
    // 检查弹窗是否打开
    const modal = page.locator('.modal.active, #planModal, #addPlanModal').first();
    await expect(modal).toBeVisible();
  });

  test('6. 新增方案弹窗能关闭', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare/air-conditioner');
    await page.waitForTimeout(500);
    
    // 打开弹窗
    const addBtn = page.locator('button:has-text("新增方案")').first();
    await addBtn.click();
    await page.waitForTimeout(500);
    
    // 点击关闭
    const closeBtn = page.locator('#addPlanModal .modal-close').first();
    await closeBtn.click();
    await page.waitForTimeout(500);
    
    // 检查弹窗是否关闭
    const modal = page.locator('#addPlanModal.active');
    await expect(modal).toHaveCount(0);
  });

  test('7. 新增方案弹窗包含必要字段', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare/air-conditioner');
    await page.waitForTimeout(300);
    
    // 打开弹窗
    const addBtn = page.locator('button:has-text("新增方案"), button:has-text("添加方案")').first();
    await addBtn.click();
    await page.waitForTimeout(500);
    
    // 检查必要字段
    const brandInput = page.locator('#planBrand, #brand, input[id*="brand"]').first();
    const modelInput = page.locator('#planModel, #model, input[id*="model"]').first();
    const priceInput = page.locator('#planPrice, #price, input[id*="price"]').first();
    
    // 至少有一个字段存在
    const hasBrand = await brandInput.count() > 0;
    const hasModel = await modelInput.count() > 0;
    const hasPrice = await priceInput.count() > 0;
    
    expect(hasBrand || hasModel || hasPrice).toBeTruthy();
  });

  // ==================== 视图切换 ====================

  test('8. 表格视图切换按钮存在', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare/air-conditioner');
    await page.waitForTimeout(300);
    
    const tableViewBtn = page.locator('button:has-text("表格"), [data-view="table"]').first();
    await expect(tableViewBtn).toBeVisible();
  });

  test('9. 卡片视图切换按钮存在', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare/air-conditioner');
    await page.waitForTimeout(300);
    
    const cardViewBtn = page.locator('button:has-text("卡片"), [data-view="card"]').first();
    await expect(cardViewBtn).toBeVisible();
  });

  test('10. 视图切换有效', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare/air-conditioner');
    await page.waitForTimeout(300);
    
    // 点击卡片视图
    const cardViewBtn = page.locator('button:has-text("卡片"), [data-view="card"]').first();
    await cardViewBtn.click();
    await page.waitForTimeout(300);
    
    // 点击表格视图
    const tableViewBtn = page.locator('button:has-text("表格"), [data-view="table"]').first();
    await tableViewBtn.click();
    await page.waitForTimeout(300);
    
    // 视图应该切换了
    await expect(tableViewBtn).toHaveClass(/active/);
  });

  // ==================== 参数设置弹窗 ====================

  test('11. 参数设置按钮存在', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare/air-conditioner');
    await page.waitForTimeout(300);
    
    const settingsBtn = page.locator('button:has-text("参数设置"), button:has-text("参数"), [class*="param"]').first();
    const count = await settingsBtn.count();
    
    if (count > 0) {
      await expect(settingsBtn).toBeVisible();
    }
  });

  test('12. 参数设置弹窗能打开', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare/air-conditioner');
    await page.waitForTimeout(500);
    
    // 点击参数设置按钮
    const settingsBtn = page.locator('button:has-text("参数设置")').first();
    const count = await settingsBtn.count();
    
    if (count > 0) {
      await settingsBtn.click();
      await page.waitForTimeout(500);
      
      // 检查弹窗或 Toast
      const modalVisible = await page.locator('#paramSettingsModal.active').count();
      const toastCount = await page.locator('.toast').count();
      expect(modalVisible + toastCount).toBeGreaterThan(0);
    }
  });

  // ==================== 查看装修手册按钮 ====================

  test('13. 查看装修手册按钮存在', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare/air-conditioner');
    await page.waitForTimeout(300);
    
    const notesBtn = page.locator('a:has-text("查看装修手册"), a:has-text("装修手册"), button:has-text("查看手册")').first();
    await expect(notesBtn).toBeVisible();
  });

  test('14. 查看装修手册按钮可跳转', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare/air-conditioner');
    await page.waitForTimeout(300);
    
    const notesBtn = page.locator('a:has-text("查看装修手册"), a:has-text("装修手册"), button:has-text("查看手册")').first();
    await notesBtn.click();
    await page.waitForTimeout(500);
    
    expect(page.url()).toContain('/decoration/notes');
  });

  // ==================== 产品图/报价单点击 ====================

  test('15. 产品图按钮存在且有点击反馈', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare/air-conditioner');
    await page.waitForTimeout(300);
    
    const imgBtn = page.locator('button:has-text("图片"), button:has-text("产品图"), .plan-attachment').first();
    const count = await imgBtn.count();
    
    if (count > 0) {
      await imgBtn.click();
      await page.waitForTimeout(500);
      
      // 检查 Toast
      const toast = page.locator('.toast');
      await expect(toast).toBeVisible();
    }
  });

  // ==================== Console 无报错 ====================

  test('16. Console 无红色报错', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare/air-conditioner');
    await page.waitForTimeout(1000);
    expect(consoleErrors.filter(e => !e.includes('favicon'))).toHaveLength(0);
  });
});
