// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Playwright 配置
 * @see https://playwright.dev/docs/test-configuration
 */
module.exports = defineConfig({
  // 测试基础 URL
  baseURL: 'http://127.0.0.1:5000',

  // 测试超时时间（毫秒）
  timeout: 30000,

  // 全局测试配置
  use: {
    // 基础 URL
    baseURL: 'http://127.0.0.1:5000',

    // 截图策略
    screenshot: 'only-on-failure',

    // 视频录制
    video: 'retain-on-failure',

    // 跟踪数据
    trace: 'on-first-retry',

    // 忽略 HTTPS 错误
    ignoreHTTPSErrors: true,

    // 截图目录
    screenshotDir: 'test-results/screenshots',
  },

  // 全局超时配置
  expect: {
    timeout: 5000,
  },

  // 项目配置
  projects: [
    // Chromium（桌面）
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
    },

    // iPad 横屏
    {
      name: 'ipad-horizontal',
      use: {
        ...devices['iPad (gen 7)'],
        viewport: { width: 1180, height: 820 },
        orientation: 'landscape',
      },
    },

    // iPad 竖屏
    {
      name: 'ipad-vertical',
      use: {
        ...devices['iPad (gen 7)'],
        viewport: { width: 820, height: 1180 },
        orientation: 'portrait',
      },
    },

    // 手机
    {
      name: 'mobile',
      use: {
        ...devices['iPhone 12'],
      },
    },
  ],

  // Web 服务器配置（用于 CI/CD）
  webServer: undefined,

  // 输出目录
  outputDir: 'test-results',
});
