param(
    [ValidateRange(1024, 65535)][int]$Port = 8920,
    [string]$Python = '',
    [string]$Workspace = 'outputs/workbench',
    [string]$ModelDir = '',
    [string]$LyricsPython = '',
    [string]$InferencePython = '',
    [switch]$NoBrowser,
    [switch]$Online,
    [ValidateSet('create', 'next')][string]$Interface = 'create'
)
$ErrorActionPreference = 'Stop'
$workbenchRepo = Split-Path $PSScriptRoot -Parent
$workbenchPython = $Python
if (-not $workbenchPython) {
    foreach ($relative in @('.venv-next/Scripts/python.exe', '.venv/Scripts/python.exe', '.artifacts/workbench-env/Scripts/python.exe')) {
        $candidate = Join-Path $workbenchRepo $relative
        if (Test-Path -LiteralPath $candidate) { $workbenchPython = $candidate; break }
    }
}
if (-not $workbenchPython) {
    Write-Host 'Preparing Music Workbench. No neural models are downloaded.'
    & (Join-Path $PSScriptRoot 'setup-next.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'Workbench setup failed. Run scripts/setup-next.ps1 for details.' }
    $workbenchPython = Join-Path $workbenchRepo '.venv-next/Scripts/python.exe'
}
if (-not [IO.Path]::IsPathRooted($Workspace)) { $Workspace = Join-Path $workbenchRepo $Workspace }
$savedPath = Join-Path $Workspace '.studio-runtime.json'
if (Test-Path -LiteralPath $savedPath) {
    $saved = Get-Content -LiteralPath $savedPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $ModelDir -and $saved.model_dir) { $ModelDir = $saved.model_dir }
    if (-not $InferencePython -and $saved.inference_python) { $InferencePython = $saved.inference_python }
    if (-not $LyricsPython -and $saved.lyrics_python) { $LyricsPython = $saved.lyrics_python }
}
# The current checkout must win over an older installed package.
$env:PYTHONPATH = Join-Path $workbenchRepo 'src'
$env:PYTHONUTF8 = '1'
& $workbenchPython -X utf8 -c "import av, fastapi, uvicorn, multipart, pyebur128, scipy"
if ($LASTEXITCODE -ne 0) {
    & $workbenchPython -m pip install -e ($workbenchRepo + '[workstation]')
    if ($LASTEXITCODE -ne 0) { throw 'Workbench dependency setup failed.' }
}
$workbenchArguments = @('-X', 'utf8', '-m', 'music_studio.workbench_cli', 'ui', '--workspace', $Workspace, '--port', "$Port", '--interface', $Interface)
if ($ModelDir) { $workbenchArguments += @('--model-dir', $ModelDir) }
if ($LyricsPython) { $workbenchArguments += @('--lyrics-python', $LyricsPython) }
if ($InferencePython) { $workbenchArguments += @('--inference-python', $InferencePython) }
if ($Online) { $workbenchArguments += '--online' } else { $workbenchArguments += '--offline' }
if (-not $NoBrowser) { $workbenchArguments += '--open' }
Write-Host 'Music Workbench: composition, arrangement, recording and mixing.'
Write-Host "Workspace: $Workspace"
& $workbenchPython @workbenchArguments
exit $LASTEXITCODE
