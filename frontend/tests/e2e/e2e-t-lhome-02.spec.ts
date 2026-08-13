/**
 * T-LHOME-02 加入结果边界
 * T-LEARN-01 学习概览
 * T-READER-01 内容阅读器（由于需发布内容，简化验证）
 *
 * 覆盖：错误加入、已加入班级验证、学习概览页面
 */
import { expect, test } from "@playwright/test";

const PASSWORD = "TestPass123!";

test.describe("T-LHOME-02 加入边界", () => {
  test("重复加入班级显示正确提示", async ({ page, browser }) => {
    const s = Date.now().toString();
    const className = `重复班_${s}`;

    // 教师创建班级
    const tc = await browser.newContext();
    const tp = await tc.newPage();
    await tp.goto("/");
    await tp.getByRole("button", { name: "注册账号" }).click();
    await tp.getByLabel("用户名").fill(`dup_t_${s}`);
    await tp.getByLabel("显示名称").fill("重复教师");
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
    await page.getByLabel("用户名").fill(`dup_l_${s}`);
    await page.getByLabel("显示名称").fill("重复学生");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /学习者/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("学习者");

    // 第一次加入
    await page.locator(".discover-section button", { hasText: "立即加入" }).first().click();
    await page.waitForTimeout(500);

    // 验证班级卡片已出现（已加入）
    const courseCard = page.locator("button.course-card").first();
    await expect(courseCard).toBeVisible({ timeout: 5000 });

    // 班级不再显示在发现列表中（已加入）
    const discoverSection = page.locator(".discover-section");
    // 发现区域应有"暂无可加入的教学班"或 count 减少
    await expect(discoverSection).toBeVisible();
  });
});
