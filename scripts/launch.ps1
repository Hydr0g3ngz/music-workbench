param(
    [ValidateRange(1024, 65535)][int]$Port = 8920,
    [string]$Python = '',
    [string]$LyricsPython = '',
    [switch]$Online
)
# Compatibility alias; new instructions use launch-workbench.ps1.
& (Join-Path $PSScriptRoot 'launch-workbench.ps1') @PSBoundParameters
exit $LASTEXITCODE
