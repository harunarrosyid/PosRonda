; Script Inno Setup untuk PosRonda Hub
; Mendukung Pemasangan Dwibahasa & Manajemen Upgrade Versi (Timpa / Simpan Data / Instal Bersih / Copot)

#ifndef MyAppVersion
#define MyAppVersion "4.4.4"
#endif

#define MyAppId "{8F322987-9483-4DF1-A79B-83F67B549821}"

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
CloseApplicationsFilter=*.exe,*.dll

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
  sUnInstPath := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppId}_is1';
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
  begin
    if not RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString) then
    begin
      if IsWin64() then
      begin
        if not RegQueryStringValue(HKLM64, sUnInstPath, 'UninstallString', sUnInstallString) then
          RegQueryStringValue(HKCU64, sUnInstPath, 'UninstallString', sUnInstallString);
      end;
    end;
  end;
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
  UpgradePage.SelectedValueIndex := 0;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  if (UpgradePage <> nil) and (PageID = UpgradePage.ID) then
    Result := not IsUpgrade()
  else
    Result := False;
end;

function GetUpgradeChoice(): Integer;
begin
  if UpgradePage <> nil then
    Result := UpgradePage.SelectedValueIndex
  else
    Result := 0;
end;

function ShouldInstallConfig(): Boolean;
begin
  // Jika file config.json di folder target belum ada, wajib dipasang
  if not FileExists(ExpandConstant('{app}\config.json')) then
  begin
    Result := True;
    Exit;
  end;

  // Jika file config.json sudah ada:
  // Pilihan 0 (Keep Data): jangan timpa config.json pengguna
  if IsUpgrade() and (GetUpgradeChoice() = 0) then
  begin
    Result := False;
    Exit;
  end;

  // Pilihan 1 (Clean Install) atau Pilihan 2 (Uninstall Old): pasang baru
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  UninstCmd: String;
  OldConfig: String;
  BackupConfig: String;
begin
  if (CurStep = ssInstall) and IsUpgrade() then
  begin
    // Opsi 2: Copot pemasangan versi lama terlebih dahulu
    if GetUpgradeChoice() = 2 then
    begin
      UninstCmd := RemoveQuotes(GetUninstallString());
      if (UninstCmd <> '') and FileExists(UninstCmd) then
      begin
        Exec(UninstCmd, '/SILENT /NORESTART /SUPPRESSMSGBOXES', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      end;
    end;

    // Opsi 1: Instal ulang bersih (Backup config lama lalu buat baru)
    if GetUpgradeChoice() = 1 then
    begin
      OldConfig := ExpandConstant('{app}\config.json');
      BackupConfig := ExpandConstant('{app}\config.backup.json');
      if FileExists(OldConfig) then
      begin
        if FileExists(BackupConfig) then
          DeleteFile(BackupConfig);
        RenameFile(OldConfig, BackupConfig);
      end;
    end;
  end;
end;
