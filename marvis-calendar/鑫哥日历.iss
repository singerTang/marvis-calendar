; 鑫哥日历 — Inno Setup 安装脚本
; 编译：ISCC.exe 鑫哥日历.iss （从 marvis-calendar 目录执行）
; 依赖产物：dist\鑫哥日历\ （PyInstaller onedir 输出）

#define MyAppName "鑫哥日历"
#define MyAppVersion "0.1.1"
#define MyAppPublisher "鑫哥"
#define MyAppExeName "鑫哥日历.exe"

[Setup]
AppId={{8F3A1C2D-7B4E-4E9A-9C1F-2A6D5E8B3F10}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=鑫哥日历_安装_v{#MyAppVersion}
SetupIconFile=src\assets\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin

[Files]
Source: "dist\鑫哥日历\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
