import { expect, test } from "@playwright/test";

test("教师班级 Agent 抽屉支持展开、切换和清理", async ({ page }) => {
  const suffix = Date.now().toString();
  await page.goto("/");
  await page.getByRole("button", { name: "注册账号" }).click();
  await page.getByLabel("用户名").fill(`agent_teacher_${suffix}`);
  await page.getByLabel("显示名称").fill("Agent教师");
  await page.getByLabel("密码").fill("StrongPass123!");
  await page.getByRole("button", { name: /教师/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();
  await page.getByRole("button", { name: "我的课程" }).click();
  await page.getByRole("button", { name: "创建教学班" }).click();
  await page.getByLabel("班级名称").fill(`Agent测试班${suffix}`);
  await page.getByRole("button", { name: "确认创建" }).click();
  await page.getByRole("button", { name: `Agent测试班${suffix}` }).click();

  const handle = page.getByRole("button", { name: "Agent 助手" });
  await expect(handle).toBeVisible();
  await handle.click();
  await expect(page.getByRole("heading", { name: "Agent 助手" })).toBeVisible();
  await page.getByRole("button", { name: "小B" }).click();
  await expect(page.getByText("薄弱知识点 Top 5")).toBeVisible();
  await page.getByRole("button", { name: "小C" }).click();
  await expect(page.getByText("作业统计（当前班已发布作业）")).toBeVisible();
  await page.getByRole("button", { name: "返回我的课程" }).click();
  await expect(page.getByRole("heading", { name: "我的课程" })).toBeVisible();
  await expect(page.getByLabel("教师 Agent 助手")).toHaveCount(0);
});
