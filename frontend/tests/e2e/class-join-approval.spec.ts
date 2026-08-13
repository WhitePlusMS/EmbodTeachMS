import { expect, test } from "@playwright/test";

test("班级申请审批完整流程", async ({ page }) => {
  const suffix = Date.now().toString();
  const teacherUsername = `teacher_${suffix}`;
  const learnerUsername = `learner_${suffix}`;
  const className = `机器人系统申请班_${suffix}`;
  const password = "StrongPass123!";

  // 1. 教师注册并创建申请加入状态的教学班
  await page.goto("/");
  await page.getByRole("button", { name: "注册账号" }).click();
  await page.getByLabel("用户名").fill(teacherUsername);
  await page.getByLabel("显示名称").fill("周老师");
  await page.getByLabel("密码").fill(password);
  await page.getByRole("button", { name: /教师/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();

  // 教师默认先进入知识库，班级操作从“我的课程”进入。
  await page.getByRole("button", { name: "我的课程" }).click();
  await expect(page.getByRole("heading", { name: "我的课程" })).toBeVisible();
  await expect(page.getByTestId("role-badge")).toHaveText("教师");

  // 创建 approval 类型教学班
  await page.getByRole("button", { name: /创建教学班|新建教学班/ }).click();
  await page.getByLabel("班级名称").fill(className);
  await page.getByLabel("加入状态").selectOption("approval");
  await page.getByRole("button", { name: "确认创建" }).click();

  // 验证班级创建成功
  await expect(page.getByRole("button", { name: className })).toBeVisible();

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

  // 4. 学习者提交申请加入
  const ownDiscoverCard = page.locator(".discover-card").filter({ hasText: className });
  await expect(ownDiscoverCard.getByRole("button", { name: "申请加入" })).toBeVisible();
  await ownDiscoverCard.getByRole("button", { name: "申请加入" }).click();

  // 验证申请提交成功提示
  await expect(page.getByText("申请提交成功，等待教师审批")).toBeVisible();

  // 5. 验证申请状态变为"申请中"，按钮禁用
  await expect(page.getByRole("button", { name: "申请中" })).toBeVisible();
  await expect(page.getByRole("button", { name: "申请中" })).toBeDisabled();
  await expect(page.getByText("申请已提交，等待教师审批")).toBeVisible();

  // 6. 验证申请中的学习者不能访问课程
  // 尝试点击班级卡片应该没有反应（因为不是成员）
  await ownDiscoverCard.click();
  // 应该仍然停留在发现页面，没有进入班级详情
  await expect(page.getByRole("heading", { name: "我的课程" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "可加入的教学班" })).toBeVisible();

  // 7. 学习者退出登录
  await page.getByRole("button", { name: "退出登录" }).click();
  await expect(page.getByRole("button", { name: "登录" })).toBeVisible();

  // 8. 教师登录处理申请
  await page.getByLabel("用户名").fill(teacherUsername);
  await page.getByLabel("密码").fill(password);
  await page.getByRole("button", { name: "登录" }).click();

  // 验证教师登录成功
  await page.getByRole("button", { name: "我的课程" }).click();
  await expect(page.getByRole("heading", { name: "我的课程" })).toBeVisible();

  // 9. 教师进入班级查看申请
  await page.getByRole("button", { name: className }).click();
  await page.getByRole("button", { name: "申请管理" }).click();

  // 验证申请管理页面显示
  await expect(page.getByRole("heading", { name: "申请管理" })).toBeVisible();

  // 10. 教师批准申请
  await page.getByRole("button", { name: "批准" }).first().click();

  // 验证批准成功提示
  await expect(page.getByText("申请已批准")).toBeVisible();

  // 11. 教师从正式成员列表下钻详情并返回，班级上下文保持不变。
  await page.getByRole("button", { name: "学习者详情" }).click();
  await expect(page.getByRole("heading", { name: "学习者列表" })).toBeVisible();
  const learnerRow = page.locator("tbody tr").filter({ hasText: "林晓" });
  const cellContentCenterOffsets = await learnerRow.locator("td").evaluateAll((cells) =>
    cells.map((cell) => {
      const cellRect = cell.getBoundingClientRect();
      const contentRange = document.createRange();
      contentRange.selectNodeContents(cell);
      const contentRect = contentRange.getBoundingClientRect();
      return Math.abs(
        cellRect.left + cellRect.width / 2 - (contentRect.left + contentRect.width / 2),
      );
    }),
  );
  expect(cellContentCenterOffsets.every((offset) => offset <= 1)).toBe(true);

  await learnerRow.getByRole("button", { name: "查看依据" }).click();
  await expect(page.getByRole("heading", { name: "学习者详情" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "林晓" })).toBeVisible();
  await page.getByRole("button", { name: "← 返回学习者列表" }).click();
  await expect(page.getByRole("heading", { name: "学习者列表" })).toBeVisible();
  await expect(page.locator("tbody tr").filter({ hasText: "林晓" }).getByRole("button", { name: "查看依据" })).toBeVisible();

  // 12. 教师退出登录
  await page.getByRole("button", { name: "退出登录" }).click();
  await expect(page.getByRole("button", { name: "登录" })).toBeVisible();

  // 13. 学习者重新登录验证状态
  await page.getByLabel("用户名").fill(learnerUsername);
  await page.getByLabel("密码").fill(password);
  await page.getByRole("button", { name: "登录" }).click();

  // 验证学习者登录成功
  await expect(page.getByRole("heading", { name: "我的课程" })).toBeVisible();

  // 14. 验证学习者现在可以看到已加入的班级
  await expect(page.locator(".course-grid").getByRole("button", { name: new RegExp(className) })).toBeVisible();

  // 15. 验证学习者可以访问课程详情
  await page.locator(".course-grid").getByRole("button", { name: className }).click();
  await expect(page.getByRole("button", { name: "返回我的课程" })).toBeVisible();
  await expect(page.getByRole("button", { name: "当前课程" })).toBeVisible();

  // 16. 验证申请班在可发现列表中消失
  await page.getByRole("button", { name: "返回我的课程" }).click();
  await expect(page.locator(".discover-card").getByRole("heading", { name: className })).toHaveCount(0);
});
