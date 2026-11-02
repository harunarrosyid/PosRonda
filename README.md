# PosRonda

Aplikasi pemantau CCTV multi-kamera dan live streaming berbasis Python, Tkinter, dan FFmpeg.

---

## Fitur

* **Multi-Kamera & Patrol Mode:** Mendukung pemantauan banyak kamera dengan rotasi halaman otomatis (Patrol Mode) serta opsi tata letak grid 2x2 atau 3x3.
* **Tujuan Streaming Fleksibel:**
  * **YouTube Live:** Siaran langsung dengan rotasi berkala untuk pengarsipan.
  * **Custom RTMP:** Pengiriman video ke media server pribadi (seperti MediaMTX, SRS, atau NGINX RTMP).
  * **Perekaman Lokal:** Penyimpanan video tersegmentasi (MP4) langsung ke disk atau penyimpanan jaringan (NAS) dengan penghapusan otomatis berdasarkan batas retensi.
* **Deteksi Kamera (ONVIF):** Pencarian IP kamera dan port RTSP pada jaringan lokal dengan kredensial yang ditentukan.
* **Akselerasi Hardware:** Mendukung encoder perangkat keras Intel QuickSync (`h264_qsv`) maupun CPU (`libx264`).
* **Kontrol Cepat:** Navigasi antarmuka melalui tombol pintas keyboard dan interaksi klik langsung pada kuadran kamera.

---

## Struktur Direktori

```text
PosRonda/
├── docs/                 # Dokumentasi dan panduan penggunaan
├── scripts/              # Skrip pendukung Windows (.bat, .vbs)
├── src/
│   └── posronda/         # Kode sumber aplikasi
│       ├── core/         # Konfigurasi, mesin streaming, dan lisensi
│       ├── network/      # Pemindai ONVIF, notifikasi, dan modul streaming
│       ├── ui/           # Dialog pengaturan dan tampilan
│       └── utils/        # Pemeriksaan dependensi sistem
├── tests/                # Pengujian modul
├── config.json           # Berkas konfigurasi default
├── requirements.txt      # Dependensi pustaka Python
├── PosRonda.spec         # Spesifikasi PyInstaller
└── run.py                # Titik masuk aplikasi
```

---

## Cara Menjalankan

### Menggunakan Executable (.exe)
1. Unduh `PosRonda.exe` dari bagian [Releases / Actions Artifacts](https://github.com/harunarrosyid/PosRonda/actions).
2. Pastikan berkas `ffmpeg.exe` dan `config.json` berada di dalam direktori yang sama dengan `PosRonda.exe`.
3. Jalankan `PosRonda.exe`.

### Menjalankan dari Kode Sumber
```bash
pip install -r requirements.txt
python run.py
```

---

## Pintasan Keyboard

| Tombol | Aksi |
| :--- | :--- |
| `Spasi` / `Tab` | Pindah ke halaman kamera berikutnya (Patrol Mode) |
| `PageUp` / `PageDown` | Berpindah antar halaman kamera |
| `1` - `4` | Memilih halaman kamera tertentu |
| `F2` | Membuka jendela Pengaturan |
| `F1` | Informasi Aplikasi & Lisensi |
| `F11` | Beralih Layar Penuh (Fullscreen) |
| `F5` | Memulai ulang streaming |
| `F6` | Menjeda atau melanjutkan streaming |
| `F7` | Mengakhiri atau memulai streaming |
| `Double-Click` | Menyambungkan ulang kamera pada kuadran yang dipilih |
| `Esc` | Keluar dari layar penuh |

---

## Lisensi
PosRonda tersedia dalam edisi Community (dapat digunakan untuk keperluan pribadi, lingkungan warga, dan non-komersial) serta edisi Pro untuk kebutuhan integrasi komersial.
