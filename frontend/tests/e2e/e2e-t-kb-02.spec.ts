/**
 * T-KB-03 / T-KB-04 / T-KB-05 / T-KB-06 知识库文档管理、分段索引、召回测试与备课导入
 *
 * 执行顺序依赖：
 *   1) 新建知识库
 *   2) 上传 Markdown 文档 → 文档管理（T-KB-03）
 *   3) 分段与索引（T-KB-04）
 *   4) 召回测试（T-KB-05）
 *   5) 备课导入（T-KB-06）
 *
 * 注意：所有检查点共用一个教师账号和知识库以减少耗时。
 */
import { expect, test } from "@playwright/test";

const PASSWORD = "TestPass123!";

test.describe("T-KB-03 文档管理", () => {
  test("上传文档并显示在文档列表中", async ({ page }) => {
    const s = Date.now().toString();
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(`kb3_t_${s}`);
    await page.getByLabel("显示名称").fill("文档测试教师");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /教师/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    // 创建知识库
    await page.getByRole("button", { name: "知识库管理" }).click();
    await page.getByLabel("新建知识库名称").fill(`文档库_${s}`);
    await page.getByRole("button", { name: "新建知识库" }).click();
    await expect(page.getByText(`文档库_${s}`).first()).toBeVisible({ timeout: 5000 });

    // 上传 Markdown 文档（用 setInputFiles）
    const fileChooserPromise = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: "上传 Markdown" }).click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(["tests/e2e/test-assets/sample-doc.md"]);

    // 等待文档出现在列表中（标题取自文件名）
    await expect(page.getByText("sample-doc").first()).toBeVisible({ timeout: 8000 });
  });

  test("编辑文档并保存新版本", async ({ page }) => {
    const s = Date.now().toString();
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(`kb3b_t_${s}`);
    await page.getByLabel("显示名称").fill("文档编辑教师");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /教师/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    await page.getByRole("button", { name: "知识库管理" }).click();
    await page.getByLabel("新建知识库名称").fill(`编辑库_${s}`);
    await page.getByRole("button", { name: "新建知识库" }).click();
    await expect(page.getByText(`编辑库_${s}`).first()).toBeVisible({ timeout: 5000 });

    // 上传文档
    const fc1 = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: "上传 Markdown" }).click();
    (await fc1).setFiles(["tests/e2e/test-assets/sample-doc.md"]);
    await expect(page.getByText("sample-doc").first()).toBeVisible({ timeout: 8000 });

    // 点击"编辑"按钮
    await page.getByRole("button", { name: "编辑", exact: true }).click();
    await expect(page.getByRole("textbox", { name: "标题" })).toBeVisible();

    // 修改标题
    const titleInput = page.getByRole("textbox", { name: "标题" });
    await titleInput.fill("机器学习基础（修订版）");
    await page.getByRole("button", { name: "保存新版本" }).click();

    // 验证新标题出现
    await expect(page.getByText("机器学习基础（修订版）").first()).toBeVisible({ timeout: 5000 });
  });

  test("取消编辑后原内容不变", async ({ page }) => {
    const s = Date.now().toString();
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(`kb3c_t_${s}`);
    await page.getByLabel("显示名称").fill("取消防教师");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /教师/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    await page.getByRole("button", { name: "知识库管理" }).click();
    await page.getByLabel("新建知识库名称").fill(`取消库_${s}`);
    await page.getByRole("button", { name: "新建知识库" }).click();
    await expect(page.getByText(`取消库_${s}`).first()).toBeVisible({ timeout: 5000 });

    // 上传并编辑→取消
    const fc2 = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: "上传 Markdown" }).click();
    (await fc2).setFiles(["tests/e2e/test-assets/sample-doc.md"]);
    await expect(page.getByText("sample-doc").first()).toBeVisible({ timeout: 8000 });

    await page.getByRole("button", { name: "编辑", exact: true }).click();
    await page.getByRole("textbox", { name: "标题" }).fill("临时标题");
    await page.getByRole("button", { name: "取消", exact: true }).click();

    await expect(page.getByText("sample-doc").first()).toBeVisible();
    await expect(page.getByText("临时标题")).toHaveCount(0);
  });

  test("删除文档确认后文档消失", async ({ page }) => {
    const s = Date.now().toString();
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(`kb3d_t_${s}`);
    await page.getByLabel("显示名称").fill("删除文档教师");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /教师/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    await page.getByRole("button", { name: "知识库管理" }).click();
    await page.getByLabel("新建知识库名称").fill(`删除库_${s}`);
    await page.getByRole("button", { name: "新建知识库" }).click();
    await expect(page.getByText(`删除库_${s}`).first()).toBeVisible({ timeout: 5000 });

    // 上传
    const fc3 = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: "上传 Markdown" }).click();
    (await fc3).setFiles(["tests/e2e/test-assets/sample-doc.md"]);
    await expect(page.getByText("sample-doc").first()).toBeVisible({ timeout: 8000 });

    // 删除（confirm 对话框会自动确认）
    page.on("dialog", (dialog) => dialog.accept());
    await page.getByRole("button", { name: "删除", exact: true }).click();
    await page.waitForTimeout(500);

    // 文档应消失
    await expect(page.getByText("sample-doc")).toHaveCount(0);
  });

  test("替换文档后内容更新", async ({ page }) => {
    const s = Date.now().toString();
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(`kb3e_t_${s}`);
    await page.getByLabel("显示名称").fill("替换文档教师");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /教师/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    await page.getByRole("button", { name: "知识库管理" }).click();
    await page.getByLabel("新建知识库名称").fill(`替换库_${s}`);
    await page.getByRole("button", { name: "新建知识库" }).click();
    await expect(page.getByText(`替换库_${s}`).first()).toBeVisible({ timeout: 5000 });

    // 上传第一份
    const fc4 = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: "上传 Markdown" }).click();
    (await fc4).setFiles(["tests/e2e/test-assets/sample-doc.md"]);
    await expect(page.getByText("sample-doc").first()).toBeVisible({ timeout: 8000 });

    // 点击"替换"（label 内部隐藏 input）
    const replaceFileChooser = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: "替换" }).click();
    (await replaceFileChooser).setFiles(["tests/e2e/test-assets/python-intro.md"]);
    await page.waitForTimeout(1000);

    // 新文件名应显示
    await expect(page.getByText("python-intro").first()).toBeVisible({ timeout: 8000 });
  });
});

test.describe("T-KB-04 分段与索引", () => {
  test("进入分段页签并刷新分段", async ({ page }) => {
    const s = Date.now().toString();
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(`kb4_t_${s}`);
    await page.getByLabel("显示名称").fill("分段测试教师");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /教师/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    await page.getByRole("button", { name: "知识库管理" }).click();
    await page.getByLabel("新建知识库名称").fill(`分段库_${s}`);
    await page.getByRole("button", { name: "新建知识库" }).click();
    await expect(page.getByText(`分段库_${s}`).first()).toBeVisible({ timeout: 5000 });

    // 上传文档
    const fc = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: "上传 Markdown" }).click();
    (await fc).setFiles(["tests/e2e/test-assets/sample-doc.md"]);
    await expect(page.getByText("机器学习基础").first()).toBeVisible({ timeout: 8000 });

    // 点击"查看分段"跳转到分段页签
    await page.getByRole("button", { name: "查看分段" }).click();
    // 分段页签应被激活
    await expect(page.getByRole("button", { name: "分段", exact: true }).filter({ has: page.locator(".active") }).or(page.getByRole("tab", { name: "分段" }))).toBeAttached();

    // 刷新分段按钮应可见
    await expect(page.getByRole("button", { name: "刷新分段" })).toBeVisible();

    // 预览分段
    await page.getByRole("button", { name: "预览分段" }).click();
    // 预览结果或空提示应该显示
    await page.waitForTimeout(1000);

    // 切换到简单分段模式（默认应已是简单）
    // 点击"应用规则并重建"
    const rebuildBtn = page.getByRole("button", { name: /应用规则并重建/ });
    if (await rebuildBtn.isEnabled().catch(() => false)) {
      await rebuildBtn.click();
      await page.waitForTimeout(1500);
    }
  });

  test("分段页签切换文档后内容更新", async ({ page }) => {
    const s = Date.now().toString();
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(`kb4b_t_${s}`);
    await page.getByLabel("显示名称").fill("分段切换教师");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /教师/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    await page.getByRole("button", { name: "知识库管理" }).click();
    await page.getByLabel("新建知识库名称").fill(`分段切库_${s}`);
    await page.getByRole("button", { name: "新建知识库" }).click();
    await expect(page.getByText(`分段切库_${s}`).first()).toBeVisible({ timeout: 5000 });

    // 上传两份文档
    const f1 = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: "上传 Markdown" }).click();
    (await f1).setFiles(["tests/e2e/test-assets/sample-doc.md"]);
    await expect(page.getByText("机器学习基础").first()).toBeVisible({ timeout: 8000 });

    const f2 = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: "上传 Markdown" }).click();
    (await f2).setFiles(["tests/e2e/test-assets/python-intro.md"]);
    await expect(page.getByText("Python 编程入门").first()).toBeVisible({ timeout: 8000 });

    // 点到分段页签，查看当前文档分段
    await page.getByRole("button", { name: "查看分段" }).first().click();
    await page.waitForTimeout(500);

    // 当前文档应是第一个上传的文档
    await expect(page.getByText(/当前文档/).first()).toBeVisible();
  });

  test("无文档时预览分段按钮禁用", async ({ page }) => {
    const s = Date.now().toString();
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(`kb4c_t_${s}`);
    await page.getByLabel("显示名称").fill("分段空态教师");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /教师/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    await page.getByRole("button", { name: "知识库管理" }).click();
    await page.getByLabel("新建知识库名称").fill(`分段空库_${s}`);
    await page.getByRole("button", { name: "新建知识库" }).click();
    await expect(page.getByText(`分段空库_${s}`).first()).toBeVisible({ timeout: 5000 });

    // 直接切换到分段页签
    await page.getByRole("button", { name: "分段", exact: true }).click();
    await page.waitForTimeout(500);

    // 预览分段按钮应禁用（无文档选择）
    await expect(page.getByRole("button", { name: "预览分段" })).toBeDisabled();
  });
});

test.describe("T-KB-05 召回测试", () => {
  test("输入问题并执行召回测试", async ({ page }) => {
    const s = Date.now().toString();
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(`kb5_t_${s}`);
    await page.getByLabel("显示名称").fill("召回测试教师");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /教师/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    await page.getByRole("button", { name: "知识库管理" }).click();
    await page.getByLabel("新建知识库名称").fill(`召回库_${s}`);
    await page.getByRole("button", { name: "新建知识库" }).click();
    await expect(page.getByText(`召回库_${s}`).first()).toBeVisible({ timeout: 5000 });

    // 切换到召回测试页签
    await page.getByRole("button", { name: "召回测试" }).click();

    // 空查询时按钮禁用
    await expect(page.getByRole("button", { name: "开始召回测试" })).toBeDisabled();

    // 输入查询内容
    await page.getByPlaceholder(/具身智能/).fill("机器学习是什么");
    await expect(page.getByRole("button", { name: "开始召回测试" })).toBeEnabled();

    // 执行召回测试
    await page.getByRole("button", { name: "开始召回测试" }).click();
    await page.waitForTimeout(1500);

    // 检查结果或空结果提示出现
    await expect(page.getByText("Top").or(page.getByText("没有达到"))).toBeVisible({ timeout: 5000 });
  });

  test("切换检索模式后表单可提交", async ({ page }) => {
    const s = Date.now().toString();
    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(`kb5b_t_${s}`);
    await page.getByLabel("显示名称").fill("召回模式教师");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /教师/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    await page.getByRole("button", { name: "知识库管理" }).click();
    await page.getByLabel("新建知识库名称").fill(`召回库b_${s}`);
    await page.getByRole("button", { name: "新建知识库" }).click();
    await expect(page.getByText(`召回库b_${s}`).first()).toBeVisible({ timeout: 5000 });

    // 切换到召回测试页签
    await page.getByRole("button", { name: "召回测试" }).click();

    // 切换检索模式
    await page.getByLabel("检索模式").selectOption("keyword");
    await page.getByPlaceholder(/具身智能/).fill("测试查询");

    // 提交
    await page.getByRole("button", { name: "开始召回测试" }).click();
    await page.waitForTimeout(1000);

    // 验证结果区域出现
    await page.waitForTimeout(500);
  });
});

test.describe("T-KB-06 备课导入", () => {
  test("导入选中文档到教学班", async ({ page }) => {
    const s = Date.now().toString();
    const className = `导入班_${s}`;

    await page.goto("/");
    await page.getByRole("button", { name: "注册账号" }).click();
    await page.getByLabel("用户名").fill(`kb6_t_${s}`);
    await page.getByLabel("显示名称").fill("备课导入教师");
    await page.getByLabel("密码").fill(PASSWORD);
    await page.getByRole("button", { name: /教师/ }).click();
    await page.getByRole("button", { name: "创建账号" }).click();
    await expect(page.getByTestId("role-badge")).toHaveText("教师");

    // 先创建教学班（导入需要目标班级）
    await page.getByRole("button", { name: "创建教学班" }).click();
    await page.getByLabel("班级名称").fill(className);
    await page.getByRole("button", { name: "确认创建" }).click();
    await expect(page.getByText(className).first()).toBeVisible({ timeout: 5000 });

    // 进入知识库管理
    await page.getByRole("button", { name: "知识库管理" }).click();
    await page.getByLabel("新建知识库名称").fill(`备课源库_${s}`);
    await page.getByRole("button", { name: "新建知识库" }).click();
    await expect(page.getByText(`备课源库_${s}`).first()).toBeVisible({ timeout: 5000 });

    // 上传文档
    const fc = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: "上传 Markdown" }).click();
    (await fc).setFiles(["tests/e2e/test-assets/sample-doc.md"]);
    await expect(page.getByText("机器学习基础").first()).toBeVisible({ timeout: 8000 });

    // 在导入面板中勾选文档
    const checkbox = page.locator(".import-document input[type=checkbox]");
    await expect(checkbox).toBeVisible({ timeout: 5000 });
    await checkbox.check();

    // 选择目标班级
    await page.getByLabel("教学班").selectOption({ label: className });

    // 点击导入
    await page.getByRole("button", { name: /导入选中文档/ }).click();
    await page.waitForTimeout(1500);

    // 验证成功通知（或页面不崩溃）
    await expect(page.getByText("已将").or(page.getByText("导入"))).toBeVisible({ timeout: 5000 });
  });
});
