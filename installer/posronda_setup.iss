; Script Inno Setup untuk PosRonda Hub
; Mendukung Pemasangan Dwibahasa & Manajemen Upgrade Versi (Timpa / Simpan Data / Instal Bersih / Copot)

#ifndef MyAppVersion
#define MyAppVersion "4.4.0"
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
CloseApplications=yes
CloseApplicationsFilter=PosRonda.exe,PosRonda-Full.exe,PosRonda-Lite.exe

[Languages]
Name: "id"; MessagesFile: "Indonesian.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
id.CreateDesktopIcon=Buat ikon di Desktop
id.LaunchProgram=Jalankan %1 sekarang
en.CreateDesktopIcon=Create a desktop shortcut
en.LaunchProgram=Launch %1 now

id.UpgradeTitle=Deteksi Instalasi Sebelumnya
id.UpgradeSubTitle=Pilih bagaimana Anda ingin memasang versi baru ini.
id.UpgradeDesc=PosRonda terdeteksi sudah terpasang di komputer ini. Silakan pilih opsi pembaruan:
id.UpgradeOptionKeepData=Perbarui versi dan pertahankan data pengaturan (Rekomendasi - password & kamera tetap aman)
id.UpgradeOptionCleanInstall=Instal ulang bersih (Reset pengaturan dan data kamera ke awal pabrik)
id.UpgradeOptionUninstallOld=Copot pemasangan versi lama terlebih dahulu sebelum memasang baru

en.UpgradeTitle=Previous Installation Detected
en.UpgradeSubTitle=Choose how you want to install this new version.
en.UpgradeDesc=An existing installation of PosRonda was found. Please select an update option:
en.UpgradeOptionKeepData=Update application and keep settings data (Recommended - keeps passwords & camera feeds)
en.UpgradeOptionCleanInstall=Clean installation (Reset settings and camera data to defaults)
en.UpgradeOptionUninstallOld=Uninstall previous version completely before installing new version

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Salin semua file aplikasi KECUALI config.json
Source: "..\pkg-full\*"; DestDir: "{app}"; Excludes: "config.json"; Flags: ignoreversion recursesubdirs createallsubdirs

; config.json dikelola khusus berdasarkan pilihan pengguna saat upgrade
Source: "..\pkg-full\config.json"; DestDir: "{app}"; Check: ShouldInstallConfig

[Icons]
Name: "{autoprograms}\PosRonda Hub\PosRonda"; Filename: "{app}\PosRonda.exe"
Name: "{autoprograms}\PosRonda Hub\Panduan Penggunaan"; Filename: "{app}\PANDUAN.md"
Name: "{autoprograms}\PosRonda Hub\Uninstall PosRonda"; Filename: "{uninstallexe}"
Name: "{autodesktop}\PosRonda Hub"; Filename: "{app}\PosRonda.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PosRonda.exe"; Description: "{cm:LaunchProgram,PosRonda Hub}"; Flags: nowait postinstall skipifsilent

[Code]
var
  UpgradePage: TInputOptionWizardPage;

function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '') or FileExists(ExpandConstant('{app}\PosRonda.exe'));
end;

procedure InitializeWizard;
begin
  UpgradePage := CreateInputOptionPage(
    wpWelcome,
    CustomMessage('UpgradeTitle'),
    CustomMessage('UpgradeSubTitle'),
    CustomMessage('UpgradeDesc'),
    True, False
  );
  UpgradePage.Add(CustomMessage('UpgradeOptionKeepData'));
  UpgradePage.Add(CustomMessage('UpgradeOptionCleanInstall'));
  UpgradePage.Add(CustomMessage('UpgradeOptionUninstallOld'));
  UpgradePage.Values[0] := True;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  if (UpgradePage <> nil) and (PageID = UpgradePage.ID) then
    Result := not IsUpgrade()
  else
    Result := False;
end;

function ShouldInstallConfig(): Boolean;
begin
  // Jika instalasi baru, langsung pasang
  if not IsUpgrade() then
  begin
    Result := True;
    Exit;
  end;

  // Jika upgrade dan pengguna memilih Clean Install (Index 1)
  if UpgradePage.Values[1] then
  begin
    // Cadangkan file lama terlebih dahulu
    if FileExists(ExpandConstant('{app}\config.json')) then
      RenameFile(ExpandConstant('{app}\config.json'), ExpandConstant('{app}\config.backup.json'));
    Result := True;
    Exit;
  end;

  // Jika pengguna memilih Keep Data (Index 0): jangan timpa jika sudah ada
  if UpgradePage.Values[0] then
  begin
    Result := not FileExists(ExpandConstant('{app}\config.json'));
    Exit;
  end;

  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  UninstCmd: String;
begin
  if (CurStep = ssInstall) and IsUpgrade() and (UpgradePage <> nil) and UpgradePage.Values[2] then
  begin
    UninstCmd := RemoveQuotes(GetUninstallString());
    if FileExists(UninstCmd) then
    begin
      Exec(UninstCmd, '/SILENT /NORESTART', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;
