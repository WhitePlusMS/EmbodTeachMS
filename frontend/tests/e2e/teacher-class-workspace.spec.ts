import { expect, test } from "@playwright/test";

test("教师教学班工作台完整流程", async ({ page }) => {
  const suffix = Date.now().toString();
  const teacherUsername = `teacher_${suffix}`;
  const password = "StrongPass123!";

  // 1. 注册教师
  await page.goto("/");
  await page.getByRole("button", { name: "注册账号" }).click();
  await page.getByLabel("用户名").fill(teacherUsername);
  await page.getByLabel("显示名称").fill("周老师");
  await page.getByLabel("密码").fill(password);
  await page.getByRole("button", { name: /教师/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();

  // 验证登录成功：教师顶层入口统一为“我的课程”，知识库管理在课程页内进入。
  await expect(page.getByRole("heading", { name: "我的课程" })).toBeVisible();
  await expect(page.getByTestId("role-badge")).toHaveText("教师");

  // 2. 课程页内验证教学班空状态。
  await page.getByRole("button", { name: "我的课程" }).click();
  await expect(page.getByText("暂无教学班")).toBeVisible();
  await expect(page.getByText("后续可在这里创建第一个教学班。")).toBeVisible();

  // 3. 创建教学班
  await page.getByRole("button", { name: /创建教学班|新建教学班/ }).click();
  await page.getByLabel("班级名称").fill("机器人系统 1 班");
  await page.getByLabel("加入状态").selectOption("free");
  await page.getByRole("button", { name: "确认创建" }).click();

  // 4. 验证班级卡片显示
  await expect(page.getByRole("button", { name: /机器人系统 1 班/ })).toBeVisible();
  await expect(page.getByText("自由加入")).toBeVisible();
  await expect(page.getByText("0 名学习者")).toBeVisible();

  // 5. 点击班卡进入详情页
  await page.getByRole("button", { name: "机器人系统 1 班" }).click();

  // 验证默认显示课程概述
  await expect(page.getByRole("heading", { name: "课程概述" })).toBeVisible();

  // 6. 精确验证教学班导航的10个按钮（知识库属于“我的课程”分组，不是顶层并列入口）
  const navButtons = await page.locator('[aria-label="教学班导航"] button');
  await expect(navButtons).toHaveCount(10);

  await expect(page.getByRole("button", { name: "返回我的课程" })).toBeVisible();
  await expect(page.getByRole("button", { name: "知识库管理" })).toBeVisible();
  await expect(page.getByRole("button", { name: "课程概述" })).toBeVisible();
  await expect(page.getByRole("button", { name: "申请管理" })).toBeVisible();
  await expect(page.getByRole("button", { name: "授权码管理" })).toBeVisible();
  await expect(page.getByRole("button", { name: "课件备课" })).toBeVisible();
  await expect(page.getByRole("button", { name: "班级概览" })).toBeVisible();
  await expect(page.getByRole("button", { name: "学习者详情" })).toBeVisible();
  await expect(page.getByRole("button", { name: "课堂练习管理" })).toBeVisible();
  await expect(page.getByRole("button", { name: "作业管理" })).toBeVisible();

  await page.getByRole("button", { name: "知识库管理" }).click();
  await expect(page.getByRole("heading", { name: "知识库", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "返回我的课程" }).click();
  await page.getByRole("button", { name: "机器人系统 1 班" }).click();

  // 7. 空班概览仍展示各模块真实空态，并可进入全部学习者页面。
  await page.getByRole("button", { name: "班级概览" }).click();
  await expect(page.getByText("班级暂无学习者")).toBeVisible();
  await expect(page.getByRole("heading", { name: "班级知识点分布" })).toBeVisible();
  await expect(page.getByText("未学习")).toBeVisible();
  await expect(page.getByText("来源：替身协议结构化事实（非真实 Webots 评价）")).toBeVisible();
  await page.getByRole("button", { name: "全部学习者 →" }).click();
  await expect(page.getByRole("heading", { name: "学习者列表" })).toBeVisible();

  // 课堂练习管理只展示当前班已发布练习；空班应引导教师进入课件备课。
  await page.getByRole("button", { name: "课堂练习管理" }).click();
  await expect(page.getByRole("heading", { name: "课堂练习管理" })).toBeVisible();
  await expect(page.getByText("暂无课堂练习")).toBeVisible();
  await expect(page.getByText("请先在课件备课页面发布课堂练习")).toBeVisible();

  // 作业统计页在没有发布作业时显示真实空态。
  await page.getByRole("button", { name: "作业管理" }).click();
  await expect(page.getByRole("heading", { name: "作业管理" })).toBeVisible();
  await expect(page.getByText("暂无已发布作业")).toBeVisible();
  await expect(page.getByText("请先在课件备课页面发布作业")).toBeVisible();

  // 8. 点击课件备课按钮
  await page.getByRole("button", { name: "课件备课" }).click();
  await expect(page.getByRole("heading", { name: "课件备课" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "备课步骤" })).toContainText(/1\s*从知识库选文档/);
  await expect(page.getByRole("navigation", { name: "备课步骤" })).toContainText(/2\s*在线划重点/);
  await expect(page.getByRole("navigation", { name: "备课步骤" })).toContainText(/3\s*手工建题/);
  await expect(page.getByRole("navigation", { name: "备课步骤" })).toContainText(/4\s*发布/);
  await expect(page.locator("main").getByRole("button", { name: "基于重点生成候选题" })).toHaveCount(0);

  // 9. 返回我的课程再点班卡
  await page.getByRole("button", { name: "返回我的课程" }).click();
  await expect(page.getByRole("heading", { name: "我的课程" })).toBeVisible();
  await page.getByRole("button", { name: "机器人系统 1 班" }).click();

  // 10. 教师可在同一班级切换三种加入状态并看到成功反馈。
  await page.getByLabel("加入状态").selectOption("approval");
  await page.getByRole("button", { name: "保存设置" }).click();
  await expect(page.locator(".status-badge").getByText("申请加入")).toBeVisible();
  await page.getByLabel("加入状态").selectOption("closed");
  await page.getByRole("button", { name: "保存设置" }).click();

  // 验证设置保存成功
  await expect(page.locator(".status-badge").getByText("关闭加入")).toBeVisible();

  // 11. 创建并显示班级授权码，确保工作台事件穿过中继 module。
  await page.getByRole("button", { name: "授权码管理" }).click();
  await expect(page.getByRole("heading", { name: "班级授权码" })).toBeVisible();
  await expect(page.getByText("尚未创建班级授权码。")).toBeVisible();
  await page.getByRole("button", { name: "保存授权码" }).click();
  await expect(page.getByText("当前授权码", { exact: true })).toBeVisible();

  // 12. 刷新页面验证持久性
  await page.reload();

  await page.getByRole("button", { name: "我的课程" }).click();
  await page.getByRole("button", { name: "机器人系统 1 班" }).click();
  await expect(page.getByRole("heading", { name: "课程概述" })).toBeVisible();
  await expect(page.locator(".status-badge").getByText("关闭加入")).toBeVisible();
});
