param(
    [string]$Block,
    [switch]$All,
    [switch]$Summary
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..\..\..")
$AuditScript = Join-Path $RepoRoot "compact_v5\_status\scripts\scope_audit.py"

if (-not (Test-Path -LiteralPath $AuditScript)) {
    throw "Missing scope audit script: $AuditScript"
}

$argsList = @()
if ($All) {
    $argsList += "--all"
} elseif ($Block) {
    $argsList += "--block"
    $argsList += $Block
} else {
    throw "Use -Block <BLOCK> or -All"
}

if ($Summary) {
    $argsList += "--summary"
}
$argsList += "--strict"

Push-Location $RepoRoot
try {
    py -3.11 $AuditScript @argsList
    if ($LASTEXITCODE -ne 0) {
        throw "Scope completeness gate failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}
