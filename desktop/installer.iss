#ifndef Payload
  #error Payload is required
#endif
#ifndef BuildVersion
  #define BuildVersion "0.2.0.dev14"
#endif
#ifndef BuildAppId
  #define BuildAppId "MusicWorkbench.Local.Workstation"
#endif

[Setup]
AppId={#BuildAppId}
AppName=Music Workbench
AppVersion={#BuildVersion}
AppVerName=Music Workbench {#BuildVersion}
AppPublisher=Music Workbench Contributors
AppPublisherURL=https://github.com/Hydr0g3ngz/music-workbench
DefaultDirName={localappdata}\Programs\Music Workbench
DefaultGroupName=Music Workbench
DisableProgramGroupPage=yes
DisableDirPage=no
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.19045
WizardStyle=modern
LicenseFile={#Repo}\LICENSE
InfoBeforeFile={#Repo}\desktop\installation-info.txt
OutputDir={#Destination}
OutputBaseFilename=Music-Workbench-{#BuildVersion}-Setup-x64
Compression=lzma2/fast
SolidCompression=yes
LZMANumBlockThreads=2
SetupLogging=yes
UninstallDisplayIcon={app}\Music Workbench.exe
AppMutex=MusicWorkbench.Desktop.Running
CloseApplications=no
RestartApplications=no
Uninstallable=yes
UsePreviousAppDir=yes
VersionInfoVersion=0.2.0.14
VersionInfoProductName=Music Workbench

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesesimplified"; MessagesFile: "{#ChineseLanguage}"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: checkedonce

[Files]
Source: "{#Payload}\*"; DestDir: "{app}"; Excludes: "__pycache__\*,*.pyc,*.log"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#WebViewInstaller}"; DestName: "WebView2Setup.exe"; Flags: dontcopy

[Icons]
Name: "{group}\Music Workbench"; Filename: "{app}\Music Workbench.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Music Workbench"; Filename: "{app}\Music Workbench.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\Music Workbench.exe"; Description: "{cm:LaunchProgram,Music Workbench}"; Flags: nowait postinstall skipifsilent

[Code]
function WebViewPresent: Boolean;
var Version: String;
begin
  Result := (RegQueryStringValue(HKLM32, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version) and (Version <> '') and (Version <> '0.0.0.0'));
  if not Result then
    Result := (RegQueryStringValue(HKCU, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version) and (Version <> '') and (Version <> '0.0.0.0'));
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var ExitCode: Integer;
begin
  Result := '';
  if FileExists(AddBackslash(ExpandConstant('{app}')) + '.studio.sqlite3') then begin
    Result := 'Choose a program folder separate from your music projects. / 请选择独立的程序目录，不要选择作品数据目录。';
    exit;
  end;
  if not WebViewPresent then begin
    WizardForm.StatusLabel.Caption := 'Installing desktop display component / 正在安装桌面显示组件…';
    ExtractTemporaryFile('WebView2Setup.exe');
    if not Exec(ExpandConstant('{tmp}\WebView2Setup.exe'), '/silent /install', '', SW_HIDE, ewWaitUntilTerminated, ExitCode) then
      Result := 'Could not start the display component installer. / 无法启动桌面显示组件安装。'
    else if not WebViewPresent then
      Result := 'The display component could not be installed. Please retry. / 桌面显示组件安装未完成，请重试。';
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if (CurPageID = wpSelectDir) and FileExists(AddBackslash(WizardDirValue) + '.studio.sqlite3') then begin
    SuppressibleMsgBox('Choose a program folder separate from your music projects. / 请选择独立的程序目录，不要选择作品数据目录。', mbError, MB_OK, IDOK);
    Result := False;
  end;
end;
