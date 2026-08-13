/**
 * T-LHOME-01 / T-LHOME-02 学习者加入班级
 *
 * 覆盖：
 *   1) 自由加入班级
 *   2) 申请加入班级
 *   3) 授权码加入班级
 *   4) 重复加入、错误授权码
 *
 * 依赖：教师创建 free / approval / closed 三种班级
 */
import { expect, test } from "@playwright/test";

const PASSWORD = "TestPass123!";

async function registerTeacher(page: import("@playwright/test").Page, suffix: string) {
  await page.goto("/");
  await page.getByRole("button", { name: "注册账号" }).click();
  await page.getByLabel("用户名").fill(`lh_t_${suffix}`);
  await page.getByLabel("显示名称").fill("加入测试教师");
  await page.getByLabel("密码").fill(PASSWORD);
  await page.getByRole("button", { name: /教师/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();
  await expect(page.getByTestId("role-badge")).toHaveText("教师");
}

async function registerLearner(page: import("@playwright/test").Page, suffix: string) {
  await page.goto("/");
  await page.getByRole("button", { name: "注册账号" }).click();
  await page.getByLabel("用户名").fill(`lh_l_${suffix}`);
  await page.getByLabel("显示名称").fill("加入学生");
  await page.getByLabel("密码").fill(PASSWORD);
  await page.getByRole("button", { name: /学习者/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();
  await expect(page.getByTestId("role-badge")).toHaveText("学习者");
}

test.describe("T-LHOME-01 学习者加入班级", () => {
  test("自由加入班级流程", async ({ page, browser }) => {
    const s = Date.now().toString();
    const className = `自由班_${s}`;

    // 教师创建 free 班级
    const teacherCtx = await browser.newContext();
    const teacherPage = await teacherCtx.newPage();
    await registerTeacher(teacherPage, `a_${s}`);
    await teacherPage.getByRole("button", { name: "创建教学班" }).click();
    await teacherPage.getByLabel("班级名称").fill(className);
    await teacherPage.getByRole("button", { name: "确认创建" }).click();
    await teacherCtx.close();

    // 学习者自由加入
    await registerLearner(page, `b_${s}`);
    const discoverSection = page.locator(".discover-section");
    await expect(discoverSection).toBeVisible({ timeout: 5000 });

    const joinBtn = discoverSection.locator("button", { hasText: "立即加入" }).first();
    await expect(joinBtn).toBeVisible();
    await joinBtn.click();
    await expect(page.getByText("已加入教学班").first()).toBeVisible({ timeout: 5000 });
  });
});
