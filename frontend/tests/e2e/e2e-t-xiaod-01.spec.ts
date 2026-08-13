/**
 * T-XIAOD-01 / T-XIAOD-02 小D伴学
 */
import { expect, test } from "@playwright/test";

const PASSWORD = "TestPass123!";

test.describe("T-XIAOD 小D伴学", () => {
  test("学习者进入班级后查看学习概览", async ({ page, browser }) => {
    const s = Date.now().toString();
    const className = `概览班_${s}`;

    // 教师创建班级
    const tc = await browser.newContext();
    const tp = await tc.newPage();
    await tp.goto("/");
    await tp.getByRole("button", { name: "注册账号" }).click();
    await tp.getByLabel("用户名").fill(`over_t_${s}`);
    await tp.getByLabel("显示名称").fill("概览教师");
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
    await page.getByLabel("用户名").fill(`over_l_${s}`);
    await page.getByLabel("显示名称").fill("概览学生");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /学习者/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("学习者");

    await page.locator(".discover-section button", { hasText: "立即加入" }).first().click();
    await page.waitForTimeout(500);
    await page.locator("button.course-card").first().click();

    // 切到学习概览
    await page.getByLabel("当前课程导航").getByRole("button", { name: "学习概览" }).click();
    // 验证页面存在
    await expect(page.getByRole("heading", { name: "进度与知识掌握" }).or(page.getByText("暂无数据"))).toBeVisible({ timeout: 5000 });
  });
});
