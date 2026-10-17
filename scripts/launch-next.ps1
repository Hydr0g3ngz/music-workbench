param(
    [int]$Port = 8900,
    [string]$Python = "",
    [string]$Workspace = "outputs/next",
    [string]$ModelDir = "",
    [string]$LyricsPython = "",
    [string]$InferencePython = "",
    [switch]$NoBrowser,
    [ValidateSet('next', 'create')][string]$Interface = 'next'
)
$ErrorActionPreference = "Stop"
$nextRepo = Split-Path $PSScriptRoot -Parent
if ($Port -lt 1024 -or $Port -gt 65520) { throw "Port must be between 1024 and 65520." }
$nextPython = $Python
if (-not $nextPython) {
    foreach ($relative in @(".venv-next/Scripts/python.exe", ".artifacts/workbench-env/Scripts/python.exe")) {
        $candidate = Join-Path $nextRepo $relative
        if (Test-Path -LiteralPath $candidate) { $nextPython = $candidate; break }
    }
}
if (-not $nextPython) {
    Write-Host "First start: installing the separate Next runtime. Neural models are not downloaded."
    & (Join-Path $PSScriptRoot "setup-next.ps1")
    if ($LASTEXITCODE -ne 0) { throw "Next setup failed. Run scripts/setup-next.ps1 to see the details." }
    $nextPython = Join-Path $nextRepo ".venv-next/Scripts/python.exe"
}
& $nextPython -X utf8 -c "import importlib.util, sys; sys.exit(0 if all(importlib.util.find_spec(n) for n in ('av','fastapi','pyebur128','scipy')) else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Updating the separate Next editing runtime. Neural models are not downloaded.'
    & $nextPython -m pip install -e ($nextRepo + '[workstation]')
    if ($LASTEXITCODE -ne 0) { throw 'Next runtime update failed. Run scripts/setup-next.ps1 for details.' }
}
if (-not [IO.Path]::IsPathRooted($Workspace)) { $Workspace = Join-Path $nextRepo $Workspace }
$nextRuntimeFile = Join-Path $Workspace ".studio-runtime.json"
if (Test-Path -LiteralPath $nextRuntimeFile) {
    $nextSavedRuntime = Get-Content -LiteralPath $nextRuntimeFile -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $ModelDir -and $nextSavedRuntime.model_dir) { $ModelDir = $nextSavedRuntime.model_dir }
    if (-not $InferencePython -and $nextSavedRuntime.inference_python) { $InferencePython = $nextSavedRuntime.inference_python }
    if (-not $LyricsPython -and $nextSavedRuntime.lyrics_python) { $LyricsPython = $nextSavedRuntime.lyrics_python }
}
if (-not $ModelDir) { $ModelDir = Join-Path $nextRepo ".cache/models" }
# This checkout must win over editable packages installed for the retained stable version.
$env:PYTHONPATH = Join-Path $nextRepo "src"
$env:PYTHONUTF8 = "1"
$nextArguments = @("-X", "utf8", "-m", "music_studio.workbench_cli", "ui", "--interface", $Interface, "--workspace", $Workspace, "--port", "$Port", "--model-dir", $ModelDir, "--offline")
if (-not $LyricsPython) {
    $candidate = Join-Path $nextRepo ".artifacts/lyrics-env/Scripts/python.exe"
    if (Test-Path -LiteralPath $candidate) { $LyricsPython = $candidate }
}
if ($LyricsPython) { $nextArguments += @("--lyrics-python", $LyricsPython) }
if (-not $InferencePython) {
    $candidate = Join-Path $nextRepo ".venv-next-models/Scripts/python.exe"
    if (Test-Path -LiteralPath $candidate) { $InferencePython = $candidate }
}
if ($InferencePython) { $nextArguments += @("--inference-python", $InferencePython) }
if (-not $NoBrowser) { $nextArguments += "--open" }
$nextEntry = if ($Interface -eq 'create') { 'station.html' } else { 'next.html' }
Write-Host "Preparing Music Workbench; the page opens after it is ready."
Write-Host "Workspace: $Workspace"
& $nextPython @nextArguments
exit $LASTEXITCODE
