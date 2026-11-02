# PANDUAN LENGKAP: MENDAPATKAN YOUTUBE DATA API & KONFIGURASI

Panduan langkah demi langkah ini dibuat sangat mudah dipahami untuk mendapatkan file **`client_secrets.json`** dan **Playlist ID** dari Google.

---

## BAGIAN 1: Cara Mendapatkan `client_secrets.json` (Gratis 100%)

### Langkah 1: Buka Google Cloud Console
1. Buka browser dan kunjungi: **https://console.cloud.google.com/**
2. Login menggunakan akun Google (Gmail) yang terhubung dengan **Channel YouTube** Anda.
3. Di bagian atas, klik menu dropdown proyek, lalu klik **"NEW PROJECT"** (Proyek Baru).
4. Beri nama proyek, misalnya: `CCTV-YouTube-Stream`, lalu klik **"CREATE"**.

---

### Langkah 2: Aktifkan YouTube Data API v3
1. Pastikan proyek `CCTV-YouTube-Stream` sudah terpilih di bagian atas.
2. Buka menu navigasi (garis tiga di pojok kiri atas) ➔ pilih **"APIs & Services"** ➔ **"Library"**.
3. Di kolom pencarian, ketik: **`YouTube Data API v3`**.
4. Klik hasilnya, lalu klik tombol biru: **"ENABLE"** (Aktifkan).

---

### Langkah 3: Konfigurasi Layar Izin (OAuth Consent Screen)
1. Di menu sebelah kiri, klik **"OAuth consent screen"**.
2. Pilih User Type: **"External"**, lalu klik **"CREATE"**.
3. Isi kolom wajib:
   * **App name**: `CCTV Hub`
   * **User support email**: Pilih email Gmail Anda.
   * **Developer contact information**: Masukkan email Gmail Anda lagi.
4. Klik **"SAVE AND CONTINUE"**.
5. Pada halaman **Scopes**, langsung scroll ke bawah dan klik **"SAVE AND CONTINUE"**.
6. Pada halaman **Test users** (**SANGAT PENTING**):
   * Klik **"+ ADD USERS"**.
   * Masukkan alamat email Gmail akun YouTube Anda.
   * Klik **"ADD"**, lalu klik **"SAVE AND CONTINUE"**.

---

### Langkah 4: Buat Kredensial & Unduh File JSON
1. Di menu sebelah kiri, klik **"Credentials"**.
2. Di bagian atas, klik tombol **"+ CREATE CREDENTIALS"** ➔ pilih **"OAuth client ID"**.
3. Pada kolom **Application type**, pilih: **"Desktop app"**.
4. Pada kolom **Name**, biarkan default atau beri nama: `CCTV Desktop`.
5. Klik **"CREATE"**.
6. Akan muncul jendela pop-up. Klik tombol **"DOWNLOAD JSON"** (ikon panah ke bawah).
7. File yang terunduh biasanya bernama panjang (contoh: `client_secret_xxxxxxxxxx.json`).
8. **Ubah nama file tersebut menjadi:** **`client_secrets.json`**
9. Pindahkan file **`client_secrets.json`** tersebut ke dalam folder aplikasi:
   `cctv_youtube_hub/`

---

## BAGIAN 2: Cara Mendapatkan YouTube Playlist ID

1. Buka YouTube di browser: **https://www.youtube.com**
2. Buka menu profil ➔ masuk ke **YouTube Studio** atau klik menu **Playlist** di channel Anda.
3. Buat Playlist baru (misalnya diberi nama: *"Arsip CCTV Rumah"*).
   * Visibilitas bisa disetel ke **Unlisted** (Tidak Publik) agar hanya Anda yang bisa menonton, atau **Public**.
4. Buka playlist tersebut, lalu lihat alamat (URL) di address bar browser Anda.
   * Contoh URL:
     `https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxxxxxxxxxxxx`
5. Kode acak setelah tanda `list=` itulah Playlist ID Anda:
   * Contoh: **`PLxxxxxxxxxxxxxxxxxxxxxxxx`** (salin kode ini).

---

## BAGIAN 3: Cara Konfigurasi di Aplikasi CCTV YouTube Hub

1. Jalankan aplikasi (atau klik file `run.bat` / `CCTV-Hub.exe`).
2. Tekan tombol **`F2`** di keyboard untuk membuka jendela Pengaturan.
3. Masuk ke tab **"▶ YouTube Live & Playlist"**:
   * Centang kotak: **[X] Aktifkan Otomasi YouTube API**.
   * Pada kolom *File Client Secret*, pastikan tertulis: `client_secrets.json`.
   * Pada kolom *YouTube Playlist ID*, paste kode Playlist ID Anda tadi.
4. Klik tombol merah: **`[▶ Tes Koneksi YouTube API & Playlist]`**.
5. **Autentikasi Sekali Saja (Browser):**
   * Browser akan otomatis terbuka meminta izin login Google.
   * Pilih akun Gmail/Channel YouTube Anda.
   * Jika muncul peringatan *"Google hasn’t verified this app"*, jangan panik (ini normal karena aplikasi milik pribadi):
     * Klik tulisan kecil: **Advanced** (Lanjutan).
     * Klik: **Go to CCTV Hub (unsafe)**.
     * Klik **Continue / Allow** untuk memberikan izin streaming dan playlist.
6. Aplikasi akan memunculkan notifikasi sukses:  
   * ✔ *Berhasil terhubung ke Channel: [Nama Channel Anda]*  
   * ✔ *Playlist Valid: [Nama Playlist Anda]*
7. Klik **"Simpan & Terapkan"**.

File token otentikasi akan otomatis tersimpan sebagai **`token.json`** di folder aplikasi. Anda **tidak perlu login lagi** untuk seterusnya! Siaran 11 jam dan penambahan ke playlist akan berjalan 100% otomatis 24 jam non-stop.
