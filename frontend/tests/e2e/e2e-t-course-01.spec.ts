/**
 * T-COURSE-01 学习者当前课程页面
 */
import { expect, test } from "@playwright/test";

const PASSWORD = "TestPass123!";

test.describe("T-COURSE-01 学习者课程", () => {
  test("学习者进入已加入班级查看当前课程", async ({ page, browser }) => {
    const s = Date.now().toString();
    const className = `课程班_${s}`;

    // 教师创建班级
    const tCtx = await browser.newContext();
    const tPage = await tCtx.newPage();
    await tPage.goto("/");
    await tPage.getByRole("button", { name: "注册账号" }).click();
    await tPage.getByLabel("用户名").fill(`co_t_${s}`);
    await tPage.getByLabel("显示名称").fill("课程教师");
    await tPage.getByLabel("密码").fill(PASSWORD);
    await tPage.getByRole("button", { name: /教师/ }).click();
    await tPage.getByRole("button", { name: "创建账号" }).click();
    await expect(tPage.getByTestId("role-badge")).toHaveText("教师");
    await tPage.getByRole("button", { name: "创建教学班" }).click();
    await tPage.getByLabel("班级名称").fill(className);
    await tPage.getByRole("button", { name: "确认创建" }).click();
    await tCtx.close();

    // 学习者注册并加入
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(`co_l_${s}`);
    await page.getByLabel("显示名称").fill("课程学生");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /学习者/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("学习者");

    // 自由加入
    const joinBtn = page.locator(".discover-section button", { hasText: "立即加入" }).first();
    await expect(joinBtn).toBeVisible({ timeout: 5000 });
    await joinBtn.click();
    await page.waitForTimeout(500);

    // 点击班级卡片进入
    await page.locator("button.course-card").first().click();
    await expect(page.getByLabel("当前课程导航")).toBeVisible({ timeout: 5000 });
  });
});
