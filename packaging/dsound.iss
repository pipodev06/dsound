; Instalador de dsound para Windows (Inno Setup 6).
; Lo arma el workflow "Binarios" después de packaging/build.py:
;   iscc /DAppVersion=0.3.0 packaging\dsound.iss
; Instala para el usuario actual (sin pedir permisos de administrador) en
; %LOCALAPPDATA%\Programs\dsound, con acceso directo en el menú Inicio.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{6F1D2A3B-8C47-4E5A-9B3D-2D50C0A1D5E7}
AppName=dsound
AppVersion={#AppVersion}
AppVerName=dsound {#AppVersion}
AppPublisher=pipodev06
AppPublisherURL=https://github.com/pipodev06/dsound
AppSupportURL=https://github.com/pipodev06/dsound/issues
AppUpdatesURL=https://github.com/pipodev06/dsound/releases
DefaultDirName={localappdata}\Programs\dsound
DisableProgramGroupPage=yes
DisableDirPage=auto
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=dsound-{#AppVersion}-windows-x64-setup
SetupIconFile=dsound.ico
UninstallDisplayIcon={app}\dsound.exe
UninstallDisplayName=dsound
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; cierra dsound si está abierto (por ejemplo, al actualizar)
CloseApplications=force

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startup"; Description: "Abrir dsound al iniciar Windows"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\dsound\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\dsound"; Filename: "{app}\dsound.exe"
Name: "{autodesktop}\dsound"; Filename: "{app}\dsound.exe"; Tasks: desktopicon
Name: "{userstartup}\dsound"; Filename: "{app}\dsound.exe"; Parameters: "--background"; Tasks: startup

[Run]
Filename: "{app}\dsound.exe"; Description: "{cm:LaunchProgram,dsound}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; la música descargada y la cola (~\.dsound) no se tocan; solo lo generado junto al .exe
Type: files; Name: "{app}\.env"
