
#define MyAppName "AgenteUTN"
#define MyAppVersion "1.5"
#define MyAppExeName "AgenteUTN.exe"

[Setup]
AppId={{D91C6E72-18B9-4F6B-9B2D-4CD5B9E23810}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\AgenteUTN
DefaultGroupName={#MyAppName}
OutputDir=output
OutputBaseFilename=AgenteUTN_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Types]
Name: "full"; Description: "Instalación completa"; Flags: iscustom

[Components]
Name: "diagnostico"; Description: "AgenteUTN - Aplicación de diagnóstico"; Types: full
Name: "sevenzip"; Description: "7-Zip - Compresor de archivos"; Types: full

[Files]
Source: "..\dist\AgenteUTN.exe"; DestDir: "{app}"; Components: diagnostico; Flags: ignoreversion
Source: "redist\7z-installer-x64.exe"; DestDir: "{tmp}"; Components: sevenzip; Flags: deleteafterinstall

[Icons]
Name: "{group}\AgenteUTN"; Filename: "{app}\{#MyAppExeName}"; Components: diagnostico
Name: "{autodesktop}\AgenteUTN"; Filename: "{app}\{#MyAppExeName}"; Components: diagnostico; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; Flags: unchecked

[Run]
Filename: "{tmp}\7z-installer-x64.exe"; Parameters: "/S"; StatusMsg: "Instalando 7-Zip..."; Components: sevenzip; Flags: waituntilterminated
Filename: "{app}\{#MyAppExeName}"; Description: "Ejecutar AgenteUTN"; Components: diagnostico; Flags: nowait postinstall skipifsilent
