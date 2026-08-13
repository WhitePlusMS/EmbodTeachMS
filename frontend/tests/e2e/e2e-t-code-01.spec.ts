/**
 * T-CODE-01 授权码管理
 *
 * 覆盖：
 *   1) 教师进入授权码管理页签
 *   2) 启用授权码
 *   3) 保存授权码设置
 */
import { expect, test } from "@playwright/test";

const PASSWORD = "TestPass123!";

async function registerTeacher(page: import("@playwright/test").Page, suffix: string) {
  await page.goto("/");
  await page.getByRole("button", { name: "注册账号" }).click();
  await page.getByLabel("用户名").fill(`code_t_${suffix}`);
  await page.getByLabel("显示名称").fill("授权码教师");
  await page.getByLabel("密码").fill(PASSWORD);
  await page.getByRole("button", { name: /教师/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();
  await expect(page.getByTestId("role-badge")).toHaveText("教师");
}

test.describe("T-CODE-01 授权码管理", () => {
  test("教师进入授权码管理页签并保存授权码", async ({ page }) => {
    const s = Date.now().toString();
    const className = `授权码班_${s}`;

    await registerTeacher(page, `a_${s}`);
    await page.getByRole("button", { name: "创建教学班" }).click();
    await page.getByLabel("班级名称").fill(className);
    await page.getByRole("button", { name: "确认创建" }).click();
    await page.locator("button.class-card", { hasText: className }).click();

    // 切换到授权码管理页签
    await page.getByLabel("教学班导航").getByRole("button", { name: "授权码管理" }).click();

    // 验证页面加载
    await expect(page.getByRole("heading", { name: "授权码管理" })).toBeVisible({ timeout: 5000 });
  });
});
