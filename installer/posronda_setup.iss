; Script Inno Setup untuk PosRonda Hub
; Menghasilkan PosRonda-Setup.exe resmi dengan progress bar dan integrasi Windows

#ifndef MyAppVersion
#define MyAppVersion "4.2.1"
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
DisableWelcomePage=no
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "default"; MessagesFile: "compiler:Default.isl"

[Messages]
SetupAppTitle=Pemasangan PosRonda Hub
SetupWindowTitle=Pemasangan - %1
WelcomeLabel1=Selamat Datang di Pemasangan PosRonda Hub
WelcomeLabel2=Program ini akan memasang [name/ver] di komputer Anda.%n%nDisarankan untuk menutup aplikasi lain sebelum melanjutkan.
ClickNext=Klik Lanjut untuk meneruskan, atau Batal untuk keluar dari Pemasangan.
SelectDirLabel3=Program Pemasangan akan memasang [name] ke dalam folder berikut.
SelectDirBrowseLabel=Untuk melanjutkan, klik Lanjut. Jika Anda ingin memilih folder lain, klik Telusuri.
ReadyLabel1=Program Pemasangan telah siap memasang [name] di komputer Anda.
ReadyLabel2a=Klik Pasang untuk memulai proses instalasi.
InstallingLabel=Mohon tunggu sementara Program Pemasangan memasang [name] di komputer Anda...
FinishedHeadingLabel=Pemasangan Selesai
FinishedLabelNoIcons=Pemasangan [name] telah selesai di komputer Anda.
FinishedLabel=Pemasangan [name] telah selesai di komputer Anda. Aplikasi dapat dijalankan dengan memilih ikon yang telah dibuat.
ClickFinish=Klik Selesai untuk keluar dari Pemasangan.

[Tasks]
Name: "desktopicon"; Description: "Buat ikon di Desktop (Layar Utama)"; GroupDescription: "Ikon Tambahan:"

[Files]
Source: "..\pkg-full\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\PosRonda Hub\PosRonda"; Filename: "{app}\PosRonda.exe"
Name: "{autoprograms}\PosRonda Hub\Panduan Penggunaan"; Filename: "{app}\PANDUAN.md"
Name: "{autoprograms}\PosRonda Hub\Uninstall PosRonda"; Filename: "{uninstallexe}"
Name: "{autodesktop}\PosRonda Hub"; Filename: "{app}\PosRonda.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PosRonda.exe"; Description: "Jalankan PosRonda Hub sekarang"; Flags: nowait postinstall skipifsilent
