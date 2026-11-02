import json
import os
import sys

def get_base_dir():
    """Mendapatkan direktori dasar aplikasi (kompatibel dengan script biasa maupun PyInstaller .exe)"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, "config.json")):
        return cwd
    this_dir = os.path.dirname(os.path.abspath(__file__))
    root_candidate = os.path.abspath(os.path.join(this_dir, "..", "..", ".."))
    if os.path.exists(os.path.join(root_candidate, "config.json")):
        return root_candidate
    return cwd

DEFAULT_CONFIG = {
    "app_name": "PosRonda",
    "app_tagline": "Autonomous CCTV Multi-Camera Hub & YouTube Streaming Engine",
    "version": "4.2.0",
    "default_camera_credentials": {
        "username": "admin",
        "password": "",
        "default_port": 554
    },
    "cameras": [
        {
            "id": 1,
            "name": "Kamera 1",
            "rtsp_url": "rtsp://admin:admin123@192.168.1.101:554/live/ch0",
            "enabled": True
        },
        {
            "id": 2,
            "name": "Kamera 2",
            "rtsp_url": "rtsp://admin:admin123@192.168.1.102:554/live/ch0",
            "enabled": True
        },
        {
            "id": 3,
            "name": "Kamera 3",
            "rtsp_url": "rtsp://admin:admin123@192.168.1.103:554/live/ch0",
            "enabled": True
        },
        {
            "id": 4,
            "name": "Kamera 4",
            "rtsp_url": "rtsp://admin:admin123@192.168.1.104:554/live/ch0",
            "enabled": True
        }
    ],
    "patrol": {
        "enabled": False,
        "interval_seconds": 15,
        "layout": "2x2"
    },
    "auto_discover_camera_ip": False,
    "streaming": {
        "mode": "youtube",
        "rtmp_server": "rtmp://a.rtmp.youtube.com/live2",
        "stream_key": "",
        "custom_rtmp_url": "rtmp://127.0.0.1:1935/live/posronda",
        "local_record": {
            "enabled": False,
            "output_dir": "recordings",
            "segment_minutes": 15,
            "retention_days": 14
        },
        "max_duration_hours": 11,
        "rollover_lead_minutes": 5,
        "encoder": "h264_qsv",
        "x264_preset": "veryfast",
        "fps": 25,
        "bitrate_kbps": 1200,
        "grid_resolution": "1280x720",
        "rtsp_transport": "tcp"
    },
    "osd": {
        "enabled": True,
        "font_scale": 0.42,
        "position": "top_left",
        "style": "badge_outline"
    },
    "youtube_api": {
        "enabled": False,
        "client_secrets_file": "client_secrets.json",
        "token_file": "token.json",
        "playlist_id": "",
        "title_prefix": "CCTV Monitoring 24 Jam",
        "privacy_status": "unlisted",
        "latency_preference": "low",
        "single_stream_mode": True
    },
    "telegram": {
        "enabled": False,
        "bot_token": "",
        "chat_id": ""
    }
}

CONFIG_FILE = os.path.join(get_base_dir(), "config.json")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            # Bersihkan kunci fitur usang agar config tetap ringkas & bebas ML overhead
            cfg.pop("ai_features", None)

            deep_merge(cfg, DEFAULT_CONFIG)
            # Auto-extract default credentials from camera 1 if missing
            if not cfg.get("default_camera_credentials", {}).get("username") and cfg.get("cameras"):
                first_url = cfg["cameras"][0].get("rtsp_url", "")
                import re
                m = re.search(r"rtsp://([^:]+):([^@]+)@", first_url)
                if m:
                    cfg["default_camera_credentials"] = {
                        "username": m.group(1),
                        "password": m.group(2),
                        "default_port": 554
                    }
            return cfg
    except Exception as e:
        print(f"Error membaca config.json: {e}, membuat config baru.")
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def deep_merge(target, default):
    for k, v in default.items():
        if k not in target:
            target[k] = v
        elif isinstance(v, dict) and isinstance(target[k], dict):
            deep_merge(target[k], v)
    return target

def export_config(cfg, target_path):
    """Mengekspor konfigurasi aktif ke file JSON tujuan (backup)."""
    try:
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
        return True, "Konfigurasi berhasil diekspor."
    except Exception as e:
        return False, f"Gagal mengekspor konfigurasi: {e}"

def import_config(source_path):
    """Mengimpor dan memvalidasi file backup JSON konfigurasi."""
    try:
        with open(source_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return False, "Format file tidak valid (harus objek JSON).", None

        # Validasi struktur konfigurasi PosRonda
        if "cameras" not in data and "streaming" not in data:
            return False, "File JSON ini bukan backup konfigurasi PosRonda yang valid.", None

        merged = deep_merge(data, DEFAULT_CONFIG)
        merged.pop("ai_features", None)
        return True, "Konfigurasi berhasil diimpor.", merged
    except Exception as e:
        return False, f"Gagal membaca file konfigurasi: {e}", None

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
        return True
    except Exception as e:
        print(f"Gagal menyimpan config.json: {e}")
        return False

def get_startup_shortcut_path():
    """Mendapatkan path shortcut CCTV Hub di folder Startup Windows"""
    appdata = os.environ.get("APPDATA")
    if not appdata:
        # Fallback path jika env APPDATA belum di-expand
        userprofile = os.environ.get("USERPROFILE", "")
        if userprofile:
            appdata = os.path.join(userprofile, "AppData", "Roaming")
        else:
            return None
    return os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "PosRonda Hub.lnk")

def is_autostart_enabled():
    """Mengecek apakah shortcut auto-start di folder Startup Windows sudah aktif"""
    path = get_startup_shortcut_path()
    return bool(path and os.path.exists(path))

def set_autostart(enable=True):
    """
    Mengaktifkan atau menonaktifkan auto-start CCTV Hub saat Windows menyala.
    Membuat shortcut ke Jalankan_Tanpa_CMD.vbs sehingga berjalan otomatis tanpa jendela hitam CMD.
    """
    path = get_startup_shortcut_path()
    if not path:
        return False

    if enable:
        base_dir = get_base_dir()
        vbs_target = os.path.join(base_dir, "Jalankan_Tanpa_CMD.vbs")
        if not os.path.exists(vbs_target):
            vbs_target = os.path.join(base_dir, "run.bat")

        # Gunakan PowerShell untuk membuat .lnk secara native tanpa library eksternal
        ps_cmd = (
            f"$ws = New-Object -ComObject WScript.Shell; "
            f"$s = $ws.CreateShortcut('{path}'); "
            f"$s.TargetPath = '{vbs_target}'; "
            f"$s.WorkingDirectory = '{base_dir}'; "
            f"$s.IconLocation = 'shell32.dll,14'; "
            f"$s.Description = 'PosRonda Hub Auto-Start ThinkPad X230'; "
            f"$s.Save()"
        )
        import subprocess
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                check=True,
                capture_output=True
            )
            print(f"[Auto-Start] Berhasil memasang shortcut startup: {path}")
            return True
        except Exception as e:
            print(f"[Auto-Start] Gagal membuat shortcut startup: {e}")
            return False
    else:
        try:
            if os.path.exists(path):
                os.remove(path)
                print(f"[Auto-Start] Berhasil menghapus shortcut startup: {path}")
            return True
        except Exception as e:
            print(f"[Auto-Start] Gagal menghapus shortcut startup: {e}")
            return False

