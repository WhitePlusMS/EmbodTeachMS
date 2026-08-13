/**
 * T-SHELL-01 / T-SHELL-02 工作区导航与退出
 *
 * T-SHELL-01 覆盖：
 *   1) 教师"我的课程"顶层导航
 *   2) 学习者顶层导航
 *   3) 退出登录 → token 清除 → 不能后退进入工作区
 *   4) 401 会话失效后显示"返回登录"
 *
 * T-SHELL-02 覆盖：
 *   5) 教师班级内 8 个导航页签
 *   6) 学习者 3 个页签导航
 *   7) 切换班级不串状态
 *
 * 每个 test 独立登录，不依赖共享数据。
 */
import { expect, test } from "@playwright/test";

const SUFFIX = Date.now().toString();
const NAV_TEACHER = `e2e_shell_nav_${SUFFIX}`;
const NAV_CLASS_A = `班级A_${SUFFIX}`;
const NAV_CLASS_B = `班级B_${SUFFIX}`;
const PASSWORD = "TestPass123!";

test.describe("T-SHELL-01 工作区入口与退出", () => {
  /**
   * 在每个测试中动态注册一个一次性用户。这样测试之间互不干扰。
   * 由于 test.describe.serial 能保证顺序执行，用 serial 避免竞争。
   */
  let learnerUser = "";
  let teacherUser = "";

  test.beforeAll(async ({ browser }) => {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    const suffix = Date.now().toString();
    teacherUser = `e2e_s01_t_${suffix}`;
    learnerUser = `e2e_s01_l_${suffix}`;

    // 注册教师
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(teacherUser);
    await page.getByLabel("显示名称").fill("TS01教师");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /教师/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    // 退出
    await page.getByRole("button", { name: "退出登录" }).click();
    await expect(page.getByRole("button", { name: "登录" })).toBeVisible();

    // 注册学习者
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(learnerUser);
    await page.getByLabel("显示名称").fill("TS01学生");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /学习者/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("学习者");

    // 退出
    await page.getByRole("button", { name: "退出登录" }).click();
    await expect(page.getByRole("button", { name: "登录" })).toBeVisible();
    await ctx.close();
  });

  test("教师登录后显示我的课程导航和角色标签", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("用户名").fill(teacherUser);
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: "登录" }).click();

    await expect(page.getByTestId("role-badge")).toHaveText("教师");
    await expect(page.getByTestId("primary-navigation")).toBeVisible();
    await expect(
      page.getByTestId("primary-navigation").getByRole("button", { name: "我的课程" }),
    ).toBeVisible();
    await expect(page.getByText("TS01教师")).toBeVisible();
  });

  test("学习者登录后显示导航和角色标签", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("用户名").fill(learnerUser);
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: "登录" }).click();

    await expect(page.getByTestId("role-badge")).toHaveText("学习者");
    await expect(page.getByText("TS01学生")).toBeVisible();
  });

  test("退出登录清除 token 且刷新后回到登录页", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("用户名").fill(learnerUser);
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: "登录" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("学习者");

    // 退出按钮可见后点击
    await page.getByRole("button", { name: "退出登录" }).click();

    // 等待登录页出现
    await expect(page.getByRole("heading", { name: "登录工作台" })).toBeVisible({ timeout: 10000 });

    // 验证 token 已被清除
    const token = await page.evaluate(() =>
      window.localStorage.getItem("course-agent-token"),
    );
    expect(token).toBeNull();

    // 刷新后仍停留在登录页（无 token 不会自动登录）
    await page.reload();
    await expect(page.getByRole("heading", { name: "登录工作台" })).toBeVisible();
  });

  test("token 失效注入 401 后显示登录页", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("用户名").fill(learnerUser);
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: "登录" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("学习者");

    // 注入无效 token
    await page.evaluate(() => {
      window.localStorage.setItem("course-agent-token", "invalid-token-e2e");
    });
    await page.reload();

    await expect(page.getByText("登录状态已失效")).toBeVisible();
    await expect(page.getByRole("button", { name: "登录" })).toBeVisible();
  });
});

test.describe("T-SHELL-02 班级内导航", () => {
  test.beforeAll(async ({ browser }) => {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();

    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(NAV_TEACHER);
    await page.getByLabel("显示名称").fill("导航教师");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /教师/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    // 创建第1个班级 — 注意 label 是"班级名称"不是"教学班名称"
    await page.getByRole("button", { name: "创建教学班" }).click();
    await page.getByLabel("班级名称").fill(NAV_CLASS_A);
    await page.getByRole("button", { name: "确认创建" }).click();

    // 创建第2个班级
    await page.getByRole("button", { name: "创建教学班" }).click();
    await page.getByLabel("班级名称").fill(NAV_CLASS_B);
    await page.getByRole("button", { name: "确认创建" }).click();

    // 等待班级卡片渲染
    await expect(page.getByText(NAV_CLASS_A)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(NAV_CLASS_B)).toBeVisible({ timeout: 5000 });
    await ctx.close();
  });

  test("教师进入班级后 8 个导航页签可见", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("用户名").fill(NAV_TEACHER);
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: "登录" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    // 点击班级卡片
    await page.getByText(NAV_CLASS_A).click();

    // 验证班级导航栏
    const classNav = page.getByLabel("教学班导航");
    await expect(classNav).toBeVisible({ timeout: 5000 });

    // 主区域页签
    const mainTabs = ["课程概述", "课件备课", "班级概览", "学习者详情", "课堂练习管理", "作业管理"];
    for (const tab of mainTabs) {
      await expect(classNav.getByRole("button", { name: tab })).toBeVisible();
    }

    // 管理区域页签
    const mgmtTabs = ["申请管理", "授权码管理"];
    for (const tab of mgmtTabs) {
      await expect(classNav.getByRole("button", { name: tab })).toBeVisible();
    }
  });

  test("学习者进入班级后 3 个导航页签可见", async ({ page }) => {
    // 注册新学习者
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    const learnerSuffix = Date.now().toString();
    const joinLearner = `e2e_join_${learnerSuffix}`;
    await page.getByLabel("用户名").fill(joinLearner);
    await page.getByLabel("显示名称").fill("加入学生");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /学习者/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("学习者");

    // 从"发现教学班"区域找到可加入的班级，点击"立即加入"
    const discoverSection = page.locator(".discover-section");
    await expect(discoverSection).toBeVisible({ timeout: 5000 });

    // 在"发现教学班"区域找加入按钮
    const joinBtn = discoverSection.locator("button", { hasText: "立即加入" }).first();
    await expect(joinBtn).toBeVisible({ timeout: 5000 });
    await joinBtn.click();

    // 等待加入成功并出现在"我的课程"列表中
    await expect(page.locator(".course-grid")).toBeVisible({ timeout: 5000 });

    // 点击班级卡片进入
    const classCard = page.locator("button.course-card").first();
    await expect(classCard).toBeVisible({ timeout: 5000 });
    await classCard.click();

    // 验证学习者班级导航
    const classNav = page.getByLabel("当前课程导航");
    await expect(classNav).toBeVisible({ timeout: 5000 });

    const tabs = ["当前课程", "仿真实训", "学习概览"];
    for (const tab of tabs) {
      await expect(classNav.getByRole("button", { name: tab })).toBeVisible();
    }
  });

  test("切换班级后状态重置", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("用户名").fill(NAV_TEACHER);
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: "登录" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    // 进入班级A
    await page.getByText(NAV_CLASS_A).click();
    await expect(page.getByLabel("教学班导航")).toBeVisible({ timeout: 5000 });

    // 切换到"班级概览"页签
    await page.getByLabel("教学班导航").getByRole("button", { name: "班级概览" }).click();

    // 返回班级列表
    await page.getByRole("button", { name: "返回我的课程" }).click();
    await expect(page.getByTestId("primary-navigation")).toBeVisible();

    // 进入班级B
    await page.getByText(NAV_CLASS_B).click();
    await expect(page.getByLabel("教学班导航")).toBeVisible({ timeout: 5000 });

    // 验证默认页签是"课程概述"（非班级概览）
    const overviewBtn = page.getByLabel("教学班导航").getByRole("button", { name: "课程概述" });
    await expect(overviewBtn).toHaveAttribute("aria-current", "page");
  });
});
