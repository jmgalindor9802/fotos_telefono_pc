; ===========================================================
; The Elite Flower - Instalador Windows (Inno Setup)
; ===========================================================
; Para compilar: abrir este archivo en Inno Setup y click "Compile"
; Genera: EliteFlower_Setup.exe

#define MyAppName "The Elite Flower"
#define MyAppVersion "1.0"
#define MyAppPublisher "Elite Flowers Mallas"
#define MyAppExeName "main.exe"

; Ajusta esta ruta si tu carpeta dist/main esta en otra ubicacion
#define MyAppSource "D:\PROYECTOS DE SOFTWARE\ELITE FLOWERS MALLAS\fotos_telefono_pc\dist\main"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=D:\PROYECTOS DE SOFTWARE\ELITE FLOWERS MALLAS\fotos_telefono_pc\installer
OutputBaseFilename=EliteFlower_Setup
SetupIconFile=D:\PROYECTOS DE SOFTWARE\ELITE FLOWERS MALLAS\fotos_telefono_pc\elite_flower.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UsePreviousAppDir=yes
CloseApplications=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el Escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "{#MyAppSource}\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppSource}\elite_flower.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppSource}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\fotos_recibidas"; Permissions: users-modify

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Ejecutar {#MyAppName}"; Flags: nowait postinstall skipifsilent
