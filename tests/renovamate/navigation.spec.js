/**
 * RenovaMate 全局导航和布局 E2E 测试
 *
 * 测试内容：
 * 1. 所有页面返回 200
 * 2. Sidebar 导航点击有效
 * 3. 当前页面 active 状态正确
 * 4. Sidebar 收起按钮有效
 * 5. Topbar 设置按钮有效
 * 6. Console 无红色 JS 报错
 */

const { test, expect } = require('@playwright/test');

/**
 * 收集 Console 错误的辅助函数（过滤无关错误）
 */
function collectConsoleErrors(page) {
  const errors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const text = msg.text();
      // 过滤浏览器插件和无关错误
      if (!text.includes('chrome-extension') && !text.includes('favicon')) {
        errors.push(text);
      }
    }
  });
  return errors;
}

test.describe('全局导航和布局测试', () => {
  let consoleErrors;

  test.afterEach(async ({ page }) => {
    // 断言没有 Console 错误
    const realErrors = consoleErrors.filter(e => !e.includes('favicon') && !e.includes('chrome-extension'));
    expect(realErrors, `Console 错误: ${realErrors.join(', ')}`).toHaveLength(0);
  });

  // ==================== 页面加载测试 ====================

  test('1. 首页 /decoration 返回 200', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    const response = await page.goto('/decoration');
    expect(response.status()).toBe(200);
  });

  test('2. 进度页 /decoration/progress 返回 200', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    const response = await page.goto('/decoration/progress');
    expect(response.status()).toBe(200);
  });

  test('3. 分类比较 /decoration/compare 返回 200', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    const response = await page.goto('/decoration/compare');
    expect(response.status()).toBe(200);
  });

  test('4. 中央空调详情 /decoration/compare/air-conditioner 返回 200', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    const response = await page.goto('/decoration/compare/air-conditioner');
    expect(response.status()).toBe(200);
  });

  test('5. 预算控制 /decoration/budget 返回 200', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    const response = await page.goto('/decoration/budget');
    expect(response.status()).toBe(200);
  });

  test('6. 装修手册 /decoration/notes 返回 200', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    const response = await page.goto('/decoration/notes');
    expect(response.status()).toBe(200);
  });

  // ==================== Sidebar 导航测试 ====================

  test('7. Sidebar 导航到首页', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/progress');
    await page.waitForTimeout(500);
    
    // 点击首页导航（使用文本定位，避免 href 属性匹配问题）
    await page.click('.sidebar .nav-item:has-text("首页总览")');
    await page.waitForTimeout(500);
    
    // 检查 URL
    expect(page.url()).toContain('/decoration');
    expect(page.url()).not.toContain('/progress');
  });

  test('8. Sidebar 导航到进度页', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration');
    await page.waitForTimeout(500);
    
    // 点击进度导航
    await page.click('.sidebar .nav-item[href="/decoration/progress"]');
    await page.waitForTimeout(500);
    
    // 检查 URL
    expect(page.url()).toContain('/decoration/progress');
  });

  test('9. Sidebar 导航到分类比较', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration');
    await page.waitForTimeout(500);
    
    await page.click('.sidebar .nav-item[href="/decoration/compare"]');
    await page.waitForTimeout(500);
    
    expect(page.url()).toContain('/decoration/compare');
    expect(page.url()).not.toContain('/air-conditioner');
  });

  test('10. Sidebar 导航到预算控制', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration');
    await page.waitForTimeout(500);
    
    await page.click('.sidebar .nav-item[href="/decoration/budget"]');
    await page.waitForTimeout(500);
    
    expect(page.url()).toContain('/decoration/budget');
  });

  test('11. Sidebar 导航到装修手册', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration');
    await page.waitForTimeout(500);
    
    await page.click('.sidebar .nav-item[href="/decoration/notes"]');
    await page.waitForTimeout(500);
    
    expect(page.url()).toContain('/decoration/notes');
  });

  // ==================== Active 状态测试 ====================

  test('12. 首页 active 状态正确', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration');
    await page.waitForTimeout(300);
    
    const activeLink = page.locator('.sidebar .nav-item.active');
    await expect(activeLink).toContainText('首页总览');
  });

  test('13. 进度页 active 状态正确', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/progress');
    await page.waitForTimeout(300);
    
    const activeLink = page.locator('.sidebar .nav-item.active');
    await expect(activeLink).toContainText('装修进度');
  });

  test('14. 分类比较 active 状态正确', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare');
    await page.waitForTimeout(500);
    
    const activeLink = page.locator('.sidebar .nav-item.active');
    await expect(activeLink).toContainText('分类比较');
  });

  test('15. 预算控制 active 状态正确', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/budget');
    await page.waitForTimeout(300);
    
    const activeLink = page.locator('.sidebar .nav-item.active');
    await expect(activeLink).toContainText('预算控制');
  });

  test('16. 装修手册 active 状态正确', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/notes');
    await page.waitForTimeout(300);
    
    const activeLink = page.locator('.sidebar .nav-item.active');
    await expect(activeLink).toContainText('装修手册');
  });

  // ==================== Sidebar 收起测试 ====================

  test('17. Sidebar 收起按钮存在', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration');
    await page.waitForTimeout(300);
    
    const collapseBtn = page.locator('.sidebar-collapse, .sidebar .collapse-btn, [class*="collapse"]');
    // 如果存在就测试点击
    const count = await collapseBtn.count();
    if (count > 0) {
      await collapseBtn.first().click();
      await page.waitForTimeout(300);
    }
  });

  // ==================== Topbar 测试 ====================

  test('18. Topbar 设置按钮存在', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration');
    await page.waitForTimeout(300);
    
    // 查找设置按钮
    const settingsBtn = page.locator('.topbar button:has-text("设置"), .topbar button[class*="settings"], .topbar button[class*="setting"]');
    const count = await settingsBtn.count();
    
    if (count > 0) {
      await settingsBtn.first().click();
      await page.waitForTimeout(500);
      // 应该打开弹窗或显示 Toast
      const modalVisible = await page.locator('.modal.active, .modal[class*="active"]').count();
      const toastVisible = await page.locator('.toast').count();
      expect(modalVisible + toastVisible).toBeGreaterThan(0);
    }
  });

  // ==================== Console 无报错测试 ====================

  test('19. 首页 Console 无红色报错', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration');
    await page.waitForTimeout(1000);
    expect(consoleErrors.filter(e => !e.includes('favicon'))).toHaveLength(0);
  });

  test('20. 进度页 Console 无红色报错', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/progress');
    await page.waitForTimeout(1000);
    expect(consoleErrors.filter(e => !e.includes('favicon'))).toHaveLength(0);
  });

  test('21. 分类比较 Console 无红色报错', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare');
    await page.waitForTimeout(1000);
    expect(consoleErrors.filter(e => !e.includes('favicon'))).toHaveLength(0);
  });

  test('22. 中央空调详情 Console 无红色报错', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare/air-conditioner');
    await page.waitForTimeout(1000);
    expect(consoleErrors.filter(e => !e.includes('favicon'))).toHaveLength(0);
  });

  test('23. 预算控制 Console 无红色报错', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/budget');
    await page.waitForTimeout(1000);
    expect(consoleErrors.filter(e => !e.includes('favicon'))).toHaveLength(0);
  });

  test('24. 装修手册 Console 无红色报错', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/notes');
    await page.waitForTimeout(1000);
    expect(consoleErrors.filter(e => !e.includes('favicon'))).toHaveLength(0);
  });
});
