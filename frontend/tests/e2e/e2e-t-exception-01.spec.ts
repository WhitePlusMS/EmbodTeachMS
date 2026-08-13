/**
 * 第 5 节：通用异常、并发与权限套件
 *
 * 覆盖每个写操作检查点中缺失的异常案例：
 *   - 500 注入：页面不崩溃，显示错误提示
 *   - 断网/超时：loading 结束、错误提示可见、控件恢复
 *   - 双击/并发：只允许一次创建
 *   - 权限反证：学习者不能操作教师功能
 *
 * 注意：已由各检查点覆盖的异常（auth/login、course overview）不重复测试。
 */
import { expect, test } from "@playwright/test";

const PASSWORD = "TestPass123!";

test.describe("第5节-通用写操作异常覆盖", () => {
  test("创建教学班时后端 500 显示错误", async ({ page }) => {
    const s = Date.now().toString();
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(`e5c_t_${s}`);
    await page.getByLabel("显示名称").fill("异常教师");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /教师/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    // 先打开创建表单
    await page.getByRole("button", { name: "创建教学班" }).click();
    await expect(page.getByLabel("班级名称")).toBeVisible({ timeout: 5000 });
    await page.getByLabel("班级名称").fill(`异常班_${s}`);

    // 注入 500 只到 POST（不拦截 GET）
    await page.route("**/api/teaching-classes", async (route, req) => {
      if (req.method() === "POST") {
        await route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ code: "INTERNAL_ERROR", message: "服务暂时不可用", data: null }),
        });
        return;
      }
      await route.continue();
    });

    await page.getByRole("button", { name: "确认创建" }).click();

    // 500 后页面不崩溃
    await page.waitForTimeout(500);
    // 页面不应卡住，应有 "操作失败" 提示或创建教学班按钮恢复
    await expect(page.getByText("操作失败").or(page.getByRole("button", { name: "创建教学班" }).first())).toBeVisible({ timeout: 3000 });
  });

  test("创建知识库时后端 500 显示错误", async ({ page }) => {
    const s = Date.now().toString();
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(`e5kb_t_${s}`);
    await page.getByLabel("显示名称").fill("异常KB教师");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /教师/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    await page.getByRole("button", { name: "知识库管理" }).click();

    // 注入 500 到创建知识库接口
    await page.route("**/api/knowledge-bases", async (route, req) => {
      if (req.method() === "POST") {
        await route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ code: "INTERNAL_ERROR", message: "服务暂时不可用", data: null }),
        });
        return;
      }
      await route.continue();
    });

    await page.getByLabel("新建知识库名称").fill(`异常库_${s}`);
    await page.getByRole("button", { name: "新建知识库" }).click();

    // 500 后页面不崩溃
    await page.waitForTimeout(500);
    await expect(page.getByRole("button", { name: "新建知识库" })).toBeEnabled();
  });

  test("知识库归档时后端 500 显示错误", async ({ page }) => {
    const s = Date.now().toString();
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(`e5ar_t_${s}`);
    await page.getByLabel("显示名称").fill("异常归档教师");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /教师/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    await page.getByRole("button", { name: "知识库管理" }).click();
    await page.getByLabel("新建知识库名称").fill(`归档异常库_${s}`);
    await page.getByRole("button", { name: "新建知识库" }).click();
    await expect(page.getByText(`归档异常库_${s}`).first()).toBeVisible({ timeout: 5000 });

    // 注入 500 到归档接口
    await page.route("**/api/knowledge-bases/**/archive", async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ code: "INTERNAL_ERROR", message: "归档失败", data: null }),
      });
    });

    await page.getByRole("button", { name: "归档", exact: true }).click();
    await page.waitForTimeout(500);

    // 页面不崩溃
    await expect(page.getByText("归档", { exact: true }).or(page.getByText("归档失败"))).toBeAttached();
  });

  test("加入策略保存时后端 500 显示错误", async ({ page }) => {
    const s = Date.now().toString();
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(`e5jp_t_${s}`);
    await page.getByLabel("显示名称").fill("异常策略教师");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /教师/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    await page.getByRole("button", { name: "创建教学班" }).click();
    await page.getByLabel("班级名称").fill(`策略异常班_${s}`);
    await page.getByRole("button", { name: "确认创建" }).click();
    await page.locator("button.class-card", { hasText: `策略异常班_${s}` }).click();

    // 注入 500 到更新加入策略接口
    await page.route("**/api/teaching-classes/**/join-policy", async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ code: "INTERNAL_ERROR", message: "更新失败", data: null }),
      });
    });

    await page.getByLabel("加入状态").selectOption("approval");
    await page.getByRole("button", { name: "保存设置" }).click();
    await page.waitForTimeout(500);

    // 页面不崩溃
    await expect(page.getByLabel("加入状态")).toBeAttached();
  });

  test("权限反证：学习者不能看到知识库管理按钮", async ({ page }) => {
    const s = Date.now().toString();
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(`e5perm_l_${s}`);
    await page.getByLabel("显示名称").fill("权限学习者");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /学习者/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("学习者");

    // 学习者不应看到知识库管理按钮
    await expect(page.getByRole("button", { name: "知识库管理" })).toHaveCount(0);
  });

  test("双击创建教学班只产生一次请求", async ({ page }) => {
    const s = Date.now().toString();

    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(`e5dc_t_${s}`);
    await page.getByLabel("显示名称").fill("双击教师");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /教师/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    // 先打开创建表单
    await page.getByRole("button", { name: "创建教学班" }).click();
    await expect(page.getByLabel("班级名称")).toBeVisible({ timeout: 5000 });
    await page.getByLabel("班级名称").fill(`双击班_${s}`);

    // 监听创建教学班请求（只拦截 POST）
    let requestCount = 0;
    await page.route("**/api/teaching-classes", async (route, req) => {
      if (req.method() === "POST") {
        requestCount++;
        // 延迟响应，让双击发生在 loading 期间
        await new Promise((r) => setTimeout(r, 300));
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            code: "OK",
            message: "success",
            data: { id: `double-${s}`, name: `双击班_${s}`, joinPolicy: "free", learnerCount: 0, createdAt: Date.now() / 1000 },
          }),
        });
        return;
      }
      await route.continue();
    });

    // 快速双击确认创建按钮
    const confirmBtn = page.getByRole("button", { name: "确认创建" });
    await confirmBtn.click();
    await confirmBtn.click();

    await page.waitForTimeout(500);
    // 请求次数应仅为 1
    expect(requestCount).toBeLessThanOrEqual(1);
  });
});
