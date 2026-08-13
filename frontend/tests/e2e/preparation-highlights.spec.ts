import { expect, test } from "@playwright/test";

async function selectParagraphRange(
  paragraph: ReturnType<import("@playwright/test").Page["locator"]>,
  startOffset: number,
  endOffset: number,
): Promise<void> {
  await paragraph.evaluate((element, rangeOffsets) => {
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    let position = 0;
    let startNode: Text | null = null;
    let endNode: Text | null = null;
    let startNodeOffset = 0;
    let endNodeOffset = 0;
    while (walker.nextNode()) {
      const node = walker.currentNode as Text;
      const nodeEnd = position + node.data.length;
      if (startNode === null && rangeOffsets.start < nodeEnd) {
        startNode = node;
        startNodeOffset = rangeOffsets.start - position;
      }
      if (rangeOffsets.end <= nodeEnd) {
        endNode = node;
        endNodeOffset = rangeOffsets.end - position;
        break;
      }
      position = nodeEnd;
    }
    if (!startNode || !endNode) throw new Error("无法创建段落文字选择范围");
    const range = document.createRange();
    range.setStart(startNode, startNodeOffset);
    range.setEnd(endNode, endNodeOffset);
    const selection = window.getSelection();
    if (!selection) throw new Error("浏览器不支持文字选择");
    selection.removeAllRanges();
    selection.addRange(range);
    element.dispatchEvent(new MouseEvent("mouseup", { bubbles: true }));
  }, { start: startOffset, end: endOffset });
}

test("教师可以连续选中多处文字并一次保存全部教学重点", async ({ page }) => {
  const suffix = Date.now().toString();
  await page.goto("/");
  await page.getByRole("button", { name: "注册账号" }).click();
  await page.getByLabel("用户名").fill(`highlight_teacher_${suffix}`);
  await page.getByLabel("显示名称").fill("重点教师");
  await page.getByLabel("密码").fill("TestPass123!");
  await page.getByRole("button", { name: /教师/ }).click();
  await page.getByRole("button", { name: "创建账号" }).click();
  await page.getByTestId("primary-navigation").getByRole("button", { name: "我的课程" }).click();

  await page.getByRole("button", { name: "创建教学班", exact: true }).click();
  await expect(page.getByLabel("班级名称")).toBeVisible();
  await page.getByLabel("班级名称").fill("划重点回归测试班");
  await page.getByRole("button", { name: "确认创建" }).click();
  await page.getByRole("button", { name: "知识库管理" }).click();

  await page.getByLabel("新建知识库名称").fill("重点测试知识库");
  await page.getByRole("button", { name: "新建知识库" }).click();
  await expect(page.getByRole("heading", { name: "重点测试知识库" })).toBeVisible();
  await page.locator("input[type=file]").setInputFiles({
    name: "highlight.md",
    mimeType: "text/markdown",
    buffer: Buffer.from("# 具身智能\n感知、规划与控制需要形成可靠闭环。", "utf8"),
  });
  await page.getByRole("button", { name: "上传 Markdown" }).click();
  await expect(page.getByText("highlight.md").first()).toBeVisible();
  await page.getByRole("button", { name: "查看分段", exact: true }).click();
  await expect(page.getByRole("heading", { name: "分段与索引" })).toBeVisible();
  await page.getByRole("button", { name: "文档", exact: true }).click();

  await page.getByRole("checkbox").check();
  await page.getByLabel("教学班").selectOption({ label: "划重点回归测试班" });
  await page.getByRole("button", { name: /导入选中文档/ }).click();
  await expect(page.getByText("已将 1 份原始文档导入教学班知识库")).toBeVisible();

  await page.getByTestId("primary-navigation").getByRole("button", { name: "我的课程" }).click();
  await page.getByRole("button", { name: "划重点回归测试班" }).click();
  await page.getByRole("button", { name: "课件备课", exact: true }).click();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: /选择文档并开始备课/ }).click();
  await expect(page.getByRole("heading", { name: "在线划重点" })).toBeVisible();

  const paragraph = page.locator(".paragraph-text").first();
  await selectParagraphRange(paragraph, 0, 2);
  await selectParagraphRange(paragraph, 4, 6);
  await expect(page.getByRole("button", { name: "保存当前选择" })).toBeEnabled();
  await expect(page.locator(".highlight-pending")).toHaveCount(2);
  await page.getByRole("button", { name: "保存当前选择" }).click();

  await expect(page.getByText("2 处重点")).toBeVisible();
  await expect(page.locator("mark.highlight")).toHaveCount(2);

  let deleteRequestBody = "";
  page.on("request", (request) => {
    if (request.method() === "DELETE" && request.url().endsWith("/preparation-session/highlights")) {
      deleteRequestBody = request.postData() ?? "";
    }
  });
  await page.locator("mark.highlight").first().click();
  const deleteButton = page.getByRole("button", { name: "删除重点" });
  await expect(deleteButton).toBeVisible();
  await deleteButton.click();
  await expect(page.locator("mark.highlight")).toHaveCount(1);
  await expect(page.getByText("1 处重点")).toBeVisible();
  expect(deleteRequestBody).toContain("highlightId");
});
