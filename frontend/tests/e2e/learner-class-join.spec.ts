import { expect, test } from "@playwright/test";

test("学习者自由加入课程完整流程", async ({ page }) => {
  const suffix = Date.now().toString();
  const teacherUsername = `teacher_${suffix}`;
  const learnerUsername = `learner_${suffix}`;
  const password = "StrongPass123!";
  const freeClassName = `机器人系统自由班_${suffix}`;
  const approvalClassName = `机器人系统申请班_${suffix}`;
  const closedClassName = `机器人系统关闭班_${suffix}`;

  // 1. 教师注册并创建三种类型的教学班
  await page.goto("/");
  await page.getByRole("button", { name: "注册账号" }).click();
  await page.getByLabel("用户名").fill(teacherUsername);
  await page.getByLabel("显示名称").fill("周老师");
  await page.getByLabel("密码").fill(password);
  await page.getByRole("button", { name: /教师/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();

  await page.getByRole("button", { name: "我的课程" }).click();
  // 验证教师登录成功
  await expect(page.getByRole("heading", { name: "我的课程" })).toBeVisible();
  await expect(page.getByTestId("role-badge")).toHaveText("教师");

  // 创建 free 类型教学班
  await page.getByRole("button", { name: /创建教学班|新建教学班/ }).click();
  await page.getByLabel("班级名称").fill(freeClassName);
  await page.getByLabel("加入状态").selectOption("free");
  await page.getByRole("button", { name: "确认创建" }).click();

  // 创建 approval 类型教学班
  await page.getByRole("button", { name: /创建教学班|新建教学班/ }).click();
  await page.getByLabel("班级名称").fill(approvalClassName);
  await page.getByLabel("加入状态").selectOption("approval");
  await page.getByRole("button", { name: "确认创建" }).click();

  // 创建 closed 类型教学班
  await page.getByRole("button", { name: /创建教学班|新建教学班/ }).click();
  await page.getByLabel("班级名称").fill(closedClassName);
  await page.getByLabel("加入状态").selectOption("closed");
  await page.getByRole("button", { name: "确认创建" }).click();

  // 验证三个班级创建成功
  await expect(
    page.locator(".class-grid").getByRole("button", { name: new RegExp(freeClassName) }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: new RegExp(approvalClassName) })).toBeVisible();
  await expect(page.getByRole("button", { name: new RegExp(closedClassName) })).toBeVisible();

  // 2. 教师退出登录
  await page.getByRole("button", { name: "退出登录" }).click();
  await expect(page.getByRole("button", { name: "登录" })).toBeVisible();

  // 3. 学习者注册
  await page.getByRole("button", { name: "注册账号" }).click();
  await page.getByLabel("用户名").fill(learnerUsername);
  await page.getByLabel("显示名称").fill("林晓");
  await page.getByLabel("密码").fill(password);
  await page.getByRole("button", { name: /学习者/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();

  // 验证学习者登录成功
  await expect(page.getByRole("heading", { name: "我的课程" })).toBeVisible();
  await expect(page.getByTestId("role-badge")).toHaveText("学习者");

  // 4. 验证学习者看到空状态
  await expect(page.getByRole("button", { name: /通过邀请码加入教学班/ })).toBeVisible();

  // 5. 学习者浏览可加入的教学班
  // 验证可发现班级列表自动加载
  await expect(page.getByRole("heading", { name: "可加入的教学班" })).toBeVisible();

  // 验证只显示 free 和 approval 类型的教学班，不显示 closed
  const freeClassCard = page.locator(".discover-card").filter({ hasText: freeClassName });
  const approvalClassCard = page.locator(".discover-card").filter({ hasText: approvalClassName });
  await expect(freeClassCard.getByRole("button", { name: "立即加入" })).toBeVisible();
  await expect(approvalClassCard.getByRole("button", { name: "申请加入" })).toBeVisible();
  await expect(page.getByText(closedClassName)).toHaveCount(0);

  // 验证状态标签显示正确
  await expect(freeClassCard.locator(".discover-body > .tag")).toHaveText("自由加入");
  await expect(approvalClassCard.locator(".discover-body > .tag")).toHaveText("申请加入");

  // 6. 学习者加入 free 类型的教学班
  await page.getByRole("button", { name: "立即加入" }).first().click();

  // 加入成功后停留在“我的课程”，由真实成员关系生成班级卡片。
  await expect(
    page.locator(".course-grid").getByRole("button", { name: new RegExp(freeClassName) }),
  ).toBeVisible();

  // 7. 点击班卡进入课程详情页
  await page.locator(".course-grid").getByRole("button", { name: freeClassName }).click();

  // 验证课程详情页显示正确内容
  await expect(page.getByRole("button", { name: "返回我的课程" })).toBeVisible();
  await expect(page.getByRole("button", { name: "当前课程" })).toBeVisible();
  await expect(page.getByRole("button", { name: "仿真实训" })).toBeVisible();
  await expect(page.getByRole("button", { name: "学习概览" })).toBeVisible();

  // 验证默认显示当前课程页面
  await expect(page.locator(".class-main").getByText("当前课程", { exact: true })).toBeVisible();

  // 仿真实训只读取替身协议：空目录明确展示未配置，不宣称存在真实 Webots 任务。
  await page.getByRole("button", { name: "仿真实训" }).click();
  await expect(page.getByRole("heading", { name: "仿真实训" })).toBeVisible();
  await expect(page.getByText("尚未配置任务包")).toBeVisible();
  await expect(page.getByText("目录来源：替身协议（非真实 Webots）")).toBeVisible();

  // 8. 尝试加入 approval 类型的教学班
  await page.getByRole("button", { name: "返回我的课程" }).click();

  // 03 仅展示申请加入状态；04 任务允许提交申请
  await expect(approvalClassCard.getByRole("button", { name: "申请加入" })).toBeEnabled();
  await expect(approvalClassCard.getByText("需要教师审批通过后才能加入")).toBeVisible();

  // 9. 刷新页面验证持久性
  await page.reload();

  // 验证登录状态保持
  await expect(page.getByTestId("role-badge")).toHaveText("学习者");

  // 验证已加入的班级依然显示
  await expect(
    page.locator(".course-grid").getByRole("button", { name: new RegExp(freeClassName) }),
  ).toBeVisible();

  // 10. 验证再次点击班卡可以正常进入
  await page.locator(".course-grid").getByRole("button", { name: freeClassName }).click();
  await expect(page.locator(".class-main").getByText("当前课程", { exact: true })).toBeVisible();
});
