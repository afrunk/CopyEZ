/**
 * RenovaMate 分类比较页面 E2E 测试（精简版）
 */

const { test, expect } = require('@playwright/test');

function collectConsoleErrors(page) {
  const errors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });
  return errors;
}

test.describe('分类比较页面 (/decoration/compare)', () => {
  let consoleErrors;

  test('1. 页面能正常加载', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare');
    await expect(page).toHaveTitle(/分类比较/);
  });

  test('2. 页面标题显示正确', async ({ page }) => {
    await page.goto('/decoration/compare');
    const title = page.locator('h1.page-title');
    await expect(title).toContainText('分类比较');
  });

  test('3. 新增子分类按钮存在', async ({ page }) => {
    await page.goto('/decoration/compare');
    const btn = page.locator('#btnAddSubcat');
    await expect(btn).toBeVisible();
  });

  test('4. 新增大类按钮存在', async ({ page }) => {
    await page.goto('/decoration/compare');
    const btn = page.locator('#btnAddGroup');
    await expect(btn).toBeVisible();
  });

  test('5. 没有大类时，新增子分类提示', async ({ page }) => {
    await page.goto('/decoration/compare');
    await page.waitForTimeout(500);
    
    await page.click('#btnAddSubcat');
    await page.waitForTimeout(300);
    
    // 检查 toast 提示
    const toast = page.locator('.toast');
    await expect(toast).toContainText(/请先添加分类大类|没有分类大类/, { timeout: 3000 }).catch(() => {
      // 如果没有 toast，检查 modal 是否打开
      const modal = page.locator('#subcatModal');
      const isModalOpen = modal.evaluate(el => el.classList.contains('active'));
      expect(isModalOpen).toBe(false);
    });
  });

  test('6. Console 无红色报错', async ({ page }) => {
    consoleErrors = collectConsoleErrors(page);
    await page.goto('/decoration/compare');
    await page.waitForTimeout(1000);
    expect(consoleErrors.filter(e => !e.includes('favicon'))).toHaveLength(0);
  });
});
