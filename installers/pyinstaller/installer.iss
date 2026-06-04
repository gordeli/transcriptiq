; Inno Setup script — builds Transcriptiq-Setup.exe from the PyInstaller output.
; Compiled in CI with: ISCC.exe installers\pyinstaller\installer.iss
; Expects the PyInstaller one-folder build at dist\Transcriptiq\.

#define MyAppName "Transcriptiq"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Ivan Gordeliy"
#define MyAppURL "https://github.com/gordeli/transcriptiq"
#define MyAppExeName "Transcriptiq.exe"

[Setup]
AppId={{8F3C2A10-7B4E-4D9A-9E21-TRANSCRIPTIQ01}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer_output
OutputBaseFilename=Transcriptiq-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "..\..\dist\Transcriptiq\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
