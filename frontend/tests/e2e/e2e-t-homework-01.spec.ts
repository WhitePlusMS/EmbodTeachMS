/**
 * T-HOMEWORK-01 作业管理
 */
import { expect, test } from "@playwright/test";

const PASSWORD = "TestPass123!";

async function reg(page: any, s: string) {
  await page.goto("/");
  await page.getByRole("button", { name: "注册账号" }).click();
  await page.getByLabel("用户名").fill(`hw_t_${s}`);
  await page.getByLabel("显示名称").fill("作业教师");
  await page.getByLabel("密码").fill(PASSWORD);
  await page.getByRole("button", { name: /教师/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();
  await expect(page.getByTestId("role-badge")).toHaveText("教师");
}

test.describe("T-HOMEWORK-01 作业管理", () => {
  test("进入作业管理页签", async ({ page }) => {
    const s = Date.now().toString();
    await reg(page, s);
    await page.getByRole("button", { name: "创建教学班" }).click();
    await page.getByLabel("班级名称").fill(`作业班_${s}`);
    await page.getByRole("button", { name: "确认创建" }).click();
    await page.locator("button.class-card", { hasText: `作业班_${s}` }).click();
    await page.getByLabel("教学班导航").getByRole("button", { name: "作业管理" }).click();
    await expect(page.getByRole("heading", { name: "作业管理" })).toBeVisible({ timeout: 5000 });
  });
});
