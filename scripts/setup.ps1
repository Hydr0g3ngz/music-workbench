param(
    [ValidateSet('preview', 'full')][string]$Mode = 'full',
    [ValidateSet('cpu', 'cuda')][string]$Device = 'cuda',
    [string]$Python = 'py',
    [switch]$DownloadModels
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
        if ($Python -eq 'py') {
            $availablePython = & $Python -0p
            if ($availablePython -match '3\.12') { & $Python -3.12 -m venv .venv }
            elseif ($availablePython -match '3\.11') { & $Python -3.11 -m venv .venv }
            else { throw 'Install Python 3.11 or 3.12 from python.org, then retry.' }
        }
        else { & $Python -m venv .venv }
        if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 or 3.12 is required.' }
    }
    $projectPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    & $projectPython -c 'import sys; assert (3,11) <= sys.version_info[:2] < (3,13), "Python 3.11 or 3.12 is required"'
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 or 3.12 is required.' }
    & $projectPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw 'pip setup failed' }
    if ($Mode -eq 'full') {
        $index = if ($Device -eq 'cuda') { 'https://download.pytorch.org/whl/cu121' } else { 'https://download.pytorch.org/whl/cpu' }
        & $projectPython -m pip install 'torch==2.5.1' 'torchaudio==2.5.1' --index-url $index
        if ($LASTEXITCODE -ne 0) { throw 'PyTorch installation failed' }
    }
    $extras = if ($Mode -eq 'full') { 'ui,inference' } else { 'ui' }
    $wheel = Get-ChildItem -LiteralPath (Join-Path $projectRoot 'packages') -Filter 'music_workbench_local-*.whl' -ErrorAction SilentlyContinue | Select-Object -First 1
    $package = if ($wheel) { "$($wheel.FullName)[$extras]" } else { ".[$extras]" }
    & $projectPython -m pip install $package
    if ($LASTEXITCODE -ne 0) { throw 'Music Studio installation failed' }
    if ($DownloadModels) {
        if ($Mode -ne 'full') { throw '-DownloadModels requires -Mode full' }
        & $projectPython -m music_studio models download --model-dir '.cache/models' --device $Device
        if ($LASTEXITCODE -ne 0) { throw 'Model download failed; rerun to resume.' }
    }
    & $projectPython -m music_studio doctor
    Write-Host 'Ready. Run scripts/launch.ps1 or double-click Start-Music-Studio.cmd.'
} finally { Pop-Location }
