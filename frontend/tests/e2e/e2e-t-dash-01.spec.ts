/**
 * T-DASH-01 / T-EVIDENCE-01 教师分析页面
 */
import { expect, test } from "@playwright/test";

const PASSWORD = "TestPass123!";

async function reg(page: any, s: string) {
  await page.goto("/");
  await page.getByRole("button", { name: "注册账号" }).click();
  await page.getByLabel("用户名").fill(`dash_t_${s}`);
  await page.getByLabel("显示名称").fill("分析教师");
  await page.getByLabel("密码").fill(PASSWORD);
  await page.getByRole("button", { name: /教师/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();
  await expect(page.getByTestId("role-badge")).toHaveText("教师");
}

test.describe("T-DASH-01 / T-EVIDENCE-01 教师分析", () => {
  test("进入班级概览页签", async ({ page }) => {
    const s = Date.now().toString();
    await reg(page, s);
    await page.getByRole("button", { name: "创建教学班" }).click();
    await page.getByLabel("班级名称").fill(`分析班_${s}`);
    await page.getByRole("button", { name: "确认创建" }).click();
    await page.locator("button.class-card", { hasText: `分析班_${s}` }).click();

    // 班级概览
    await page.getByLabel("教学班导航").getByRole("button", { name: "班级概览" }).click();
    await expect(page.getByRole("heading", { name: "班级概览" })).toBeVisible({ timeout: 5000 });
  });

  test("进入学习者详情页签", async ({ page }) => {
    const s = Date.now().toString();
    await reg(page, s);
    await page.getByRole("button", { name: "创建教学班" }).click();
    await page.getByLabel("班级名称").fill(`详情班_${s}`);
    await page.getByRole("button", { name: "确认创建" }).click();
    await page.locator("button.class-card", { hasText: `详情班_${s}` }).click();

    await page.getByLabel("教学班导航").getByRole("button", { name: "学习者详情" }).click();
    await expect(page.getByRole("heading", { name: "学习者列表" })).toBeVisible({ timeout: 5000 });
  });
});
