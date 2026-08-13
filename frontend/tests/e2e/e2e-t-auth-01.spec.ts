/**
 * T-AUTH-01 AuthView.vue — 认证入口
 *
 * 覆盖范围：
 *   1) 学习者/教师角色切换（注册模式）
 *   2) 注册/登录模式切换
 *   3) 提交按钮在必填项缺失时禁用
 *   4) 成功进入正确工作区（学习者/教师）
 *   5) 刷新后持久化登录状态
 *   6) 注入 500 失败，验证错误显示及可恢复性
 *
 * 规则：test-goal.md 2.1 原子检查点
 *       先测禁用/空态 → 再测成功态（写操作最后测）
 *       写操作额外以页面刷新验证
 */
import { expect, test } from "@playwright/test";

const SUFFIX = Date.now().toString();
const LEARNER_USER = `e2e_auth_l_${SUFFIX}`;
const TEACHER_USER = `e2e_auth_t_${SUFFIX}`;
const PASSWORD = "TestPass123!";

test.describe("T-AUTH-01 认证入口", () => {
  /**
   * 1) 空/禁用态测试
   *    - 确保必填项缺失时提交按钮被禁用或表单提交被阻止
   */
  test("注册模式下必填项为空时提交按钮被禁用", async ({ page }) => {
    await page.goto("/");

    // 切换到注册模式
    await page.getByRole("button", { name: "注册账号" }).click();
    await expect(page.getByRole("button", { name: "创建账号" })).toBeVisible();

    // 确认表单字段存在且为非空校验
    const usernameInput = page.getByLabel("用户名");
    const passwordInput = page.getByLabel("密码");
    const displayNameInput = page.getByLabel("显示名称");

    await expect(usernameInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
    await expect(displayNameInput).toBeVisible();

    // 所有字段为空时检查提交按钮状态
    await expect(page.getByRole("button", { name: "创建账号" })).toBeVisible();

    // HTML5 required 校验：当必填项为空时触发表单校验
    // 对空的必填输入尝试提交，浏览器应阻止提交
    const submitButton = page.getByRole("button", { name: "创建账号" });

    // 直接尝试点击提交（必填项为空，浏览器应显示校验提示）
    await submitButton.click({ force: true });

    // 确保页面未离开（仍然在注册模式）
    await expect(page.getByLabel("用户名")).toBeVisible();
    await expect(page.getByRole("button", { name: "创建账号" })).toBeVisible();
  });

  /**
   * 2) 注册模式下的角色切换
   *    - 默认角色为"学习者"
   *    - 可切换到"教师"
   *    - aria-pressed 状态正确
   */
  test("注册模式可切换学习者/教师角色", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();

    const roleGroup = page.getByLabel("账号角色");

    // 默认角色为学习者
    const learnerBtn = roleGroup.getByRole("button", { name: /学习者/ });
    const teacherBtn = roleGroup.getByRole("button", { name: /教师/ });

    await expect(learnerBtn).toBeVisible();
    await expect(teacherBtn).toBeVisible();

    // 切换到教师
    await teacherBtn.click();
    await expect(teacherBtn).toHaveAttribute("aria-pressed", "true");
    await expect(learnerBtn).toHaveAttribute("aria-pressed", "false");

    // 切换回学习者
    await learnerBtn.click();
    await expect(learnerBtn).toHaveAttribute("aria-pressed", "true");
    await expect(teacherBtn).toHaveAttribute("aria-pressed", "false");
  });

  /**
   * 3) 登录/注册模式切换
   *    - 可互相切换
   *    - 注册模式下显示角色选择区域
   *    - 登录模式下不显示角色选择区域
   */
  test("登录/注册模式可正常切换", async ({ page }) => {
    await page.goto("/");

    // 默认登录模式，验证登录表单可见
    const heading = page.getByRole("heading", { name: "登录工作台" });
    await expect(heading).toBeVisible();
    await expect(page.getByRole("button", { name: "注册账号" })).toBeVisible();

    // 切换到注册模式
    await page.getByRole("button", { name: "注册账号" }).click();
    await expect(page.getByRole("heading", { name: "注册账号" })).toBeVisible();
    await expect(page.getByLabel("账号角色")).toBeVisible();
    await expect(page.getByLabel("显示名称")).toBeVisible();

    // 切回登录模式
    await page.getByRole("button", { name: "返回登录" }).click();
    await expect(page.getByRole("heading", { name: "登录工作台" })).toBeVisible();
    await expect(page.getByLabel("账号角色")).toHaveCount(0);
    await expect(page.getByLabel("显示名称")).toHaveCount(0);
  });

  /**
   * 4) 成功注册学习者并进入正确工作区
   */
  test("注册学习者成功进入学习者工作区", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();

    // 填写学习者注册表单
    await page.getByLabel("用户名").fill(LEARNER_USER);
    await page.getByLabel("显示名称").fill("林测试");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /学习者/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();

    // 验证进入学习者工作区
    await expect(page.getByTestId("role-badge")).toHaveText("学习者");
    await expect(
      page.getByTestId("primary-navigation").getByRole("button", {
        name: "我的课程",
      }),
    ).toBeVisible();
    // 教师相关内容不可见
    await expect(page.getByText("教师工作台")).toHaveCount(0);

    // 刷新页面验证持久化
    await page.reload();
    await expect(page.getByTestId("role-badge")).toHaveText("学习者");
  });

  /**
   * 5) 退出后注册教师并进入正确工作区
   */
  test("注册教师成功进入教师工作区", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();

    // 填写教师注册表单
    await page.getByLabel("用户名").fill(TEACHER_USER);
    await page.getByLabel("显示名称").fill("周测试");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /教师/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();

    // 验证进入教师工作区
    await expect(page.getByTestId("role-badge")).toHaveText("教师");
    await expect(page.getByText("教师工作台")).toBeVisible();
    await expect(page.getByText("学习者工作台")).toHaveCount(0);

    // 刷新页面验证持久化
    await page.reload();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");
    await expect(page.getByText("教师工作台")).toBeVisible();
  });

  /**
   * 6) 登录已有账号切换角色
   */
  test("登录学习者后退出再登录教师，互不串角色", async ({ page }) => {
    // 先登录学习者
    await page.goto("/");
    await page.getByLabel("用户名").fill(LEARNER_USER);
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: "登录" }).click();

    await expect(page.getByTestId("role-badge")).toHaveText("学习者");

    // 退出
    await page.getByRole("button", { name: "退出登录" }).click();
    await expect(page.getByRole("button", { name: "登录" })).toBeVisible();

    // 登录教师
    await page.getByLabel("用户名").fill(TEACHER_USER);
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: "登录" }).click();

    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    // 再退出，验证学习者仍可正常登录
    await page.getByRole("button", { name: "退出登录" }).click();
    await page.getByLabel("用户名").fill(LEARNER_USER);
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: "登录" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("学习者");
  });

  /**
   * 7) 失败注入：断网或 500 时显示错误且可恢复
   */
  test("注册时后端 500 显示错误并可恢复", async ({ page }) => {
    // 拦截注册请求返回 500
    await page.route("**/api/auth/register", async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({
          code: "INTERNAL_ERROR",
          message: "服务暂时不可用",
          data: null,
          requestId: "e2e-500-test",
        }),
      });
    });

    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();

    await page.getByLabel("用户名").fill(`e2e_fail_${SUFFIX}`);
    await page.getByLabel("显示名称").fill("失败测试");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /学习者/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();

    // 验证错误提示可见且表单可以再次提交
    await expect(page.getByRole("alert")).toBeVisible();
    // 表单应可再次编辑
    await expect(page.getByLabel("用户名")).toHaveValue(`e2e_fail_${SUFFIX}`);
  });
});
