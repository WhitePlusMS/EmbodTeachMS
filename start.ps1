[CmdletBinding()]
param(
    [string]$JwtSecret = $env:COURSE_AGENT_JWT_SECRET,
    [ValidateRange(1, 65535)]
    [int]$BackendPort = 38117,
    [ValidateRange(1, 65535)]
    [int]$FrontendPort = 45173
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$backendDirectory = Join-Path $projectRoot "backend"
$frontendDirectory = Join-Path $projectRoot "frontend"
$runtimeDirectory = Join-Path $projectRoot ".runtime"

function Assert-CommandExists {
    param([Parameter(Mandatory)][string]$Name)

    if ($null -eq (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "未找到命令 '$Name'，请先完成项目环境安装。"
    }
}

function Assert-PortAvailable {
    param([Parameter(Mandatory)][int]$Port)

    $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    if ($null -ne $listener) {
        throw "端口 $Port 已被占用，请终止占用进程或通过脚本参数指定其他端口。"
    }
}

function Stop-ProcessTree {
    param(
        [Parameter(Mandatory)][string]$Name,
        [AllowNull()][System.Diagnostics.Process]$Process
    )

    if ($null -eq $Process -or $Process.HasExited) {
        return
    }

    Write-Host "正在停止$Name（PID $($Process.Id)）..."
    # Kill(true) 只终止本脚本创建的进程树，避免 uv、Python 或 npm 子进程残留。
    $Process.Kill($true)
    $Process.WaitForExit()
}

New-Item -ItemType Directory -Path $runtimeDirectory -Force | Out-Null
$localSecretPath = Join-Path $runtimeDirectory "jwt-secret.txt"

if ([string]::IsNullOrWhiteSpace($JwtSecret)) {
    if (Test-Path -LiteralPath $localSecretPath) {
        $JwtSecret = (Get-Content -Raw -Encoding UTF8 -LiteralPath $localSecretPath).Trim()
    }
    else {
        # 本地开发密钥使用密码学安全随机数生成，并放入已被 Git 忽略的运行目录。
        $randomBytes = [byte[]]::new(32)
        [System.Security.Cryptography.RandomNumberGenerator]::Fill($randomBytes)
        $JwtSecret = [Convert]::ToBase64String($randomBytes)
        Set-Content `
            -LiteralPath $localSecretPath `
            -Value $JwtSecret `
            -Encoding UTF8 `
            -NoNewline
        Write-Host "已生成本地开发密钥：$localSecretPath"
    }
}

if ($JwtSecret.Length -lt 32) {
    throw "JWT 密钥必须至少包含 32 个字符；请检查参数、环境变量或 $localSecretPath。"
}

Assert-CommandExists -Name "uv"
Assert-CommandExists -Name "npm.cmd"
Assert-PortAvailable -Port $BackendPort
Assert-PortAvailable -Port $FrontendPort

if (-not (Test-Path -LiteralPath (Join-Path $frontendDirectory "node_modules"))) {
    throw "前端依赖尚未安装，请先在 frontend 目录执行 npm install。"
}

$frontendOutputLog = Join-Path $runtimeDirectory "frontend.out.log"
$frontendErrorLog = Join-Path $runtimeDirectory "frontend.err.log"

$backendProcess = $null
$frontendProcess = $null

$previousJwtSecret = $env:COURSE_AGENT_JWT_SECRET
$previousAllowedOrigins = $env:COURSE_AGENT_ALLOWED_ORIGINS
$previousDatabasePath = $env:COURSE_AGENT_DATABASE_PATH
$previousApiBaseUrl = $env:VITE_API_BASE_URL

try {
    # 环境变量由子进程继承，密钥不会出现在进程命令行中。
    $env:COURSE_AGENT_JWT_SECRET = $JwtSecret
    $env:COURSE_AGENT_ALLOWED_ORIGINS = "http://127.0.0.1:$FrontendPort,http://localhost:$FrontendPort"
    $env:COURSE_AGENT_DATABASE_PATH = Join-Path $backendDirectory "data\course-agent.db"

    $backendProcess = Start-Process `
        -FilePath "uv" `
        -ArgumentList @(
            "run", "uvicorn", "app.run:app",
            "--host", "127.0.0.1",
            "--port", "$BackendPort"
        ) `
        -WorkingDirectory $backendDirectory `
        -NoNewWindow `
        -PassThru

    $env:VITE_API_BASE_URL = "http://127.0.0.1:$BackendPort"
    $frontendProcess = Start-Process `
        -FilePath "npm.cmd" `
        -ArgumentList @(
            "run", "dev", "--",
            "--host", "127.0.0.1",
            "--port", "$FrontendPort",
            "--strictPort"
        ) `
        -WorkingDirectory $frontendDirectory `
        -WindowStyle Hidden `
        -RedirectStandardOutput $frontendOutputLog `
        -RedirectStandardError $frontendErrorLog `
        -PassThru

    Write-Host ""
    Write-Host "前后端已启动："
    Write-Host "  前端：http://127.0.0.1:$FrontendPort"
    Write-Host "  后端：http://127.0.0.1:$BackendPort"
    Write-Host "  接口文档：http://127.0.0.1:$BackendPort/docs"
    Write-Host "  后端日志：直接显示在当前 CLI"
    Write-Host "  前端日志目录：$runtimeDirectory"
    Write-Host ""
    Write-Host "按 Ctrl+C 停止前后端。"

    # 由当前脚本持续监管服务；任一服务异常退出时，立即清理另一服务。
    while (-not $backendProcess.HasExited -and -not $frontendProcess.HasExited) {
        Start-Sleep -Milliseconds 250
    }

    if ($backendProcess.HasExited) {
        throw "后端已退出（退出码 $($backendProcess.ExitCode)），请查看当前 CLI 输出。"
    }

    throw "前端已退出（退出码 $($frontendProcess.ExitCode)），请查看 $frontendErrorLog。"
}
finally {
    $env:COURSE_AGENT_JWT_SECRET = $previousJwtSecret
    $env:COURSE_AGENT_ALLOWED_ORIGINS = $previousAllowedOrigins
    $env:COURSE_AGENT_DATABASE_PATH = $previousDatabasePath
    $env:VITE_API_BASE_URL = $previousApiBaseUrl

    Stop-ProcessTree -Name "前端" -Process $frontendProcess
    Stop-ProcessTree -Name "后端" -Process $backendProcess
}
