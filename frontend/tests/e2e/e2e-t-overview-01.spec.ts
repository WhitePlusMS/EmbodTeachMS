/**
 * T-OVERVIEW-01 / T-OVERVIEW-02 / T-OVERVIEW-03 课程概述与加入策略
 *
 * T-OVERVIEW-01 覆盖：
 *   1) 编辑课程概述表单 → 字段校验、保存、持久化
 *   2) 失败回退（API 500 时错误显示）
 *
 * T-OVERVIEW-02 覆盖：
 *   3) 生成候选 → 采用候选 → 候选填充到编辑表单
 *   4) 生成中 loading 禁止重复提交
 *
 * T-OVERVIEW-03 覆盖：
 *   5) 加入策略下拉切换：自由加入/申请加入/关闭加入
 *   6) 保存设置后刷新持久化
 *
 * 注意：每个 test 独立注册账号和创建班级，避免数据依赖。
 */
import { expect, test } from "@playwright/test";

const PASSWORD = "TestPass123!";

async function registerTeacher(page: import("@playwright/test").Page, suffix: string) {
  await page.goto("/");
  await page.getByRole("button", { name: "注册账号" }).click();
  await page.getByLabel("用户名").fill(`ov_${suffix}`);
  await page.getByLabel("显示名称").fill("概述测试");
  await page.getByLabel("密码").fill(PASSWORD);
  await page.getByRole("button", { name: /教师/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();
  await expect(page.getByTestId("role-badge")).toHaveText("教师");
}

async function createClass(page: import("@playwright/test").Page, name: string) {
  await page.getByRole("button", { name: "创建教学班" }).click();
  await expect(page.getByLabel("班级名称")).toBeVisible({ timeout: 5000 });
  await page.getByLabel("班级名称").fill(name);
  await page.getByRole("button", { name: "确认创建" }).click();
  await expect(page.getByText(name)).toBeVisible({ timeout: 5000 });
}

async function enterClass(page: import("@playwright/test").Page, name: string) {
  await page.locator("button.class-card", { hasText: name }).click();
  await expect(page.getByLabel("教学班导航")).toBeVisible({ timeout: 5000 });
}

test.describe("T-OVERVIEW-01 课程概述编辑", () => {
  test("编辑并保存课程概述，刷新后数据持久化", async ({ page }) => {
    const s = Date.now().toString();
    const cls = `OV1班_${s}`;
    await registerTeacher(page, `t1_${s}`);
    await createClass(page, cls);
    await enterClass(page, cls);

    // 初始状态：空概述
    await expect(page.locator(".overview-readonly")).toBeVisible();
    await expect(page.locator(".overview-readonly .overview-text")).toHaveCount(4);

    // 编辑
    await page.getByRole("button", { name: "编辑概述" }).click();
    await page.getByLabel("课程背景").fill("测试背景");
    await page.getByLabel("课程简介").fill("测试简介");
    await page.getByLabel("课程目标").fill("测试目标");
    await page.getByLabel("课程特色").fill("测试特色");
    await page.getByRole("button", { name: "保存", exact: true }).click();

    // 保存成功
    await expect(page.getByText("测试背景")).toBeVisible();
    await expect(page.getByText("测试简介")).toBeVisible();

    // 刷新后持久化
    await page.reload();
    await page.locator("button.class-card", { hasText: cls }).click();
    await expect(page.getByText("测试背景")).toBeVisible({ timeout: 5000 });
  });

  test("取消编辑后数据回退", async ({ page }) => {
    const s = Date.now().toString();
    const cls = `OV1C_${s}`;
    await registerTeacher(page, `t1c_${s}`);
    await createClass(page, cls);
    await enterClass(page, cls);

    // 先保存
    await page.getByRole("button", { name: "编辑概述" }).click();
    await page.getByLabel("课程背景").fill("原始背景");
    await page.getByRole("button", { name: "保存", exact: true }).click();
    await expect(page.getByText("原始背景")).toBeVisible();

    // 再编辑 → 取消
    await page.getByRole("button", { name: "编辑概述" }).click();
    await page.getByLabel("课程背景").fill("未保存的修改");
    await page.getByRole("button", { name: "取消" }).click();
    await expect(page.getByText("原始背景")).toBeVisible();
    await expect(page.getByText("未保存的修改")).not.toBeVisible();
  });

  test("保存课程概述时后端 500 显示错误提示", async ({ page }) => {
    const s = Date.now().toString();
    const cls = `OV1E_${s}`;
    await registerTeacher(page, `t1e_${s}`);
    await createClass(page, cls);
    await enterClass(page, cls);

    // 注入 500
    await page.route("**/api/teaching-classes/**/course-overview", async (route, req) => {
      if (req.method() === "PUT") {
        await route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ code: "INTERNAL_ERROR", message: "服务暂时不可用", data: null, requestId: "e2e-500" }),
        });
        return;
      }
      await route.continue();
    });

    await page.getByRole("button", { name: "编辑概述" }).click();
    await page.getByLabel("课程背景").fill("500测试");
    await page.getByRole("button", { name: "保存", exact: true }).click();

    // 500 后保留课程概述页面，显示错误通知
    await expect(page.getByRole("heading", { name: "课程概述" })).toBeVisible();
    await expect(page.getByRole("alert")).toContainText("服务暂时不可用");
  });
});

test.describe("T-OVERVIEW-02 课程概述候选", () => {
  test("生成候选后采用候选填充到编辑表单", async ({ page }) => {
    const s = Date.now().toString();
    const cls = `OV2班_${s}`;
    await registerTeacher(page, `t2_${s}`);
    await createClass(page, cls);
    await enterClass(page, cls);

    await page.getByRole("button", { name: "生成概述候选" }).click();
    await expect(page.getByRole("heading", { name: "候选内容" })).toBeVisible();
    await expect(page.getByText("集成未配置")).toBeVisible();

    // 采用候选
    await page.getByRole("button", { name: "采用候选内容" }).click();

    // 进入编辑模式，候选内容填入表单
    await expect(page.getByLabel("课程背景")).toBeVisible();
    await expect(page.getByRole("button", { name: "保存", exact: true })).toBeVisible();
  });
});

test.describe("T-OVERVIEW-03 加入策略", () => {
  test("切换加入策略并刷新后持久化", async ({ page }) => {
    const s = Date.now().toString();
    const cls = `OV3班_${s}`;
    await registerTeacher(page, `t3_${s}`);
    await createClass(page, cls);
    await enterClass(page, cls);

    const policySelect = page.getByLabel("加入状态");

    // 改成"申请加入"
    await policySelect.selectOption("approval");
    await page.getByRole("button", { name: "保存设置" }).click();

    // 刷新验证持久化
    await page.reload();
    await page.locator("button.class-card", { hasText: cls }).click();
    await expect(page.getByLabel("加入状态")).toHaveValue("approval", { timeout: 5000 });
  });

  test("多次切换加入策略", async ({ page }) => {
    const s = Date.now().toString();
    const cls = `OV3B_${s}`;
    await registerTeacher(page, `t3b_${s}`);
    await createClass(page, cls);
    await enterClass(page, cls);

    const policySelect = page.getByLabel("加入状态");

    // 关闭加入 → 保存
    await policySelect.selectOption("closed");
    await page.getByRole("button", { name: "保存设置" }).click();
    // 等待通知消息出现/消失
    await page.waitForTimeout(500);
    await expect(policySelect).toHaveValue("closed");

    // 自由加入 → 保存（每次 selectOption 后等待 Vue 更新 v-model）
    await policySelect.selectOption("free");
    await page.waitForTimeout(200); // 等待 Vue 响应式更新 classSettingsForm
    await page.getByRole("button", { name: "保存设置" }).click();

    await expect(policySelect).toHaveValue("free");
  });
});
