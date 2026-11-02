# 🛡️ PosRonda v4.0
**Autonomous CCTV Multi-Camera Hub & Multi-Destination Streaming Engine**  
*Dioptimalkan untuk ThinkPad X230 (Intel QuickSync GPU QSV) & Semua PC Windows*  
*Semi Open-Source License Model (ala WinRAR)*

---

[![Build PosRonda Windows EXE](https://github.com/harunarrosyid/PosRonda/actions/workflows/build-exe.yml/badge.svg)](https://github.com/harunarrosyid/PosRonda/actions/workflows/build-exe.yml)
![Platform](https://img.shields.io/badge/Platform-Windows%2064--bit-blue)
![Python](https://img.shields.io/badge/Python-3.11-brightgreen)
![Hardware](https://img.shields.io/badge/Hardware%20Accel-Intel%20QuickSync%20QSV-orange)
![License](https://img.shields.io/badge/License-Semi%20Open--Source%20(WinRAR%20Model)-blueviolet)

---

## 📌 Sekilas Tentang PosRonda

**PosRonda** adalah stasiun kontrol pengawasan CCTV multi-kamera mandiri yang dirancang untuk beroperasi nonstop 24 jam di laptop/PC pos siskamling, kantor, dan perumahan. 

Dibuat dengan efisiensi tinggi setara OBS Studio yang memanfaatkan akselerasi GPU Intel QuickSync (`h264_qsv`), PosRonda mampu berjalan dingin (suhu 45–55°C, CPU ~15%) bahkan pada perangkat lawas seperti **ThinkPad X230**.

---

## 🚀 Fitur Unggulan

### 1. Patrol / Tour Mode Multi-Kamera (> 4 CCTV)
* **Mendukung 4, 8, 12, hingga 16 Kamera:** Menampilkan kamera dalam siklus halaman (Halaman 1: Kamera 1–4, Halaman 2: Kamera 5–8) secara otomatis setiap N detik.
* **Tampilan Grid 3x3:** Mendukung tampilan 9 kamera sekaligus dalam 1 layar monitor.
* **Navigasi Cepat:** Tombol `Spasi` atau tombol angka `1`–`4` untuk beralih halaman feed kamera seketika.
* **Interaksi Layar:** Fitur **Tap 2x (Double Click)** pada kuadran layar untuk merefresh dan menyambungkan ulang feed kamera yang terputus.

### 2. Tiga Pilihan Server Transmisi & Penyimpanan
1. **Mode A: YouTube Live (Cloud Gratis 24 Jam):**
   * Sangat ideal untuk RT/RW, Siskamling, dan Tempat Ibadah.
   * Auto-split siaran live tiap 11 jam agar rekaman tersimpan utuh di YouTube Playlist tanpa batas kuota cloud.
2. **Mode B: Private Media Server / Custom RTMP (Untuk Klien Elit):**
   * Mengalirkan feed ke server media mandiri (seperti [MediaMTX](https://github.com/bluenviron/mediamtx), SRS, atau NGINX RTMP) di domain kantor (`rtmp://cctv.kantor.com/live`).
   * **Bebas logo YouTube, bebas iklan, dan latensi super rendah (<0.5 detik via WebRTC)**.
3. **Mode C: Perekaman Mandiri HDD / NAS (100% Bebas Kuota Internet):**
   * Video langsung dipecah rapi per 15/30 menit dalam format MP4 ke hard disk laptop/NAS.
   * Dilengkapi pembersihan otomatis (*auto-pruning*) rekaman lama (>14 atau 30 hari) di latar belakang agar hard disk tidak pernah penuh.

### 3. Auto-Discovery Ramah Pengguna Awam (ONVIF + Fast Subnet Probe)
* Pengguna awam **tidak perlu mengetik atau menghafal URL RTSP**.
* Cukup ketik **Username** dan **Password** CCTV, lalu klik **"🔍 PINDAI & SAMBUNGKAN OTOMATIS"**.
* Sistem akan memindai protokol ONVIF & port RTSP di seluruh LAN/Wi-Fi secara otomatis.

### 4. Model Lisensi Semi Open-Source (Filosofi WinRAR)
* **PosRonda Community Edition:** 100% GRATIS selamanya tanpa batas durasi siaran, tanpa kedaluwarsa, dan tanpa pengurangan fitur teknis untuk pos ronda, warga RT/RW, masjid, dan penggunaan mandiri.
* **PosRonda PRO Edition:** Lisensi komersial khusus untuk **teknisi / installer CCTV** yang menjual sistem ke ruko, perkantoran, atau pabrik. Dilengkapi fitur **White-Labeling** (menghapus merek PosRonda dan menggantinya dengan merek/logo teknisi sendiri), Watermark kustom pada live stream, serta Installer PIN Lock.

---

## 🏗️ Struktur Proyek

```text
PosRonda/
├── .github/
│   └── workflows/
│       └── build-exe.yml         # CI/CD otomatis kompilasi Cython + PyInstaller di Windows
├── docs/                         # Panduan & Dokumentasi
│   ├── PANDUAN.md
│   └── PANDUAN_API.md
├── scripts/                      # Skrip utilitas Windows
│   ├── run.bat
│   ├── Jalankan_Tanpa_CMD.vbs
│   ├── Aktifkan_Auto_Start_Windows.bat
│   ├── Matikan_Auto_Start_Windows.bat
│   ├── Buat_Shortcut_Desktop.bat
│   └── Update_Otomatis.bat
├── src/                          # Source Code Utama (Modular)
│   └── posronda/
│       ├── __init__.py
│       ├── main.py               # GUI Surveillance Command Center
│       ├── core/                 # [Core Engine - Cython C-Binary .pyd Target]
│       │   ├── __init__.py
│       │   ├── license_manager.py   --> Dikompilasi jadi .pyd (C native)
│       │   ├── stream_engine.py     --> Compositor Engine & Multi-mode pusher
│       │   └── config_manager.py
│       ├── ui/                   # Antarmuka Pengguna
│       │   ├── __init__.py
│       │   └── settings_dialog.py
│       ├── network/              # Protokol Jaringan & Deteksi
│       │   ├── __init__.py
│       │   ├── onvif_scanner.py
│       │   ├── youtube_manager.py
│       │   └── notifier.py
│       └── utils/
│           ├── __init__.py
│           └── check_env.py
├── tests/                        # Suite Uji Diagnostik
│   └── test_api.py
├── config.json                   # Konfigurasi default
├── requirements.txt              # Pustaka Python yang dibutuhkan
├── PosRonda.spec                 # Blueprint PyInstaller
├── setup_cython.py               # Compiler Python ke C Native (.pyd)
├── run.py                        # Entry Point Launcher
├── .gitignore
└── README.md
```

---

## ⌨️ Pintasan Keyboard (Shortcuts)

| Tombol | Fungsi |
| :--- | :--- |
| **`Spasi` / `Tab`** | **Ganti Halaman Kamera (Patrol Mode)** ke halaman berikutnya |
| **`PageUp` / `PageDown`** | Beralih antar halaman feed kamera |
| **`1`, `2`, `3`, `4`** | Langsung loncat ke Halaman 1, 2, 3, atau 4 |
| **`F2`** | Buka **Panel Pengaturan PosRonda** (Kamera, Patrol, Server Siaran) |
| **`F1`** | Buka **Info Lisensi & Model WinRAR** |
| **`F11`** | Masuk / Keluar dari mode **Layar Penuh (Full Screen)** |
| **`F5`** | **Mulai Ulang (Restart)** siaran streaming / rekaman seketika |
| **`F6`** | **Jeda (Pause)** siaran / perekaman (layar standby aktif, kamera lokal tetap jalan) |
| **`F7`** | **Akhiri / Mulai** siaran atau perekaman lokal |
| **`Double-Click` Layar** | Refresh kamera seketika jika koneksi Wi-Fi sempat tersendat |
| **`ESC`** | Keluar dari mode Full Screen |

---

## 🛠️ Menjalankan Aplikasi

### Opsi 1: Menggunakan File EXE Siap Pakai
1. Unduh **`PosRonda.exe`** dari tab [Releases / Actions Artifacts](https://github.com/harunarrosyid/PosRonda/actions).
2. Letakkan `ffmpeg.exe` dan `config.json` dalam folder yang sama dengan `PosRonda.exe`.
3. Klik 2x `PosRonda.exe` — langsung berjalan tanpa jendela hitam CMD!

### Opsi 2: Menjalankan dari Source Code (Python)
```bash
# 1. Pasang dependensi
pip install -r requirements.txt

# 2. Jalankan aplikasi
python run.py
```

---

## 🔒 Proteksi Core Biner (Model `.aar` Android)
Pada saat pipeline GitHub Actions berjalan, modul proprietary di `src/posronda/core/` diterjemahkan ke bahasa C oleh Cython dan dikompilasi oleh compiler MSVC C++ menjadi berkas biner `.pyd` (*machine code DLL*). Hal ini melindungi algoritma lisensi dan engine streaming dari decompiler Python, sementara seluruh ekosistem antarmuka dan tools tetap terbuka bagi komunitas.
