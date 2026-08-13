/**
 * T-AGENT-01 TeacherAgentDrawer 测试
 *
 * 覆盖：展开/收起、@小A/@小B/@小C 切换，以及三个助手的真实操作入口
 */
import { expect, test } from "@playwright/test";

const PASSWORD = "TestPass123!";

async function registerTeacher(page: import("@playwright/test").Page, suffix: string) {
  await page.goto("/");
  await page.getByRole("button", { name: "注册账号" }).click();
  await page.getByLabel("用户名").fill(`agent_t_${suffix}`);
  await page.getByLabel("显示名称").fill("Agent教师");
  await page.getByLabel("密码").fill(PASSWORD);
  await page.getByRole("button", { name: /教师/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();
  await expect(page.getByTestId("role-badge")).toHaveText("教师");
}

test.describe("T-AGENT-01 Agent 助手", () => {
  test("Agent 助手可展开和收起", async ({ page }) => {
    const s = Date.now().toString();
    await registerTeacher(page, `a_${s}`);
    await page.getByRole("button", { name: "创建教学班" }).click();
    await page.getByLabel("班级名称").fill(`Agent班_${s}`);
    await page.getByRole("button", { name: "确认创建" }).click();
    await page.getByRole("button", { name: new RegExp(`Agent班_${s}`) }).click();

    // 小 A 的出题能力只在右侧助手中提供；空班没有重点时保持禁用并给出前置操作。
    await page.getByRole("button", { name: "AI 助手" }).click();
    await expect(page.getByText("@小A")).toBeVisible({ timeout: 5000 });
    await expect(page.getByLabel("小A备课出题助手").getByRole("button", { name: "基于重点生成候选题" })).toBeDisabled();
    await expect(page.getByRole("button", { name: "前往课件备课标注重点" })).toBeVisible();

    // 小 B、小 C 均提供真实数据刷新入口，不再只是静态测试文案。
    await page.getByRole("button", { name: "@小B" }).click();
    await expect(page.getByRole("button", { name: "刷新分析" })).toBeVisible();
    await expect(page.getByText(/暂无薄弱知识点|班级分析事实/)).toBeVisible({ timeout: 5000 });
    await page.getByRole("button", { name: "@小C" }).click();
    await expect(page.getByRole("button", { name: "刷新作业" })).toBeVisible();
    await expect(page.getByText(/暂无已发布作业|当前班作业与学习者/)).toBeVisible({ timeout: 5000 });

    await page.getByRole("button", { name: "收起 AI 助手" }).click();

    // 关闭后 drawer 有 closed class（transform 移出视图）
    // 检查 drawer 的 aria-hidden 属性
    const drawer = page.getByLabel("教师 Agent 助手").locator("aside");
    await expect(drawer).toHaveAttribute("aria-hidden", "true");
  });
});
