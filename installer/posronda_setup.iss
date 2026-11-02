; Script Inno Setup untuk PosRonda Hub
; Mendukung Pemasangan Dwibahasa (Bahasa Indonesia & English)

#ifndef MyAppVersion
#define MyAppVersion "4.3.1"
#endif

[Setup]
AppId={{8F322987-9483-4DF1-A79B-83F67B549821}}
AppName=PosRonda Hub
AppVersion={#MyAppVersion}
AppPublisher=Ngulon Studio
AppPublisherURL=https://ngulonstudio.web.id
AppSupportURL=https://github.com/harunarrosyid/PosRonda
AppUpdatesURL=https://github.com/harunarrosyid/PosRonda/releases
DefaultDirName={autopf}\PosRonda
DefaultGroupName=PosRonda Hub
AllowNoIcons=yes
OutputDir=..
OutputBaseFilename=PosRonda-v{#MyAppVersion}-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=yes
DisableWelcomePage=no
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "id"; MessagesFile: "Indonesian.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
id.CreateDesktopIcon=Buat ikon di Desktop (Layar Utama)
id.LaunchProgram=Jalankan %1 sekarang
en.CreateDesktopIcon=Create a desktop shortcut
en.LaunchProgram=Launch %1 now

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\pkg-full\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\PosRonda Hub\PosRonda"; Filename: "{app}\PosRonda.exe"
Name: "{autoprograms}\PosRonda Hub\Panduan Penggunaan"; Filename: "{app}\PANDUAN.md"
Name: "{autoprograms}\PosRonda Hub\Uninstall PosRonda"; Filename: "{uninstallexe}"
Name: "{autodesktop}\PosRonda Hub"; Filename: "{app}\PosRonda.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PosRonda.exe"; Description: "{cm:LaunchProgram,PosRonda Hub}"; Flags: nowait postinstall skipifsilent
