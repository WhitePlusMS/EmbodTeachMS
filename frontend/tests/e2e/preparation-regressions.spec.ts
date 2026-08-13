import { expect, test, type Page } from "@playwright/test";

type PreparedMaterials = {
  className: string;
};

async function createPreparedMaterials(page: Page, suffix: string): Promise<PreparedMaterials> {
  const className = `备课回归班-${suffix}`;
  await page.goto("/");
  await page.getByRole("button", { name: "注册账号" }).click();
  await page.getByLabel("用户名").fill(`preparation_regression_${suffix}`);
  await page.getByLabel("显示名称").fill("备课回归教师");
  await page.getByLabel("密码").fill("TestPass123!");
  await page.getByRole("button", { name: /教师/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();
  await page.getByTestId("primary-navigation").getByRole("button", { name: "我的课程" }).click();

  await page.getByRole("button", { name: "创建教学班", exact: true }).click();
  await page.getByLabel("班级名称").fill(className);
  await page.getByRole("button", { name: "确认创建" }).click();
  await page.getByRole("button", { name: "知识库管理" }).click();

  await page.getByLabel("新建知识库名称").fill(`备课回归知识库-${suffix}`);
  await page.getByRole("button", { name: "新建知识库" }).click();
  await page.locator("input[type=file]").setInputFiles({
    name: "preparation-regression.md",
    mimeType: "text/markdown",
    buffer: Buffer.from(
      "# 具身智能\n\n感知、规划与控制需要形成可靠闭环，机器人通过环境交互获得反馈。",
      "utf8",
    ),
  });
  await page.getByRole("button", { name: "上传 Markdown" }).click();
  await expect(page.getByText("preparation-regression.md")).toBeVisible();
  await page.getByRole("button", { name: "查看分段", exact: true }).click();
  await expect(page.getByRole("heading", { name: "分段与索引" })).toBeVisible();
  await page.getByRole("button", { name: "文档", exact: true }).click();

  await page.getByRole("checkbox").first().check();
  await page.getByLabel("教学班").selectOption({ label: className });
  await page.getByRole("button", { name: /导入选中文档/ }).click();
  await expect(page.getByText("已将 1 份原始文档导入教学班知识库")).toBeVisible();

  await page.getByTestId("primary-navigation").getByRole("button", { name: "我的课程" }).click();
  await page.getByRole("button", { name: new RegExp(className) }).click();
  await page.getByRole("button", { name: "课件备课", exact: true }).click();
  const preparationCheckbox = page.getByRole("checkbox").first();
  await preparationCheckbox.check();
  await expect(preparationCheckbox).toHaveCSS("width", "18px");
  await expect(preparationCheckbox).toHaveCSS("height", "18px");
  await page.getByRole("button", { name: /选择文档并开始备课/ }).click();
  await expect(page.getByRole("heading", { name: "在线划重点" })).toBeVisible();

  return { className };
}

async function saveFirstHighlight(page: Page): Promise<void> {
  const paragraph = page.locator(".paragraph-text").first();
  await paragraph.selectText();
  await paragraph.dispatchEvent("mouseup");
  await page.getByRole("button", { name: "保存当前选择" }).click();
  await expect(page.locator("mark.highlight")).toHaveCount(1);
}

test("从知识库返回班级后课程导航和备课状态仍可继续使用", async ({ page }) => {
  const { className } = await createPreparedMaterials(page, Date.now().toString());
  await saveFirstHighlight(page);

  await page.getByRole("button", { name: "知识库管理", exact: true }).click();
  await expect(page.getByRole("button", { name: "课程概述", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "课件备课", exact: true }).click();
  await expect(page.getByRole("heading", { name: "在线划重点" })).toBeVisible();
  await expect(page.locator("mark.highlight")).toHaveCount(1);
  await expect(page.getByRole("button", { name: className, exact: true })).toHaveCount(0);
});

test("选中文字后立即显示待保存的重点预览", async ({ page }) => {
  await createPreparedMaterials(page, Date.now().toString());
  const paragraph = page.locator(".paragraph-text").first();
  await paragraph.selectText();
  await paragraph.dispatchEvent("mouseup");

  await expect(page.locator(".highlight-pending")).toHaveCount(1);
  await expect(page.getByRole("button", { name: "保存当前选择" })).toBeEnabled();
});

test("手工题缺少正确答案时前端阻止 422 请求", async ({ page }) => {
  await createPreparedMaterials(page, Date.now().toString());
  const questionRequests: string[] = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && request.url().endsWith("/preparation-session/questions")) {
      questionRequests.push(request.postData() ?? "");
    }
  });

  await page.getByLabel("题干").fill("为什么需要感知反馈？");
  await page.getByLabel("选项（每行一个）").fill("A\nB");
  await page.getByLabel("知识点（逗号分隔）").fill("感知");
  await page.getByRole("button", { name: "创建手工题" }).click();

  await expect(page.getByRole("alert").filter({ hasText: "至少选择一个正确答案" })).toBeVisible();
  expect(questionRequests).toHaveLength(0);
});

test("文档管理直接进入分段，工作台不再显示重复的分段设置标签", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "注册账号" }).click();
  const suffix = Date.now().toString();
  await page.getByLabel("用户名").fill(`knowledge_base_regression_${suffix}`);
  await page.getByLabel("显示名称").fill("知识库回归教师");
  await page.getByLabel("密码").fill("TestPass123!");
  await page.getByRole("button", { name: /教师/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();
  await page.getByTestId("primary-navigation").getByRole("button", { name: "我的课程" }).click();
  await page.getByRole("button", { name: "知识库管理" }).click();
  await page.getByLabel("新建知识库名称").fill(`文档回归知识库-${suffix}`);
  await page.getByRole("button", { name: "新建知识库" }).click();
  await page.locator("input[type=file]").setInputFiles({
    name: "document-first.md",
    mimeType: "text/markdown",
    buffer: Buffer.from("# 文档优先\n\n先选中文档；再调整它的分段规则。\n\n# 第二章\n\n第二段内容。", "utf8"),
  });
  await page.getByRole("button", { name: "上传 Markdown" }).click();
  await expect(page.getByText("document-first.md")).toBeVisible();
  const importCheckbox = page.getByRole("checkbox").first();
  await expect(importCheckbox).toHaveCSS("width", "18px");
  await expect(importCheckbox).toHaveCSS("height", "18px");

  await expect(page.getByRole("button", { name: "分段设置", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "查看分段", exact: true }).click();
  await expect(page.getByRole("heading", { name: "分段与索引" })).toBeVisible();
  await expect(page.getByText("当前文档：document-first.md")).toBeVisible();
  await page.getByLabel("分段方式").selectOption("advanced");
  await page.getByLabel("选择分隔符").selectOption("#");
  await page.getByRole("button", { name: "预览分段" }).click();
  await expect(page.getByText("预览：2 个分段")).toBeVisible();
});
