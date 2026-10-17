param([Parameter(Mandatory=$true)][string]$Output, [string]$Sdk = '.artifacts/desktop-build-tools/webview2')
$ErrorActionPreference = 'Stop'
$desktopRepo = Split-Path $PSScriptRoot -Parent
if (-not [IO.Path]::IsPathRooted($Sdk)) { $Sdk = Join-Path $desktopRepo $Sdk }
$desktopCompiler = Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
$desktopOutput = [IO.Path]::GetFullPath($Output)
$desktopFolder = Split-Path $desktopOutput -Parent
New-Item -ItemType Directory -Force -Path $desktopFolder | Out-Null
$desktopCore = Join-Path $Sdk 'lib/net462/Microsoft.Web.WebView2.Core.dll'
$desktopForms = Join-Path $Sdk 'lib/net462/Microsoft.Web.WebView2.WinForms.dll'
& $desktopCompiler /nologo /target:winexe /platform:x64 /optimize+ "/out:$desktopOutput" "/win32manifest:$(Join-Path $desktopRepo 'desktop/app.manifest')" /reference:System.Windows.Forms.dll /reference:System.Drawing.dll /reference:System.Web.Extensions.dll "/reference:$desktopCore" "/reference:$desktopForms" (Join-Path $desktopRepo 'desktop/App.cs')
if ($LASTEXITCODE -ne 0) { throw 'Desktop compilation failed.' }
Copy-Item -LiteralPath $desktopCore,$desktopForms -Destination $desktopFolder
Copy-Item -LiteralPath (Join-Path $Sdk 'runtimes/win-x64/native/WebView2Loader.dll') -Destination $desktopFolder
Copy-Item -LiteralPath (Join-Path $Sdk 'LICENSE.txt') -Destination (Join-Path $desktopFolder 'WEBVIEW2-SDK-LICENSE.txt')
@'
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <startup useLegacyV2RuntimeActivationPolicy="true"><supportedRuntime version="v4.0" sku=".NETFramework,Version=v4.7.2" /></startup>
  <System.Windows.Forms.ApplicationConfigurationSection><add key="DpiAwareness" value="PerMonitorV2" /></System.Windows.Forms.ApplicationConfigurationSection>
  <runtime><AppContextSwitchOverrides value="Switch.System.Windows.Forms.DoNotSupportDpiChanges=false" /></runtime>
</configuration>
'@ | Set-Content -LiteralPath ($desktopOutput + '.config') -Encoding UTF8
