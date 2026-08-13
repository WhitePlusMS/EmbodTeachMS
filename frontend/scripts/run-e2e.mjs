import { spawn, spawnSync } from "node:child_process";
import { existsSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(scriptDirectory, "..");
const backendRoot = resolve(frontendRoot, "..", "backend");
const backendPython = resolve(
  backendRoot,
  ".venv",
  process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
);
const playwrightCli = resolve(
  frontendRoot,
  "node_modules",
  "@playwright",
  "test",
  "cli.js",
);
const viteCli = resolve(frontendRoot, "node_modules", "vite", "bin", "vite.js");
const databasePath = resolve(
  tmpdir(),
  `course-agent-e2e-${process.pid}.db`,
);

if (!existsSync(backendPython)) {
  throw new Error("未找到 uv 管理的后端虚拟环境，请先在 backend 运行 uv sync");
}

const children = [];

function start(command, args, options) {
  const child = spawn(command, args, {
    ...options,
    stdio: ["ignore", "inherit", "inherit"],
  });
  children.push(child);
  return child;
}

async function waitForUrl(url, child, label) {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) {
      throw new Error(`${label}提前退出，退出码 ${child.exitCode}`);
    }
    try {
      const response = await fetch(url);
      if (response.ok) {
        return;
      }
    } catch {
      // 服务仍在启动，短暂等待后继续探测。
    }
    await new Promise((resolveDelay) => setTimeout(resolveDelay, 200));
  }
  throw new Error(`${label}在 30 秒内未就绪`);
}

async function stopChildren() {
  for (const child of children.reverse()) {
    if (child.exitCode === null) {
      child.kill();
    }
  }
  await Promise.all(
    children.map(
      (child) =>
        new Promise((resolveExit) => {
          if (child.exitCode !== null) {
            resolveExit();
            return;
          }
          child.once("exit", resolveExit);
          setTimeout(() => {
            if (child.exitCode === null) {
              child.kill("SIGKILL");
            }
            resolveExit();
          }, 2_000);
        }),
    ),
  );
}

let testStatus = 1;
try {
  const backend = start(
    backendPython,
    [
      "-m",
      "uvicorn",
      "app.run:app",
      "--host",
      "127.0.0.1",
      "--port",
      "18081",
    ],
    {
      cwd: backendRoot,
      env: {
        ...process.env,
        COURSE_AGENT_JWT_SECRET:
          "e2e-secret-with-at-least-thirty-two-characters",
        COURSE_AGENT_DATABASE_PATH: databasePath,
        COURSE_AGENT_ALLOWED_ORIGINS: "http://127.0.0.1:14173",
      },
    },
  );
  const frontend = start(
    process.execPath,
    [viteCli, "preview", "--host", "127.0.0.1", "--port", "14173"],
    { cwd: frontendRoot, env: process.env },
  );

  await Promise.all([
    waitForUrl("http://127.0.0.1:18081/docs", backend, "后端测试服务"),
    waitForUrl("http://127.0.0.1:14173", frontend, "前端测试服务"),
  ]);

  const result = spawnSync(process.execPath, [playwrightCli, "test"], {
    cwd: frontendRoot,
    env: process.env,
    stdio: "inherit",
  });
  testStatus = result.status ?? 1;
} finally {
  await stopChildren();
  for (const suffix of ["", "-shm", "-wal"]) {
    rmSync(`${databasePath}${suffix}`, { force: true });
  }
}

process.exitCode = testStatus;
