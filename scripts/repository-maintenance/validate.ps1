[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
Set-Location -LiteralPath $repoRoot

$required = @(
    'README.md',
    'README.zh-CN.md',
    'LICENSE',
    'CODE_OF_CONDUCT.md',
    'SECURITY.md',
    'SUPPORT.md',
    'GOVERNANCE.md',
    'CITATION.cff',
    '.github/PULL_REQUEST_TEMPLATE.md',
    '.github/ISSUE_TEMPLATE/config.yml',
    '.github/ISSUE_TEMPLATE/skill-failure.yml',
    '.github/ISSUE_TEMPLATE/theory-challenge.yml',
    '.github/ISSUE_TEMPLATE/documentation.yml',
    '.agents/plugins/marketplace.json',
    'plugins/rcf-focus/.codex-plugin/plugin.json',
    'plugins/rcf-focus/skills/focus/SKILL.md',
    'plugins/rcf-focus/skills/recursive-center-field-dynamics/SKILL.md',
    'plugins/rcf-focus/skills/recursive-center-field-dynamics/references/sidecar-runtime.md',
    'plugins/rcf-focus/skills/recursive-center-field-dynamics/scripts/focus_runtime.py',
    'plugins/rcf-focus/skills/recursive-center-field-dynamics/scripts/field_state.py',
    'plugins/rcf-address/.codex-plugin/plugin.json',
    'plugins/rcf-address/skills/recursive-field-addressing/SKILL.md',
    'plugins/rcf-address/skills/recursive-field-addressing/scripts/address_engine.py',
    'plugins/rcf-distill/.codex-plugin/plugin.json',
    'plugins/rcf-distill/skills/distill-conversation-ideas/SKILL.md',
    'docs/methodology/README.md',
    'docs/spec',
    'docs/release-scope.md',
    'docs/dynamic-addressing/README.md',
    'RELEASE_SNAPSHOT.md',
    'release-manifest.json',
    'CHANGELOG.md',
    'scripts/repository-maintenance/hash_release.py',
    '.github/workflows/validate.yml'
)
$missing = @($required | Where-Object { -not (Test-Path -LiteralPath (Join-Path $repoRoot $_)) })
if ($missing.Count -gt 0) { throw ('Missing required files: ' + ($missing -join ', ')) }

& python -m py_compile 'plugins/rcf-focus/skills/recursive-center-field-dynamics/scripts/focus_runtime.py' 'plugins/rcf-focus/skills/recursive-center-field-dynamics/scripts/field_state.py' 'plugins/rcf-address/skills/recursive-field-addressing/scripts/address_engine.py'
if ($LASTEXITCODE -ne 0) { throw 'Python compile check failed.' }
& python 'plugins/rcf-address/skills/recursive-field-addressing/scripts/address_engine.py' self-test
if ($LASTEXITCODE -ne 0) { throw 'Address engine self-test failed.' }
& python -m unittest discover -s tests -p 'test_*.py' -v
if ($LASTEXITCODE -ne 0) { throw 'Repository tests failed.' }
& python -m unittest discover -s 'plugins/rcf-focus/skills/recursive-center-field-dynamics/tests' -p 'test_*.py' -v
if ($LASTEXITCODE -ne 0) { throw 'Focus source tests failed.' }
& python 'scripts/repository-maintenance/hash_release.py' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Release hash computation failed.' }

$generated = @(Get-ChildItem -LiteralPath $repoRoot -Recurse -File -Force | Where-Object {
    $_.FullName -notlike "$repoRoot\.git\*" -and
    ($_.Extension -eq '.pyc' -or $_.FullName -match '[\\/]__pycache__[\\/]')
})
foreach ($item in $generated) {
    $relative = $item.FullName.Substring($repoRoot.Length + 1).Replace('\', '/')
    & git check-ignore -q -- $relative
    if ($LASTEXITCODE -ne 0) { throw "Generated file is not ignored: $relative" }
}

$textExtensions = @('.md', '.txt', '.json', '.yml', '.yaml', '.cff', '.csv', '.py', '.ps1')
$publicTextFiles = @(Get-ChildItem -LiteralPath $repoRoot -Recurse -File -Force | Where-Object {
    $_.FullName -notlike "$repoRoot\.git\*" -and
    $textExtensions -contains $_.Extension.ToLowerInvariant()
})
foreach ($item in $publicTextFiles) {
    $content = Get-Content -LiteralPath $item.FullName -Raw -Encoding UTF8
    if ($content -match '(?m)(?:^|[`"''])\s*[A-Za-z]:\\') {
        $relative = $item.FullName.Substring($repoRoot.Length + 1).Replace('\', '/')
        throw "Local absolute path found in public text: $relative"
    }
    if ($content -match '-----BEGIN (?:RSA |OPENSSH |EC |PGP )?PRIVATE KEY-----|github_pat_[A-Za-z0-9_]+|ghp_[A-Za-z0-9]+|sk-[A-Za-z0-9]{20,}') {
        $relative = $item.FullName.Substring($repoRoot.Length + 1).Replace('\', '/')
        throw "Credential-like content found in public text: $relative"
    }
}

& git diff --check
if ($LASTEXITCODE -ne 0) { throw 'Git whitespace check failed.' }
Write-Output 'VALID'
