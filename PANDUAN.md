# PANDUAN LENGKAP: POSRONDA v4.0
**Autonomous CCTV Multi-Camera Hub & Multi-Destination Streaming Engine**  
*Dioptimalkan untuk ThinkPad X230 (Intel QuickSync QSV) & Semua PC / Laptop Windows*  
*Model Lisensi Semi Open-Source (ala WinRAR)*

---

## 1. Fitur Utama PosRonda v4.0

### A. Mendukung Lebih dari 4 CCTV (Patrol / Tour Mode & Grid 3x3)
Jika Anda memiliki lebih dari 4 CCTV (misal: 6, 8, 9, 12, atau 16 kamera):
* **Mode Patrol / Tour Otomatis:** Sistem akan menampilkan 4 kamera pertama (Halaman 1), lalu setelah interval waktu tertentu (misal: 15 detik), otomatis beralih menampilkan kamera 5 sampai 8 (Halaman 2), dan seterusnya.
* **Tampilan Grid 3x3:** Mendukung tampilan 9 kamera sekaligus dalam 1 layar!
* **Ganti Halaman Manual Cepat:** Cukup tekan tombol **`Spasi`** atau tombol angka **`1`**, **`2`**, **`3`**, **`4`** untuk langsung melompat ke halaman kamera tertentu.
* **Sangat Hemat Daya di ThinkPad X230:** Hanya merender kuadran kamera aktif di memori, sehingga CPU tetap adem (~15%) dan GPU Intel HD Graphics 4000 QuickSync bekerja stabil tanpa throttling.

### B. Tiga Opsi Tujuan Siaran (YouTube, Private RTMP, atau HDD/NAS Mandiri)
PosRonda tidak membatasi Anda hanya pada YouTube:
1. **Mode A: YouTube Live (Cloud Gratis 24 Jam):**
   * Sangat cocok untuk RT/RW, Siskamling, dan Masjid.
   * Tidak butuh sewa server/VPS (100% gratis penyimpanan cloud YouTube).
   * Otomatis split video tiap 11 jam agar rekaman tersimpan rapi di YouTube Playlist.
2. **Mode B: Private Media Server / Custom RTMP (Untuk Klien Elit / Korporat):**
   * Sangat cocok untuk klien perumahan mewah, kantor, ruko elit, atau pabrik yang **menolak streaming ke YouTube** demi privasi dan gengsi korporat.
   * Mengalirkan video ke server media milik sendiri (seperti **MediaMTX**, **SRS**, atau **NGINX RTMP**) di domain kantor (contoh: `rtmp://cctv.kantor.com/live`).
   * Tanpa logo YouTube, tanpa iklan, dan dapat diakses dengan latensi ultra rendah via WebRTC (<0.5 detik).
3. **Mode C: Perekaman Lokal HDD / NAS Mandiri (100% Bebas Kuota Internet):**
   * Rekaman langsung disimpan ke Hard Disk laptop atau network drive NAS kantor tanpa memerlukan koneksi internet sama sekali.
   * **Segmentasi Otomatis:** Video otomatis dipecah menjadi file MP4 berdurasi rapi (misal: tiap 15 atau 30 menit).
   * **Auto-Pruning (Pembersihan Otomatis):** Rekaman lama yang melebihi batas retensi (misal: lebih dari 14 atau 30 hari) akan otomatis dihapus di latar belakang agar hard disk tidak pernah penuh.

### C. Auto-Discovery Ramah Orang Awam (ONVIF + Fast Subnet Scanner)
* Pengguna awam **tidak perlu menghafal URL RTSP manual**.
* Cukup ketik **Username** dan **Password** CCTV, lalu klik **"🔍 PINDAI & SAMBUNGKAN OTOMATIS"**.
* PosRonda akan melacak sinyal protokol ONVIF & port RTSP di seluruh jaringan Wi-Fi/LAN, memvalidasi jalur video kamera, dan langsung memetakan semua slot kamera secara otomatis.

### D. Model Lisensi Semi Open-Source (Filosofi WinRAR)
* **PosRonda Community Edition:** 100% GRATIS selamanya tanpa batas durasi siaran, tanpa kedaluwarsa, dan tanpa pengurangan fitur teknis untuk pos ronda, warga RT/RW, masjid, dan penggunaan pribadi.
* **PosRonda PRO Edition:** Lisensi komersial khusus untuk **teknisi / installer CCTV** yang menjual sistem ke klien berbayar. Dilengkapi fitur **White-Labeling** (menghapus merek PosRonda dan menggantinya dengan merek/logo teknisi sendiri), Watermark kustom pada live stream, serta Installer PIN Lock.

---

## 2. Navigasi & Pintasan Keyboard (Shortcuts)

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

## 3. Cara Menjalankan Aplikasi di Windows

1. **Pilihan Utama (Paling Direkomendasikan & Bersih):**
   * Klik 2x file **`Jalankan_Tanpa_CMD.vbs`**.
   * PosRonda langsung muncul di layar monitor **tanpa jendela hitam CMD**, sangat ringan, dan bebas dari false-alarm antivirus.

2. **Pilihan Pintasan Desktop:**
   * Klik 2x file **`Buat_Shortcut_Desktop.bat`**.
   * Ikon **PosRonda Hub** akan otomatis dibuat di Desktop laptop Anda.

3. **Pilihan Otomatis Nyala Pasca Mati Lampu (Auto-Start):**
   * Klik 2x file **`Aktifkan_Auto_Start_Windows.bat`**.
   * Jika listrik padam dan menyala kembali, laptop akan otomatis membuka PosRonda tanpa campur tangan manusia!

4. **Mode Debug Teks:**
   * Klik 2x file **`run.bat`** jika ingin melihat output log terminal secara langsung.

---

## 4. Tips BIOS ThinkPad X230 (Power On with AC)

Agar laptop menyala sendiri begitu colokan charger mendapat aliran listrik PLN:
1. Nyalakan laptop, tekan tombol **`F1`** berulang kali untuk masuk ke **ThinkPad BIOS Setup**.
2. Masuk ke menu **Config** -> **Power**.
3. Ubah opsi **`Power On with AC Attach`** menjadi **`[Enabled]`**.
4. Tekan **`F10`** untuk menyimpan dan restart.
