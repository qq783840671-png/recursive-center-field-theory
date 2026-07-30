[CmdletBinding()]
param(
    [switch]$Fetch
)

$ErrorActionPreference = 'Stop'
$expectedOrigin = 'https://github.com/qq783840671-png/recursive-center-field-theory.git'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path

$origin = (& git -C $repoRoot remote get-url origin).Trim()
if ($LASTEXITCODE -ne 0 -or $origin -ne $expectedOrigin) {
    throw "Unexpected origin: $origin"
}

$branch = (& git -C $repoRoot branch --show-current).Trim()
$branchState = @(& git -C $repoRoot status --porcelain=v2 --branch)
$oidLine = $branchState | Where-Object { $_ -like '# branch.oid *' } | Select-Object -First 1
$head = if ($oidLine) { ($oidLine -replace '^# branch\.oid\s+', '').Trim() } else { '(unknown)' }
$head = if ($head -eq '(initial)') { '(unborn)' } else { $head }

$savedErrorAction = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
$gh = Get-Command gh -ErrorAction SilentlyContinue
if ($gh) {
    $remoteProbe = @(& gh repo view 'qq783840671-png/recursive-center-field-theory' --json nameWithOwner,defaultBranchRef,isPrivate,url 2>&1 | ForEach-Object { $_.ToString() })
} else {
    $remoteProbe = @(& git -C $repoRoot ls-remote --symref origin HEAD 2>&1 | ForEach-Object { $_.ToString() })
}
$remoteAvailable = $LASTEXITCODE -eq 0
$ErrorActionPreference = $savedErrorAction
if ($Fetch -and $remoteAvailable) {
    & git -C $repoRoot fetch --prune origin
    if ($LASTEXITCODE -ne 0) { throw 'Fetch failed.' }
}

$status = @(& git -C $repoRoot status --short)
[pscustomobject]@{
    repository = $repoRoot
    branch = $branch
    local_head = $head
    origin = $origin
    remote_available = $remoteAvailable
    remote_probe = @($remoteProbe)
    working_tree_changes = $status.Count
    status = $status
} | ConvertTo-Json -Depth 4
