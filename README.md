# PosRonda

Aplikasi monitoring CCTV multi-kamera berbasis Python, Tkinter, dan FFmpeg. Mendukung pemantauan banyak kamera (2x2 Patrol / 3x3 Grid) serta streaming ke YouTube Live, RTMP Server pribadi, atau penyimpanan lokal.

![PosRonda Preview](docs/preview.png)

## Fitur

* **Multi-Kamera:** Mendukung hingga 16 kamera dengan Patrol Mode (rotasi halaman otomatis) atau tata letak 3x3.
* **Tujuan Streaming:**
  * **YouTube Live:** Streaming langsung dengan auto-split berkala untuk pengarsipan video.
  * **Private RTMP:** Mengalirkan video ke server media sendiri (MediaMTX, SRS, NGINX RTMP).
  * **Perekaman Lokal:** Simpan video tersegmentasi (MP4) langsung ke disk atau NAS dengan pembersihan file lama otomatis berdasarkan hari retensi.
* **Deteksi Kamera:** Pemindaian IP kamera pada jaringan lokal menggunakan protokol ONVIF & port RTSP.
* **Akselerasi Hardware:** Mendukung encoder perangkat keras Intel QuickSync (`h264_qsv`) maupun CPU (`libx264`).

## Cara Menjalankan

### Menggunakan File Executable (.exe)
Unduh `PosRonda.exe` dari bagian [Releases / Actions](https://github.com/harunarrosyid/PosRonda/actions), letakkan bersama `ffmpeg.exe` dan `config.json`, lalu jalankan.

### Menjalankan dari Source Code
```bash
git clone https://github.com/harunarrosyid/PosRonda.git
cd PosRonda
pip install -r requirements.txt
python run.py
```

## Konfigurasi

Kamera dapat ditambahkan melalui menu Pengaturan (**F2**) atau langsung pada `config.json`:

```json
"cameras": [
    {
        "id": 1,
        "name": "Pintu Gerbang",
        "rtsp_url": "rtsp://admin:password@192.168.1.101:554/live/ch0"
    }
]
```

## Pintasan Keyboard

| Tombol | Fungsi |
| :--- | :--- |
| `Spasi` / `Tab` | Ganti halaman kamera berikutnya (Patrol Mode) |
| `1` - `4` | Pilih halaman kamera 1, 2, 3, atau 4 |
| `Double Click` | Refresh / sambung ulang feed kamera yang diklik |
| `F2` | Buka menu Pengaturan |
| `F6` | Jeda / Lanjutkan siaran |
| `F7` | Mulai / Akhiri streaming atau sesi rekaman |
| `F11` / `Esc` | Masuk / Keluar Fullscreen |

## Lisensi & Kontak
PosRonda tersedia dalam edisi Community (bebas digunakan untuk keperluan pribadi, lingkungan warga, dan non-komersial) serta edisi Pro untuk kebutuhan integrasi komersial.

Untuk pemesanan lisensi Pro, integrasi kustom, atau bantuan teknis:
* Email: [ngulonstudio@gmail.com](mailto:ngulonstudio@gmail.com)
* Website: [ngulonstudio.web.id](https://ngulonstudio.web.id)
