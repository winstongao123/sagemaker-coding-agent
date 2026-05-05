param(
    [string]$RepoRoot = "D:\Github\sagemaker-coding-agent",
    [string]$Label = "pre_review_smoke",
    [string]$OutPath = "",
    [string]$ErrPath = "",
    [int]$TimeoutSeconds = 120
)

$ErrorActionPreference = "Stop"

$ClaudeCmd = "C:\Users\winst\AppData\Roaming\npm\claude.cmd"
$Expected = "CLAUDE_REVIEWER_READY $Label"

if (-not (Test-Path -LiteralPath $ClaudeCmd)) {
    throw "Claude command not found: $ClaudeCmd"
}

Set-Location -LiteralPath $RepoRoot

if ([string]::IsNullOrWhiteSpace($OutPath)) {
    $OutPath = "compact_v5/_status/v5_completion_audit/logs/claude-smoke-$Label.out.txt"
}
if ([string]::IsNullOrWhiteSpace($ErrPath)) {
    $ErrPath = "compact_v5/_status/v5_completion_audit/logs/claude-smoke-$Label.err.txt"
}

$outFull = Join-Path $RepoRoot $OutPath
$errFull = Join-Path $RepoRoot $ErrPath
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $outFull) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $errFull) | Out-Null

Remove-Item -LiteralPath $outFull -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $errFull -ErrorAction SilentlyContinue

$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = "cmd.exe"
$psi.WorkingDirectory = $RepoRoot
$psi.UseShellExecute = $false
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.CreateNoWindow = $true

$psi.ArgumentList.Add("/d")
$psi.ArgumentList.Add("/c")
$psi.ArgumentList.Add("`"$ClaudeCmd`" -p --model opus --effort xhigh --permission-mode dontAsk --setting-sources user --tools `"`" --output-format text")

if ($psi.Environment.ContainsKey("ANTHROPIC_API_KEY")) {
    $psi.Environment.Remove("ANTHROPIC_API_KEY") | Out-Null
}

$proc = [System.Diagnostics.Process]::new()
$proc.StartInfo = $psi

[void]$proc.Start()
$proc.StandardInput.WriteLine("Reply exactly: $Expected")
$proc.StandardInput.Close()

$stdoutTask = $proc.StandardOutput.ReadToEndAsync()
$stderrTask = $proc.StandardError.ReadToEndAsync()

if (-not $proc.WaitForExit($TimeoutSeconds * 1000)) {
    try { $proc.Kill($true) } catch { try { $proc.Kill() } catch {} }
    "TIMEOUT after $TimeoutSeconds seconds" | Set-Content -LiteralPath $errFull -Encoding UTF8
    "" | Set-Content -LiteralPath $outFull -Encoding UTF8
    Write-Output "ExitCode: TIMEOUT"
    Write-Output "StdoutPath: $OutPath"
    Write-Output "StderrPath: $ErrPath"
    exit 124
}

$stdout = $stdoutTask.GetAwaiter().GetResult()
$stderr = $stderrTask.GetAwaiter().GetResult()

$stdout | Set-Content -LiteralPath $outFull -Encoding UTF8
$stderr | Set-Content -LiteralPath $errFull -Encoding UTF8

$actual = $stdout.Trim()
Write-Output "ExitCode: $($proc.ExitCode)"
Write-Output "Stdout: $actual"
Write-Output "Stderr: $($stderr.Trim())"
Write-Output "StdoutPath: $OutPath"
Write-Output "StderrPath: $ErrPath"
Write-Output "ExactMatch: $($actual -eq $Expected)"

if ($proc.ExitCode -ne 0) {
    exit $proc.ExitCode
}
if ($actual -ne $Expected) {
    exit 2
}

exit 0
