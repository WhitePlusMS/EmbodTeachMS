/**
 * T-WEBOTS-01 / T-WEBOTS-02 仿真实训页面
 */
import { expect, test } from "@playwright/test";

const PASSWORD = "TestPass123!";

test.describe("T-WEBOTS 仿真实训", () => {
  test("学习者进入仿真实训页签", async ({ page, browser }) => {
    await page.setViewportSize({ width: 1024, height: 768 });
    const s = Date.now().toString();
    const className = `仿真班_${s}`;

    // 教师创建班级
    const tc = await browser.newContext();
    const tp = await tc.newPage();
    await tp.goto("/");
    await tp.getByRole("button", { name: "注册账号" }).click();
    await tp.getByLabel("用户名").fill(`web_t_${s}`);
    await tp.getByLabel("显示名称").fill("仿真教师");
    await tp.getByLabel("密码").fill(PASSWORD);
    await tp.getByRole("button", { name: /教师/ }).click();
    await tp.getByRole("button", { name: "创建账号" }).click();
    await expect(tp.getByTestId("role-badge")).toHaveText("教师");
    await tp.getByRole("button", { name: "创建教学班" }).click();
    await tp.getByLabel("班级名称").fill(className);
    await tp.getByRole("button", { name: "确认创建" }).click();
    await tc.close();

    // 学习者注册并加入
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(`web_l_${s}`);
    await page.getByLabel("显示名称").fill("仿真学生");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /学习者/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("学习者");

    // 自由加入
    await page.locator(".discover-section button", { hasText: "立即加入" }).first().click();
    await expect(page.locator("article.course-card").first()).toBeVisible({ timeout: 5000 });

    // 进入班级 → 仿真实训
    await page.locator("article.course-card").first().click();
    await page.getByLabel("当前课程导航").getByRole("button", { name: "三维演示" }).click();

    // 验证页面加载（可能是空态或功能页面）
    await expect(page.getByRole("heading", { name: "具身智能三维演示" }).or(page.getByText("暂未配置"))).toBeVisible({ timeout: 5000 });

    await expect(page.locator(".scene-host canvas")).toBeVisible({ timeout: 5000 });
    const canvasSamples = await page.evaluate(async () => {
      const host = document.querySelector<HTMLElement>(".scene-host");
      const canvas = host?.querySelector<HTMLCanvasElement>("canvas");
      if (!host || !canvas) return [];

      const samples: Array<{ hostHeight: number; canvasHeight: number }> = [];
      for (let index = 0; index < 8; index += 1) {
        await new Promise<void>((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        samples.push({ hostHeight: host.clientHeight, canvasHeight: canvas.height });
      }
      return samples;
    });

    expect(canvasSamples).toHaveLength(8);
    expect(Math.max(...canvasSamples.map((sample) => sample.hostHeight))).toBeLessThan(2000);
    expect(Math.max(...canvasSamples.map((sample) => sample.canvasHeight))).toBeLessThan(4000);
  });
});
