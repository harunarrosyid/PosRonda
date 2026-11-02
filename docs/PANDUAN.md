# Panduan Penggunaan: PosRonda v4.3.0

Dokumentasi penggunaan dan konfigurasi aplikasi pemantau CCTV multi-kamera PosRonda.

---

## 1. Fitur Utama

### A. Dukungan Multi-Kamera (Patrol Mode & Grid 3x3)
Aplikasi mendukung pemantauan lebih dari 4 kamera (hingga 16 kamera):
* **Patrol Mode (Rotasi Halaman Otomatis):** Menampilkan sejumlah kamera per halaman dan secara berkala beralih ke halaman berikutnya berdasarkan interval waktu yang ditentukan pada Pengaturan.
* **Tata Letak Grid 3x3:** Menampilkan hingga 9 kamera sekaligus dalam satu layar.
* **Navigasi Halaman Cepat:** Beralih halaman feed kamera menggunakan tombol **`Spasi`** atau angka **`1`** sampai **`4`**.

### B. Opsi Server Transmisi & Penyimpanan
1. **YouTube Live:**
   * Streaming langsung ke YouTube dengan pembaruan siaran otomatis tiap 11 jam untuk pengarsipan video.
2. **Private RTMP Server:**
   * Mengalirkan video ke server media RTMP mandiri (seperti MediaMTX, SRS, atau NGINX RTMP).
3. **Perekaman Lokal (Disk / NAS):**
   * Menyimpan rekaman video langsung ke direktori lokal tanpa membutuhkan koneksi internet.
   * Video dipecah dalam format MP4 (misal: tiap 15 atau 30 menit).
   * Fitur retensi otomatis akan menghapus file lama yang melebihi batas hari yang ditentukan agar ruang penyimpanan tetap terjaga.

### C. Pemindaian Kamera Otomatis (ONVIF)
* Memindai IP kamera pada jaringan lokal menggunakan protokol ONVIF dan verifikasi port RTSP.
* Cukup masukkan kredensial Username dan Password kamera, lalu jalankan pemindaian untuk mengisi slot kamera secara otomatis.

### D. Skema Lisensi
* **Community Edition:** Penggunaan gratis untuk kebutuhan pribadi, lingkungan warga, dan non-komersial.
* **PRO Edition:** Untuk kebutuhan komersial, dilengkapi opsi custom branding, watermark kustom, dan kunci PIN pengaturan.

---

## 2. Pintasan Keyboard

| Tombol | Fungsi |
| :--- | :--- |
| **`Spasi` / `Tab`** | Pindah ke halaman kamera berikutnya (Patrol Mode) |
| **`PageUp` / `PageDown`** | Beralih antar halaman kamera |
| **`1`, `2`, `3`, `4`** | Memilih halaman kamera 1, 2, 3, atau 4 secara langsung |
| **`F2`** | Buka jendela Pengaturan |
| **`F1`** | Informasi Aplikasi & Lisensi |
| **`F11`** | Masuk / Keluar dari Layar Penuh (Fullscreen) |
| **`F5`** | Memulai ulang siaran streaming / sesi perekaman |
| **`F6`** | Menjeda atau melanjutkan siaran |
| **`F7`** | Mengakhiri atau memulai streaming / perekaman |
| **`F9`** | Beralih antara **Mode Hemat (1 FPS GUI)** & **Mode Studio (Full)** |
| **`Double-Click`** | Merefresh dan menyambungkan ulang feed kamera pada kuadran yang dipilih |
| **`ESC`** | Keluar dari layar penuh |

---

## 3. Menjalankan Aplikasi di Windows

1. **Menggunakan File Executable:**
   * Jalankan `PosRonda.exe` secara langsung.
2. **Menjalankan Tanpa Jendela Terminal:**
   * Klik ganda pada berkas `Jalankan_Tanpa_CMD.vbs`.
3. **Menjalankan Melalui Terminal (Debug):**
   * Jalankan `run.bat` untuk melihat log keluaran pada konsol.
4. **Auto-Start Saat Komputer Menyala:**
   * Jalankan skrip `scripts/Aktifkan_Auto_Start_Windows.bat`.

---

## 4. Konfigurasi BIOS ThinkPad (Auto Power On)

Untuk menyalakan perangkat secara otomatis saat pengisi daya (charger) terhubung dengan aliran listrik:
1. Masuk ke **BIOS Setup** (tekan `F1` saat perangkat dinyalakan).
2. Buka menu **Config** -> **Power**.
3. Set opsi **`Power On with AC Attach`** ke **`[Enabled]`**.
4. Simpan pengaturan dengan menekan **`F10`**.

---

## 5. Kontak & Pemesanan Lisensi PRO

Untuk pemesanan lisensi PosRonda PRO, kustomisasi merek (white-labeling), atau bantuan teknis:
* **Email:** [ngulonstudio@gmail.com](mailto:ngulonstudio@gmail.com)
* **Website:** [https://ngulonstudio.web.id](https://ngulonstudio.web.id)
