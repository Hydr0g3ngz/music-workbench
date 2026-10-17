param([string]$Output = '')
$ErrorActionPreference = 'Stop'
$launcherRepo = Split-Path $PSScriptRoot -Parent
if (-not $Output) { $Output = Join-Path $launcherRepo 'Music Workbench.exe' }
$launcherCompiler = Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
if (-not (Test-Path -LiteralPath $launcherCompiler)) { throw 'Windows .NET Framework 4 is required to build the launcher.' }
& $launcherCompiler /nologo /target:winexe /platform:x64 /optimize+ "/out:$Output" /reference:System.Windows.Forms.dll /reference:System.Drawing.dll /reference:System.Web.Extensions.dll (Join-Path $launcherRepo 'desktop/Launcher.cs')
if ($LASTEXITCODE -ne 0) { throw 'Launcher compilation failed.' }
