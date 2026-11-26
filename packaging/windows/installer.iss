; Inno Setup 6 script -> dist\BulkPhotoEditor-Setup-<version>.exe
; Build:  ISCC.exe /DAppVersion=6.1.0 packaging\windows\installer.iss   (build_windows.bat does it)
#ifndef AppVersion
  #define AppVersion "6.1.0"
#endif
#define AppName "Bulk Photo Editor"
#define AppExe  "BulkPhotoEditor.exe"

[Setup]
AppId={{6F0B3C2A-52D1-4C7E-9B7A-3D1E8F4A2C55}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Bulk Photo Editor
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=..\..\dist
OutputBaseFilename=BulkPhotoEditor-Setup-{#AppVersion}
SetupIconFile=BulkPhotoEditor.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
; Install for just me without an admin prompt, or for everyone if the user chooses
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ChangesAssociations=no

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "explorermenu"; Description: "Add ""Open in Bulk Photo Editor"" to the right-click menu of folders and photos"; GroupDescription: "Explorer integration:"

[Files]
Source: "..\..\dist\BulkPhotoEditor\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
; Right-click a folder (or the empty background inside one) -> Open in Bulk Photo Editor
Root: HKA; Subkey: "Software\Classes\Directory\shell\BulkPhotoEditor"; ValueType: string; ValueData: "Open in {#AppName}"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKA; Subkey: "Software\Classes\Directory\shell\BulkPhotoEditor"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#AppExe}"""; Tasks: explorermenu
Root: HKA; Subkey: "Software\Classes\Directory\shell\BulkPhotoEditor\command"; ValueType: string; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: explorermenu
Root: HKA; Subkey: "Software\Classes\Directory\Background\shell\BulkPhotoEditor"; ValueType: string; ValueData: "Open this folder in {#AppName}"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKA; Subkey: "Software\Classes\Directory\Background\shell\BulkPhotoEditor"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#AppExe}"""; Tasks: explorermenu
Root: HKA; Subkey: "Software\Classes\Directory\Background\shell\BulkPhotoEditor\command"; ValueType: string; ValueData: """{app}\{#AppExe}"" ""%V"""; Tasks: explorermenu
; Right-click photos -> Open in Bulk Photo Editor
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\image\shell\BulkPhotoEditor"; ValueType: string; ValueData: "Open in {#AppName}"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\image\shell\BulkPhotoEditor"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#AppExe}"""; Tasks: explorermenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\image\shell\BulkPhotoEditor"; ValueName: "MultiSelectModel"; ValueType: string; ValueData: "Player"; Tasks: explorermenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\image\shell\BulkPhotoEditor\command"; ValueType: string; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: explorermenu

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
