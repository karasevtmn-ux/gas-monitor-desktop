
#define AppName "GAS Monitor"
#define AppExeName "GASMonitor.exe"
#define AppVersion "0.2"

[Setup]
AppId={{9A9F0A0C-9D08-4C7A-9C9B-0B6E9E0F8E77}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputBaseFilename=GASMonitor-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Languages]
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"

[Files]
Source: "distGASMonitor"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}{#AppName}"; Filename: "{app}\{#AppExeName}"

[Run]
Filename: "{app}{#AppExeName}"; Description: "Запустить"; Flags: nowait postinstall skipifsilent
