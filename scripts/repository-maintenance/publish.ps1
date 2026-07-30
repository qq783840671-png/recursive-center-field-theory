[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Message,

    [switch]$ExplicitUpload
)

$ErrorActionPreference = 'Stop'
if (-not $ExplicitUpload) {
    throw 'Remote publication requires an explicit upload instruction and -ExplicitUpload.'
}

$expectedOrigin = 'https://github.com/qq783840671-png/recursive-center-field-theory.git'
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
Set-Location -LiteralPath $repoRoot
$origin = (& git -C $repoRoot remote get-url origin).Trim()
if ($origin -ne $expectedOrigin) { throw "Unexpected origin: $origin" }

& git ls-remote origin HEAD *> $null
if ($LASTEXITCODE -ne 0) {
    throw 'Target GitHub repository is unavailable. Repository creation requires a separate explicit create-and-upload instruction.'
}

& (Join-Path $scriptRoot 'validate.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Validation failed.' }

$remoteHash = (& git ls-remote origin 'refs/heads/main' | ForEach-Object { ($_ -split "`t")[0] }).Trim()
$savedErrorAction = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
$localBefore = (& git rev-parse --verify HEAD 2>$null)
$hasLocalCommit = $LASTEXITCODE -eq 0
$ErrorActionPreference = $savedErrorAction
if ($hasLocalCommit -and $remoteHash) {
    $localBefore = $localBefore.Trim()
    & git merge-base --is-ancestor $remoteHash $localBefore
    if ($LASTEXITCODE -ne 0) { throw 'Remote main is ahead or divergent; refusing to publish.' }
} elseif ($remoteHash -and -not $hasLocalCommit) {
    throw 'Remote main exists but the local repository has no commit; reconcile before publishing.'
}

& git add -A
if ($LASTEXITCODE -ne 0) { throw 'Staging failed.' }
& git diff --cached --quiet
if ($LASTEXITCODE -eq 0) { throw 'No staged changes to publish.' }

& git commit -m $Message
if ($LASTEXITCODE -ne 0) { throw 'Commit failed.' }
$localHash = (& git rev-parse HEAD).Trim()

$env:FOCUS_EXPLICIT_UPLOAD = '1'
try {
    & git push origin 'HEAD:main'
    if ($LASTEXITCODE -ne 0) { throw 'Push failed.' }
} finally {
    Remove-Item Env:FOCUS_EXPLICIT_UPLOAD -ErrorAction SilentlyContinue
}

$verifiedRemote = (& git ls-remote origin 'refs/heads/main' | ForEach-Object { ($_ -split "`t")[0] }).Trim()
if ($verifiedRemote -ne $localHash) { throw 'Remote verification failed.' }

$ledger = Join-Path (Split-Path -Parent (Split-Path -Parent $repoRoot)) '已公开\同步记录.tsv'
$timestamp = [DateTime]::UtcNow.ToString('o')
Add-Content -LiteralPath $ledger -Encoding UTF8 -Value "$timestamp`tqq783840671-png/recursive-center-field-theory`tmain`t$localHash`t$verifiedRemote`tpush`tverified"
Write-Output "Published and verified: $verifiedRemote"
