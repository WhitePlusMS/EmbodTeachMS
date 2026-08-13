# EmbodTeachMS 具身课堂

EmbodTeachMS 具身课堂面向教师与学习者，围绕“课程资料 → 教师备课与发布 → 学生学习、练习和作业 → 教师查看学习证据与分析”形成教学闭环。项目采用 Vue 3 + TypeScript 前端、FastAPI 后端和 SQLite 本地持久化，并提供可交互的 Three.js 具身智能三维教学演示。

## 第 1 部分：项目成果

### 1.1 可运行的产品 Demo

#### Demo 解决的问题

传统课程资料、课堂练习、作业和学情数据容易分散在不同环节，教师难以持续追踪“发布了什么、学生学了什么、练习结果如何”。本 Demo 将课程资料管理、教师备课发布、学生学习实践和教师分析集中在同一工作台，使教学内容与学习证据形成可追溯闭环。

#### Demo 用户与核心功能

| 用户 | 核心功能 | 可产生的结果 |
| --- | --- | --- |
| 教师 | 创建教学班、设置加入方式、管理知识库、选择资料备课、标注重点、创建并确认题目、发布课件/练习/作业、查看班级与个人学情 | 已发布课程内容、课堂练习与作业，以及班级统计、作业统计和学习者证据 |
| 学习者 | 加入教学班、阅读课件、完成课堂练习、提交作业、查看学习进度与掌握依据 | 内容完成记录、答题结果、作业提交结果、个人学习概览 |
| 教师与学习者 | 查看具身智能三维演示，逐步观察机器人从接收指令、感知环境到规划和执行动作 | 对具身智能核心工作流程的可视化理解 |

#### 推荐演示流程

当前随本地 Demo 数据库提供以下演示账号；这些均为本地演示数据，不应用于生产环境：

| 角色 | 用户名 | 密码 | 说明 |
| --- | --- | --- | --- |
| 教师 | `jiaoshi1` | `jiaoshi1` | “具身智能课程班”的教师 |
| 学习者 | `xuesheng1` 至 `xuesheng10` | 与各自用户名相同 | 已加入“具身智能课程班” |

也可在登录页自行注册教师和学习者账号；账号角色注册后不可自行切换。若提交前清理或替换了 `backend/data/course-agent.db`，请使用新注册账号完成下述流程。

1. 启动项目并打开 `http://127.0.0.1:45173`。
2. 使用教师演示账号进入已有教学班；如需从零演示，可注册教师账号、创建教学班，并选择自由加入、申请审批或授权码加入策略。
3. 进入“知识库管理”，创建知识库并上传 Markdown 课程资料；将资料导入当前教学班。
4. 进入教学班的“课件备课”，选择资料、标注重点、创建题目并确认，然后发布课程内容；也可继续发布作业。
5. 退出教师账号，使用学习者演示账号进入班级；如需从零演示，可注册学习者账号，通过发现教学班、申请审批或授权码加入该班级。
6. 学习者进入“当前课程”，阅读教师发布的课件，完成课堂练习并提交作业，再到“学习概览”查看进度和掌握依据。
7. 切回教师账号，在“班级概览”“学习者详情”“课堂练习管理”和“作业管理”中查看学习结果与统计。
8. 在任一角色的“三维演示”页面选择演示任务，使用上一步/下一步观察机器人任务的感知、理解、规划与执行过程。

完成以上流程后，评审可以看清项目服务对象、使用方式、核心功能之间的数据流，以及最终形成的课程发布结果和学习证据。

#### 当前完成范围与已知边界

- 核心教学闭环可在本地使用 SQLite 和 Markdown 资料独立演示，不依赖外部数据库。
- DeepSeek 兼容接口未配置时，确定性的班级、课程、练习、作业和统计功能仍可使用；AI 出题、问答或分析能力会明确提示不可用。
- Markdown 可由后端本地解析；PDF、DOCX 解析需要额外部署并配置 MinerU 服务。
- 三维教学演示使用项目内置场景、任务和机器人模型，可本地运行；Webots 真实仿真环境属于外部集成，未配置时界面会显示明确状态。
- 个性化练习当前仅保留降级入口，尚未实现真实生成能力。未完成能力不影响上述推荐核心演示流程，后续优化应在项目计划书中说明。

### 1.2 完整项目源代码

#### 源代码组成

| 路径 | 内容 |
| --- | --- |
| `frontend/` | Vue 3 + TypeScript + Vite 前端、Three.js 三维演示、OpenAPI 类型生成和 Playwright E2E 测试 |
| `backend/` | FastAPI API、认证授权、教学班、知识库、备课发布、练习、作业、学情、AI 网关、Webots 连接及 pytest 测试 |
| `backend/data/` | SQLite 数据库和本地上传文件目录；应用启动时会初始化所需表结构 |
| `third_party/MinerU/` | PDF/DOCX 文档解析相关的第三方 MinerU 源码与说明 |
| `start.ps1` | Windows 下统一启动、日志记录和进程清理脚本 |
| `README.md` | 产品 Demo、配置、启动、验证和源代码交付说明 |
| `UPDATE_LOG.md` | 项目修改记录 |

提交源代码时应保留业务源码、静态资源、依赖清单与锁文件、环境变量示例、数据库初始化逻辑、测试及本文档。不要提交真实 API 密钥、`.runtime/` 运行日志、前端 `node_modules/`、构建产物或 Python 虚拟环境；这些内容均可按下述步骤重新生成。

## 技术栈与运行环境

- Node.js 24
- npm 11
- Python 3.13（由 `backend/.python-version` 固定）
- uv 0.8 或更高（后端依赖由 `backend/uv.lock` 锁定）
- Vue 3.5、TypeScript 5.8、Vite 7、Three.js 0.180
- FastAPI 0.116、Pydantic 2.11、Uvicorn 0.35、SQLite
- Chrome（仅运行 Playwright E2E 测试时需要）

## 首次安装

在项目根目录执行：

```powershell
cd backend
uv sync --dev

cd ..\frontend
npm install
cd ..
```

## 配置说明

### 必需配置

一键启动脚本会自动生成至少 32 字符的本地 JWT 密钥，并保存到 Git 已忽略的 `.runtime/jwt-secret.txt`，因此本地 Demo 无需手工创建 `.env`。

手动启动或部署时，可复制 `backend/.env.example` 为 `backend/.env`，至少设置：

```dotenv
COURSE_AGENT_JWT_SECRET=replace-with-at-least-32-random-characters
COURSE_AGENT_DATABASE_PATH=data/course-agent.db
COURSE_AGENT_ALLOWED_ORIGINS=http://127.0.0.1:45173,http://localhost:45173
```

前端通过 `VITE_API_BASE_URL` 指向后端。手动启动时可复制 `frontend/.env.example` 为 `frontend/.env`，并使端口与实际后端一致：

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:38117
```

### 可选 AI 模型配置

项目通过 OpenAI 兼容聊天接口接入 DeepSeek。启用真实 AI 能力时，在 `backend/.env` 中设置：

```dotenv
CANVAS_AGENT_LLM_API_KEY=replace-with-your-api-key
CANVAS_AGENT_LLM_BASE_URL=https://api.deepseek.com/v1
CANVAS_AGENT_LLM_MODEL=deepseek-v4-flash
CANVAS_AGENT_LLM_TIMEOUT_SECONDS=20
```

API Key 不得提交到 Git。模型名称必须以服务商当前实际提供的模型为准；未配置密钥时系统会显式降级，不会伪造 AI 结果。

### 可选文档解析配置

仅使用 Markdown 资料时无需额外服务。解析 PDF 或 DOCX 时，需要单独部署 MinerU，并在 `backend/.env` 中设置：

```dotenv
MINERU_BASE_URL=http://mineru.internal:8080
PARSING_TIMEOUT=300
MAX_PAGES=100
MAX_PARAGRAPHS=1000
MAX_OUTPUT_SIZE=10485760
```

MinerU 的部署与安全边界详见 `backend/app/document_parsing/README.md` 和 `third_party/MinerU/README_zh-CN.md`。

## 启动方式

### 推荐：Windows 一键启动

在项目根目录执行：

```powershell
.\start.ps1
```

默认地址：

- 产品 Demo：`http://127.0.0.1:45173`
- 后端 API：`http://127.0.0.1:38117`
- Swagger 接口文档：`http://127.0.0.1:38117/docs`
- 运行日志：项目根目录 `.runtime/`

如默认端口已被占用：

```powershell
.\start.ps1 -BackendPort 8002 -FrontendPort 5174
```

脚本会把实际前端地址写入后端 CORS 配置，并把实际后端地址传给前端。按 `Ctrl+C` 可同时终止脚本创建的前后端进程树；任一服务异常退出时，脚本也会清理另一服务。

### 分别启动

后端：

```powershell
cd backend
$env:COURSE_AGENT_JWT_SECRET='replace-with-at-least-32-random-characters'
uv run uvicorn app.run:app --host 127.0.0.1 --port 38117
```

前端（另开终端）：

```powershell
cd frontend
$env:VITE_API_BASE_URL='http://127.0.0.1:38117'
npm run dev -- --host 127.0.0.1 --port 45173
```
