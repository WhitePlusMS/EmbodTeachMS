import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  workers: 1,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:14173",
    channel: "chrome",
    viewport: { width: 1920, height: 1080 },
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "desktop-chrome",
      // 设备预设自带 1280×720，需在展开后显式覆盖，确保桌面验收使用完整工作台视野。
      use: { ...devices["Desktop Chrome"], viewport: { width: 1920, height: 1080 } },
    },
  ],
});
