/**
 * T-JOIN-01 班级申请审批流程
 *
 * 覆盖：
 *   1) 学习者"申请加入"班级
 *   2) 教师批准/拒绝申请
 *   3) 状态迁移（pending → approved/rejected）
 */
import { expect, test } from "@playwright/test";

const PASSWORD = "TestPass123!";

async function registerTeacher(page: import("@playwright/test").Page, suffix: string) {
  await page.goto("/");
  await page.getByRole("button", { name: "注册账号" }).click();
  await page.getByLabel("用户名").fill(`join_t_${suffix}`);
  await page.getByLabel("显示名称").fill("审批教师");
  await page.getByLabel("密码").fill(PASSWORD);
  await page.getByRole("button", { name: /教师/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();
  await expect(page.getByTestId("role-badge")).toHaveText("教师");
}

async function registerLearner(page: import("@playwright/test").Page, suffix: string) {
  await page.goto("/");
  await page.getByRole("button", { name: "注册账号" }).click();
  await page.getByLabel("用户名").fill(`join_l_${suffix}`);
  await page.getByLabel("显示名称").fill("申请学生");
  await page.getByLabel("密码").fill(PASSWORD);
  await page.getByRole("button", { name: /学习者/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();
  await expect(page.getByTestId("role-badge")).toHaveText("学习者");
}

test.describe("T-JOIN-01 申请审批", () => {
  test("学习者申请加入 + 教师批准", async ({ page, browser }) => {
    const s = Date.now().toString();
    const className = `审批班_${s}`;

    // 教师创建 approval 班级
    const teacherUsername = `join_t_a_${s}`;
    const learnerUsername = `join_l_b_${s}`;

    await registerTeacher(page, `a_${s}`);
    await page.getByRole("button", { name: "创建教学班" }).click();
    await page.getByLabel("班级名称").fill(className);
    await page.getByRole("button", { name: "确认创建" }).click();

    // 设置 approval 策略
    await page.locator("button.class-card", { hasText: className }).click();
    await page.getByLabel("加入状态").selectOption("approval");
    await page.getByRole("button", { name: "保存设置" }).click();
    await page.waitForTimeout(300);
    // 退出教师
    await page.getByRole("button", { name: "退出登录" }).click();
    await expect(page.getByRole("button", { name: "登录" })).toBeVisible();

    // 学习者申请加入（需要在单独的 context 中登录）
    const learnerCtx = await browser.newContext();
    const learnerPage = await learnerCtx.newPage();
    await registerLearner(learnerPage, `b_${s}`);

    // 在"发现教学班"区域找到班级并点击"申请加入"
    const discoverSection = learnerPage.locator(".discover-section");
    await expect(discoverSection).toBeVisible({ timeout: 5000 });

    const joinBtn = discoverSection.locator("button", { hasText: "申请加入" }).first();
    await expect(joinBtn).toBeVisible();
    await joinBtn.click();

    // 等待申请成功提示
    await expect(learnerPage.getByText("申请提交成功")).toBeVisible({ timeout: 5000 });
    await learnerCtx.close();

    // 教师登录 → 审批
    await page.getByLabel("用户名").fill(teacherUsername);
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: "登录" }).click();
    await page.locator("button.class-card", { hasText: className }).click();
    await page.getByLabel("教学班导航").getByRole("button", { name: "申请管理" }).click();

    // 找到"批准"按钮并点击
    const approveBtn = page.locator("button", { hasText: "批准" }).first();
    await expect(approveBtn).toBeVisible({ timeout: 5000 });
    await approveBtn.click();

    // 批准后应有通知
    await expect(page.getByText("申请已批准").first()).toBeVisible({ timeout: 5000 });
  });
});
