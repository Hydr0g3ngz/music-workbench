param([string]$Python = "")
$ErrorActionPreference = "Stop"
$nextRepo = Split-Path $PSScriptRoot -Parent
$nextEnvironment = Join-Path $nextRepo ".venv-next"
$nextPython = Join-Path $nextEnvironment "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $nextPython)) {
    if ($Python) {
        & $Python -X utf8 -c "import sys; assert (3,11) <= sys.version_info[:2] < (3,13), 'Python 3.11 / 3.12 is required'"
        if ($LASTEXITCODE -ne 0) { throw "Choose Python 3.11 / 3.12 with -Python." }
        & $Python -m venv $nextEnvironment
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.12 -m venv $nextEnvironment
        if ($LASTEXITCODE -ne 0) { & py -3.11 -m venv $nextEnvironment }
    } else {
        & python -X utf8 -c "import sys; assert (3,11) <= sys.version_info[:2] < (3,13), 'Python 3.11 / 3.12 is required'"
        if ($LASTEXITCODE -ne 0) { throw "Install Python 3.11 / 3.12, or pass -Python <interpreter>." }
        & python -m venv $nextEnvironment
    }
    if ($LASTEXITCODE -ne 0) { throw "Install Python 3.11 or 3.12, then run setup-next.ps1 again." }
}
& $nextPython -X utf8 -c "import sys; assert (3,11) <= sys.version_info[:2] < (3,13), 'Python 3.11 / 3.12 is required'"
if ($LASTEXITCODE -ne 0) { throw "The Next environment needs Python 3.11 / 3.12." }
& $nextPython -m pip install -e ($nextRepo + "[workstation]")
if ($LASTEXITCODE -ne 0) { throw "Next dependency installation failed." }
Write-Host "Next is ready. Run Start-Music-Studio-Next.cmd. Neural models are installed separately."
