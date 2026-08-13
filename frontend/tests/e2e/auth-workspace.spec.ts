import { expect, test } from "@playwright/test";

test("双角色注册登录不会残留另一角色导航", async ({ page }) => {
  const suffix = Date.now().toString();
  const learnerUsername = `learner_${suffix}`;
  const teacherUsername = `teacher_${suffix}`;
  const password = "StrongPass123!";

  await page.goto("/");
  await page.getByRole("button", { name: "注册账号" }).click();
  await page.getByLabel("用户名").fill(learnerUsername);
  await page.getByLabel("显示名称").fill("林晓");
  await page.getByLabel("密码").fill(password);
  await page.getByRole("button", { name: /学习者/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();

  await expect(page.getByRole("heading", { name: "我的课程" })).toBeVisible();
  await expect(page.getByTestId("role-badge")).toHaveText("学习者");
  await expect(
    page.getByTestId("primary-navigation").getByRole("button", {
      name: "我的课程",
    }),
  ).toBeVisible();
  await expect(page.getByText("教师工作台")).toHaveCount(0);

  await page.getByRole("button", { name: "退出登录" }).click();
  await expect(page.getByRole("button", { name: "登录" })).toBeVisible();

  await page.getByRole("button", { name: "注册账号" }).click();
  await page.getByLabel("用户名").fill(teacherUsername);
  await page.getByLabel("显示名称").fill("周老师");
  await page.getByLabel("密码").fill(password);
  await page.getByRole("button", { name: /教师/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();

  await expect(page.getByTestId("role-badge")).toHaveText("教师");
  await expect(page.getByText("教师工作台")).toBeVisible();
  await expect(page.getByText("学习者工作台")).toHaveCount(0);

  await page.getByRole("button", { name: "退出登录" }).click();
  await page.getByLabel("用户名").fill(learnerUsername);
  await page.getByLabel("密码").fill(password);
  await page.getByRole("button", { name: "登录" }).click();
  await expect(page.getByTestId("role-badge")).toHaveText("学习者");
  await expect(page.getByText("教师工作台")).toHaveCount(0);

  await page.evaluate(() => {
    window.localStorage.setItem("course-agent-token", "invalid-session");
  });
  await page.reload();
  await expect(page.getByText("登录状态已失效，请重新登录")).toBeVisible();
  await expect(page.getByRole("button", { name: "登录" })).toBeVisible();
});

const operationalStates = [
  {
    status: 403,
    code: "AUTH_ROLE_FORBIDDEN",
    title: "无权访问",
  },
  {
    status: 404,
    code: "RESOURCE_NOT_FOUND",
    title: "资源不存在",
  },
  {
    status: 503,
    code: "INTEGRATION_UNAVAILABLE",
    title: "集成暂不可用",
  },
  {
    status: 500,
    code: "INTERNAL_ERROR",
    title: "服务加载失败",
  },
] as const;

for (const scenario of operationalStates) {
  test(`统一呈现 ${scenario.status} 状态`, async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem("course-agent-token", "test-session");
    });
    await page.route("**/api/auth/me", async (route) => {
      await route.fulfill({
        status: scenario.status,
        contentType: "application/json",
        body: JSON.stringify({
          code: scenario.code,
          message: "测试状态",
          data: null,
          requestId: `state-${scenario.status}`,
        }),
      });
    });

    await page.goto("/");
    await expect(page.getByText(scenario.title, { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "返回登录" })).toBeVisible();
  });
}
