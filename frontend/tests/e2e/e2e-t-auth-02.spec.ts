/**
 * T-AUTH-02 认证失败
 *
 * 覆盖场景：
 *   1) 错误密码 → 401 提示
 *   2) 重复账号注册 → 409 提示
 *   3) 不存在的用户名登录 → 401 提示
 *   4) 网络错误 → 通用错误提示
 *   5) 注入 401 后提示可见且表单可再次提交
 *
 * 规则：先测错误态，后测恢复态
 */
import { expect, test } from "@playwright/test";

const SUFFIX = Date.now().toString();
const EXISTING_USER = `e2e_auth_fail_${SUFFIX}`;
const PASSWORD = "TestPass123!";

test.describe("T-AUTH-02 认证失败", () => {
  /** 先注册一个用户用于失败测试 */
  test.beforeAll(async ({ browser }) => {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    await page.goto("/");

    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(EXISTING_USER);
    await page.getByLabel("显示名称").fill("失败测试用户");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /学习者/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();

    // 确保注册成功
    await expect(page.getByTestId("role-badge")).toHaveText("学习者");

    // 退出
    await page.getByRole("button", { name: "退出登录" }).click();
    await expect(page.getByRole("button", { name: "登录" })).toBeVisible();
    await ctx.close();
  });

  /** 1) 错误密码 → 401 提示可见且表单可再次提交 */
  test("错误密码登录显示错误提示", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("用户名").fill(EXISTING_USER);
    await page.getByLabel("密码").fill("WrongPassword999");
    await page.getByRole("button", { name: "登录" }).click();

    // 验证错误提示可见
    await expect(page.getByRole("alert")).toBeVisible();
    await expect(page.getByRole("alert")).toContainText("用户名或密码错误");

    // 表单可再次提交（输入值保持）
    await expect(page.getByLabel("用户名")).toHaveValue(EXISTING_USER);
    await expect(page.getByLabel("密码")).toHaveValue("WrongPassword999");
  });

  /** 2) 重复账号注册 → 409 提示可见 */
  test("重复用户名注册显示错误提示", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();

    await page.getByLabel("用户名").fill(EXISTING_USER);
    await page.getByLabel("显示名称").fill("重复测试");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /学习者/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();

    // 验证错误提示
    await expect(page.getByRole("alert")).toBeVisible();
    await expect(page.getByRole("alert")).toContainText("用户名已存在");

    // 表单可再次编辑
    await expect(page.getByLabel("用户名")).toHaveValue(EXISTING_USER);
  });

  /** 3) 不存在的用户名登录 → 401 提示 */
  test("不存在的用户名登录显示错误提示", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("用户名").fill("nonexistent_user_xyz");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: "登录" }).click();

    await expect(page.getByRole("alert")).toBeVisible();
    await expect(page.getByRole("alert")).toContainText("用户名或密码错误");
  });

  /** 4) 网络错误 → 通用错误提示 */
  test("网络断开显示通用错误提示", async ({ page }) => {
    // 拦截 /api/auth/login 使其网络失败
    await page.route("**/api/auth/login", (route) => route.abort("connectionrefused"));

    await page.goto("/");
    await page.getByLabel("用户名").fill(EXISTING_USER);
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: "登录" }).click();

    await expect(page.getByRole("alert")).toBeVisible();
    await expect(page.getByRole("alert")).toContainText("服务暂时不可用");

    // 移除拦截后表单可正常提交
    await page.unroute("**/api/auth/login");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: "登录" }).click();
    // 应成功登录
    await expect(page.getByTestId("role-badge")).toHaveText("学习者");
  });

  /** 5) 注册时后端注入 500 - 已在 T-AUTH-01 中覆盖，这里测试 422 边界 */
  test("注册时空用户名触发表单校验", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();

    // 仅填写密码和显示名称，留空用户名
    await page.getByLabel("显示名称").fill("测试名称");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /学习者/ }).click();

    // HTML5 校验应阻止提交，页面不跳转
    const submitBtn = page.getByRole("button", { name: "创建账号" });
    await submitBtn.click({ force: true });

    // 确保仍停留在注册页
    await expect(page.getByRole("heading", { name: "注册账号" })).toBeVisible();
    await expect(page.getByLabel("显示名称")).toHaveValue("测试名称");
  });
});
