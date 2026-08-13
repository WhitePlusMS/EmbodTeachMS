/**
 * T-PREP-01 备课步骤1：文档选择
 */
import { expect, test } from "@playwright/test";

const PASSWORD = "TestPass123!";

async function reg(page: any, s: string) {
  await page.goto("/");
  await page.getByRole("button", { name: "注册账号" }).click();
  await page.getByLabel("用户名").fill(`prep_t_${s}`);
  await page.getByLabel("显示名称").fill("备课教师");
  await page.getByLabel("密码").fill(PASSWORD);
  await page.getByRole("button", { name: /教师/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();
  await expect(page.getByTestId("role-badge")).toHaveText("教师");
}

test.describe("T-PREP-01 备课入口", () => {
  test("进入课件备课页签", async ({ page }) => {
    const s = Date.now().toString();
    await reg(page, s);
    await page.getByRole("button", { name: "创建教学班" }).click();
    await page.getByLabel("班级名称").fill(`备课班_${s}`);
    await page.getByRole("button", { name: "确认创建" }).click();
    await page.locator("button.class-card", { hasText: `备课班_${s}` }).click();

    // 进入课件备课
    await page.getByLabel("教学班导航").getByRole("button", { name: "课件备课" }).click();
    await expect(page.getByRole("heading", { name: "课件备课" })).toBeVisible({ timeout: 5000 });
  });
});
