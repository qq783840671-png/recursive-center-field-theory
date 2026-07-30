[CmdletBinding()]
param(
    [switch]$Fetch
)

$ErrorActionPreference = 'Stop'
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $scriptRoot 'validate.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Validation failed.' }
& (Join-Path $scriptRoot 'status.ps1') -Fetch:$Fetch
if ($LASTEXITCODE -ne 0) { throw 'Status collection failed.' }

Write-Output 'No files were staged, committed, or pushed.'

