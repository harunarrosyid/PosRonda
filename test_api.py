"""
Standalone Diagnostic & API Test Suite - PosRonda v4.0
Alat pengujian cepat untuk YouTube API, Playlist, 4 RTSP Kamera, dan Telegram.
"""

import os
import sys
import time
import config_manager
import cv2

def print_header(title):
    print("\n" + "=" * 60)
    print(f"   {title}")
    print("=" * 60)

def test_youtube():
    print_header("TES 1: KONEKSI YOUTUBE DATA API & PLAYLIST")
    cfg = config_manager.load_config()
    yt_cfg = cfg.get("youtube_api", {})

    secret_file = yt_cfg.get("client_secrets_file", "client_secrets.json")
    playlist_id = yt_cfg.get("playlist_id", "")

    if not os.path.exists(secret_file):
        print(f"✖ File '{secret_file}' TIDAK DITEMUKAN!")
        print("  Silakan letakkan file client_secrets.json dari Google Cloud Console di folder ini.")
        return False

    print(f"✔ File '{secret_file}' ditemukan.")
    print("  Menghubungi Google OAuth & YouTube Data API...")

    try:
        from youtube_manager import YouTubeManager
        yt = YouTubeManager(cfg)
        yt.authenticate()
        ok, msg = yt.test_connection(playlist_id=playlist_id)
        print(f"\nHASIL:")
        print(msg)
        return ok
    except Exception as e:
        print(f"\n✖ Terjadi Kesalahan YouTube API: {e}")
        return False

def test_cameras():
    print_header("TES 2: KONEKSI 4 RTSP KAMERA V360")
    cfg = config_manager.load_config()
    cams = cfg.get("cameras", [])

    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|fflags;nobuffer|flags;low_delay|framedrop;1|stimeout;5000000|timeout;5000000|buffer_size;1048576"

    for c in cams:
        name = c.get("name", "Kamera")
        url = c.get("rtsp_url", "")
        print(f"\nMenguji {name} ({url})...")

        if not url or not url.startswith("rtsp://"):
            print("  ⚠️ URL kosong atau tidak valid.")
            continue

        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            print(f"  ✖ GAGAL terhubung ke {name}. Periksa IP/password/Wi-Fi.")
        else:
            ret, frame = cap.read()
            if ret and frame is not None:
                h, w, _ = frame.shape
                print(f"  ✔ BERHASIL! Resolusi stream terdeteksi: {w}x{h} piksel.")
            else:
                print(f"  ⚠️ Terhubung, tetapi gagal menangkap frame gambar.")
            cap.release()

def test_telegram():
    print_header("TES 3: KONEKSI TELEGRAM BOT")
    cfg = config_manager.load_config()
    tg = cfg.get("telegram", {})
    token = tg.get("bot_token", "")
    chat_id = tg.get("chat_id", "")

    if not token or not chat_id:
        print("⚠️ Bot Token atau Chat ID belum disetel di config.json.")
        return

    print("Mengirim pesan tes ke Telegram...")
    import requests
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat_id, "text": "🔔 Tes Diagnostik PosRonda Hub v4.0 Berhasil!"}, timeout=5)
        if r.status_code == 200:
            print("✔ Berhasil! Pesan tes sudah masuk ke Telegram Anda.")
        else:
            print(f"✖ Gagal: {r.text}")
    except Exception as e:
        print(f"✖ Error: {e}")

def cleanup_youtube_upcoming():
    print_header("BERSIHKAN SIARAN UPCOMING MENUMPUK")
    cfg = config_manager.load_config()
    try:
        from youtube_manager import YouTubeManager
        yt = YouTubeManager(cfg)
        yt.authenticate()
        print("Mencari dan membersihkan seluruh siaran 'Upcoming' yang menumpuk...")
        ok, msg = yt.cleanup_all_upcoming()
        print(f"\nHASIL:")
        print(msg)
    except Exception as e:
        print(f"\n✖ Terjadi Kesalahan: {e}")

def scan_network_cameras():
    print_header("TES 4: PINDAI KAMERA OTOMATIS (ONVIF & NETWORK RTSP)")
    try:
        import onvif_scanner
        cams = onvif_scanner.scan_all_cameras()
        print(f"\nHASIL PEMINDAIAN ({len(cams)} Kamera Ditemukan):")
        for i, c in enumerate(cams, 1):
            print(f" {i}. {c['name']} (IP: {c['ip']}, Protokol: {c['protocol']})")
            print(f"    RTSP URL Saran: {c['primary_url']}")
        if not cams:
            print("  ⚠️ Tidak ada kamera dengan port RTSP/ONVIF terbuka yang ditemukan di subnet ini.")
    except Exception as e:
        print(f"✖ Error saat scan: {e}")

def cleanup_active_live():
    print_header("TUTUP SEMUA SIARAN LIVE MENGGANTUNG (ZOMBIE STREAMS)")
    cfg = config_manager.load_config()
    try:
        from youtube_manager import YouTubeManager
        yt = YouTubeManager(cfg)
        yt.authenticate()
        print("Mencari siaran live yang sedang aktif atau menggantung di channel...")
        ok, msg = yt.cleanup_active_live_broadcasts(only_cctv_prefix=False)
        print(f"\nHASIL:")
        print(msg)
    except Exception as e:
        print(f"\n✖ Terjadi Kesalahan: {e}")

def main():
    while True:
        print("\n" + "=" * 60)
        print("     MENU TES & DIAGNOSTIK POSRONDA v4.0 HUB")
        print("=" * 60)
        print("1. Tes YouTube Data API & Playlist")
        print("2. Tes Koneksi 4 RTSP Kamera")
        print("3. Tes Notifikasi Telegram")
        print("4. Jalankan Semua Tes Sekaligus")
        print("5. 🗑️ Bersihkan Semua Siaran 'Upcoming' yang Menumpuk di YouTube")
        print("6. 🔍 Pindai Kamera Otomatis di Jaringan (ONVIF & RTSP Scanner)")
        print("7. ⏹️ Tutup Semua Siaran Live Menggantung (Zombie Streams)")
        print("8. Keluar")

        choice = input("\nPilih menu (1-8): ").strip()

        if choice == "1":
            test_youtube()
        elif choice == "2":
            test_cameras()
        elif choice == "3":
            test_telegram()
        elif choice == "4":
            test_youtube()
            test_cameras()
            test_telegram()
        elif choice == "5":
            cleanup_youtube_upcoming()
        elif choice == "6":
            scan_network_cameras()
        elif choice == "7":
            cleanup_active_live()
        elif choice == "8":
            break
        else:
            print("Pilihan tidak valid.")

if __name__ == "__main__":
    main()
