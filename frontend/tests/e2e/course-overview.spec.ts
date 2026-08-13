import { expect, test } from "@playwright/test";

const PASSWORD = "TestPass123!";

test("教师可维护课程概述并在刷新后保持", async ({ page }) => {
  const suffix = Date.now().toString();

  await page.goto("/");
  await page.getByRole("button", { name: "注册账号" }).click();
  await page.getByLabel("用户名").fill(`course_overview_teacher_${suffix}`);
  await page.getByLabel("显示名称").fill("课程概述教师");
  await page.getByLabel("密码").fill(PASSWORD);
  await page.getByRole("button", { name: /教师/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();

  const className = `课程概述测试班${suffix}`;
  await page.getByRole("button", { name: "创建教学班" }).click();
  await expect(page.getByLabel("班级名称")).toBeVisible({ timeout: 5000 });
  await page.getByLabel("班级名称").fill(className);
  await page.getByRole("button", { name: "确认创建" }).click();

  // 点击班级卡片进入（用 class-card 避免 strict 冲突）
  await page.locator("button.class-card", { hasText: className }).click();

  await expect(page.getByRole("heading", { name: "课程概述" })).toBeVisible();
  await expect(page.locator(".stat-card > strong")).toHaveCount(5);
  await expect(page.locator(".stat-card > strong").filter({ hasText: "0" })).toHaveCount(5);
  // 课程概述未填写时，4 个 overview-text paragraph 均为空
  await expect(page.locator(".overview-readonly .overview-text")).toHaveCount(4);

  // 生成概述候选（无LLM配置时返回降级候选）
  await page.getByRole("button", { name: "生成概述候选" }).click();
  await expect(page.getByRole("heading", { name: "候选内容" })).toBeVisible();
  await expect(page.getByText("集成未配置")).toBeVisible();
  await page.getByRole("button", { name: "放弃候选" }).click();
  await expect(page.getByRole("heading", { name: "候选内容" })).not.toBeVisible();

  // 编辑并保存课程概述
  await page.getByRole("button", { name: "编辑概述" }).click();
  await page.getByLabel("课程背景").fill("这是课程的背景介绍");
  await page.getByLabel("课程简介").fill("这是课程的简介内容");
  await page.getByLabel("课程目标").fill("这是课程的学习目标");
  await page.getByLabel("课程特色").fill("这是课程的特色亮点");
  await page.getByRole("button", { name: "保存", exact: true }).click();

  await expect(page.getByText("课程概述已保存")).toBeVisible();
  await expect(page.getByText("这是课程的背景介绍")).toBeVisible();

  // 刷新页面后验证数据持久化
  await page.reload();
  // 等待恢复后，从 primary-navigation 进入我的课程
  await page.getByTestId("primary-navigation").getByRole("button", { name: "我的课程" }).click();
  await page.locator("button.class-card", { hasText: className }).click();
  await expect(page.getByText("这是课程的背景介绍")).toBeVisible();
  await expect(page.getByText("这是课程的简介内容")).toBeVisible();

  // 取消编辑后数据回退
  await page.getByRole("button", { name: "编辑概述" }).click();
  await page.getByLabel("课程背景").fill("未保存的修改");
  await page.getByRole("button", { name: "取消" }).click();
  await expect(page.getByText("这是课程的背景介绍")).toBeVisible();
  await expect(page.getByText("未保存的修改")).not.toBeVisible();
});
