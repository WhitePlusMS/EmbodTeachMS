[CmdletBinding()]
param(
    [switch]$IncludeE2E
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runId = Get-Date -Format "yyyyMMdd-HHmmss"
$runDirectory = Join-Path $PSScriptRoot (Join-Path "runs" $runId)
New-Item -ItemType Directory -Path $runDirectory -Force | Out-Null

$pythonPath = Join-Path $projectRoot "backend\.venv\Scripts\python.exe"
$npmCommand = if ($env:OS -eq "Windows_NT") { "npm.cmd" } else { "npm" }

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "未找到后端虚拟环境：$pythonPath。请先在 backend 目录执行 uv sync --dev。"
}

function Invoke-QualityCheck {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory
    )

    $logPath = Join-Path $runDirectory "$Name.log"
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    $exitCode = 1

    Push-Location $WorkingDirectory
    try {
        try {
            & $Executable @Arguments *> $logPath
            $exitCode = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }
        }
        catch {
            $_ | Out-File -FilePath $logPath -Encoding utf8
            $exitCode = 1
        }
    }
    finally {
        Pop-Location
        $timer.Stop()
    }

    $result = [PSCustomObject]@{
        name = $Name
        exit_code = $exitCode
        duration_seconds = [math]::Round($timer.Elapsed.TotalSeconds, 2)
        log = $logPath
    }

    if ($exitCode -eq 0) {
        Write-Host ("PASS {0} ({1}s)" -f $Name, $result.duration_seconds)
    }
    else {
        Write-Host ("FAIL {0} ({1}s), see {2}" -f $Name, $result.duration_seconds, $logPath)
        Get-Content -LiteralPath $logPath -Tail 20 | ForEach-Object {
            Write-Host $_
        }
    }

    return $result
}

$checks = @()
$checks += Invoke-QualityCheck `
    -Name "backend-compile" `
    -Executable $pythonPath `
    -Arguments @("-m", "compileall", "-q", "app", "tests") `
    -WorkingDirectory (Join-Path $projectRoot "backend")

$checks += Invoke-QualityCheck `
    -Name "backend-pytest" `
    -Executable $pythonPath `
    -Arguments @("-m", "pytest", "-q") `
    -WorkingDirectory (Join-Path $projectRoot "backend")

$checks += Invoke-QualityCheck `
    -Name "frontend-build" `
    -Executable $npmCommand `
    -Arguments @("run", "build") `
    -WorkingDirectory (Join-Path $projectRoot "frontend")

if ($IncludeE2E) {
    $checks += Invoke-QualityCheck `
        -Name "frontend-e2e" `
        -Executable $npmCommand `
        -Arguments @("run", "test:e2e") `
        -WorkingDirectory (Join-Path $projectRoot "frontend")
}

$checks += Invoke-QualityCheck `
    -Name "git-diff-check" `
    -Executable "git" `
    -Arguments @("diff", "--check") `
    -WorkingDirectory $projectRoot

$failedChecks = @($checks | Where-Object { $_.exit_code -ne 0 })
$passedChecks = @($checks | Where-Object { $_.exit_code -eq 0 })
$durationSeconds = [math]::Round((($checks | Measure-Object -Property duration_seconds -Sum).Sum), 2)
$score = if ($failedChecks.Count -eq 0) {
    [math]::Round(100000 - $durationSeconds, 2)
}
else {
    -1 * (1000 * $failedChecks.Count) + $passedChecks.Count
}
$status = if ($failedChecks.Count -eq 0) { "PASS" } else { "FAIL" }

$summary = [ordered]@{
    status = $status
    score = $score
    include_e2e = [bool]$IncludeE2E
    passed_checks = $passedChecks.Count
    failed_checks = $failedChecks.Count
    duration_seconds = $durationSeconds
    checks = $checks
}
$summaryPath = Join-Path $runDirectory "summary.json"
$summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $summaryPath -Encoding utf8

Write-Host "AUTORESEARCH_STATUS: $status"
Write-Host "AUTORESEARCH_SCORE: $score"
Write-Host "AUTORESEARCH_SUMMARY: $summaryPath"

if ($failedChecks.Count -gt 0) {
    exit 1
}

exit 0
